"""Differential checks for a fixed, reviewed corpus of Python agent actions.

This executes trusted repository fixtures. It is not a sandbox for user code.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Case:
    name: str
    source: str
    expected: object
    trace: tuple[str, ...] = ()
    contract: str = ""


CASES = (
    Case("arithmetic", "result = (3 + 4) * 2", 14),
    Case(
        "ordered_arguments",
        "result = pair(mark('left'), mark('right'))",
        ["left", "right"],
        ("left", "right"),
    ),
    Case("and_skips_rhs", "result = False and mark('unwanted')", False),
    Case("or_skips_rhs", "result = True or mark('unwanted')", True),
    Case("and_returns_operand", "result = (True and false_probe).label", "false"),
    Case("or_returns_operand", "result = (False or true_probe).label", "true"),
    Case(
        "and_checks_intermediate",
        "result = (false_probe and mark('unwanted')).label",
        "false",
        ("bool:false",),
    ),
    Case(
        "or_checks_intermediate",
        "result = (true_probe or mark('unwanted')).label",
        "true",
        ("bool:true",),
    ),
    Case("chain_builtin_short_circuit", "result = 3 < 2 < mark('unwanted')", False),
    Case("chain_middle_once", "result = 0 < number() < 2", True, ("number",)),
    Case(
        "chain_false_like_short_circuit",
        "result = (left < 1 < later()).label",
        "false",
        ("compare", "bool:false"),
        "A false-like rich comparison must suppress the next operand.",
    ),
    Case("comparison_returns_operand", "result = (left < 1).label", "false", ("compare",)),
    Case(
        "conditional_branch", "result = mark('yes') if True else mark('unwanted')", "yes", ("yes",)
    ),
    Case("comprehension_filter", "result = [x * 2 for x in range(5) if x % 2]", [2, 6]),
    Case(
        "loop_else_break",
        "result = []\nfor x in range(3):\n    if x == 1:\n        break\n"
        "    result.append(x)\nelse:\n    result.append(99)",
        [0],
    ),
    Case(
        "finally_side_effect",
        "result = 1\ntry:\n    result = 2\nfinally:\n    mark('cleanup')",
        2,
        ("cleanup",),
    ),
    Case(
        "builtin_exception_catch",
        "try:\n    {}['missing']\nexcept KeyError:\n    result = 'caught'",
        "caught",
    ),
    Case(
        "keyword_argument_order",
        "result = pair(second=mark('second'), first=mark('first'))",
        ["first", "second"],
        ("second", "first"),
    ),
)


class Probe:
    def __init__(self, label: str, truth: bool, trace: list[str]):
        self.label, self.truth, self.trace = label, truth, trace

    def __bool__(self):
        self.trace.append(f"bool:{self.label}")
        return self.truth


class Left:
    def __init__(self, trace: list[str]):
        self.trace = trace

    def __lt__(self, other):
        self.trace.append("compare")
        return Probe("false", False, self.trace)


def freeze(value):
    """Preserve value types; True must not compare equal to 1 in a report."""
    if value is None or type(value) in (bool, int, str):
        return {"type": type(value).__name__, "value": value}
    if type(value) is float and math.isfinite(value):
        return {"type": "float", "value": value}
    if type(value) in (list, tuple):
        return {"type": type(value).__name__, "value": [freeze(v) for v in value]}
    raise TypeError(f"Unsupported observation type: {type(value).__name__}")


def valid_value(value) -> bool:
    if not isinstance(value, dict) or set(value) != {"type", "value"}:
        return False
    tag, payload = value["type"], value["value"]
    scalar_types = {"NoneType": type(None), "bool": bool, "int": int, "str": str}
    if isinstance(tag, str) and tag in scalar_types:
        return type(payload) is scalar_types[tag]
    if tag == "float":
        return type(payload) is float and math.isfinite(payload)
    return (
        tag in ("list", "tuple")
        and isinstance(payload, list)
        and all(valid_value(item) for item in payload)
    )


def valid_observation(value) -> bool:
    if not isinstance(value, dict):
        return False
    trace = value.get("trace")
    if not isinstance(trace, list) or not all(isinstance(item, str) for item in trace):
        return False
    if value.get("status") == "ok":
        return set(value) == {"status", "result", "trace"} and valid_value(value["result"])
    return (
        value.get("status") == "exception"
        and set(value) == {"status", "exception", "trace"}
        and isinstance(value["exception"], str)
        and bool(value["exception"])
    )


def observe(case: Case, backend: str) -> dict:
    trace: list[str] = []

    def mark(label):
        trace.append(label)
        return label

    def number():
        trace.append("number")
        return 1

    def later():
        trace.append("later")
        return 5

    functions = {
        "mark": mark,
        "number": number,
        "later": later,
        "pair": lambda first, second: [first, second],
    }
    state = {
        "true_probe": Probe("true", True, trace),
        "false_probe": Probe("false", False, trace),
        "left": Left(trace),
    }
    if backend == "smolagents":
        # Import failures are infrastructure failures, not semantic mismatches.
        from smolagents.local_python_executor import BASE_PYTHON_TOOLS, evaluate_python_code
    try:
        if backend == "cpython":
            state.update(functions)
            exec(compile(case.source, f"<contract:{case.name}>", "exec"), state)
        elif backend == "smolagents":
            evaluate_python_code(
                case.source,
                static_tools={**BASE_PYTHON_TOOLS, **functions},
                state=state,
                authorized_imports=[],
            )
        else:
            raise ValueError(f"Unknown backend: {backend}")
    except Exception as exc:
        return {"status": "exception", "exception": type(exc).__name__, "trace": trace}
    return {"status": "ok", "result": freeze(state["result"]), "trace": trace}


def run_child(case: Case, backend: str, timeout: float = 20.0) -> dict:
    try:
        child = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "worker", backend, case.name],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"status": "infrastructure_error", "reason": "worker_timeout"}
    if child.returncode:
        return {
            "status": "infrastructure_error",
            "reason": "worker_exit",
            "returncode": child.returncode,
            "stderr": child.stderr[-2000:],
        }
    try:
        observation = json.loads(child.stdout)
        if not valid_observation(observation):
            raise ValueError("Invalid observation")
        return observation
    except (ValueError, AttributeError):
        return {"status": "infrastructure_error", "reason": "invalid_worker_output"}


def classify(case: Case, reference: dict, candidate: dict) -> str:
    if any(x.get("status") == "infrastructure_error" for x in (reference, candidate)):
        return "infrastructure_error"
    expected = {"status": "ok", "result": freeze(case.expected), "trace": list(case.trace)}
    if reference != expected:
        return "oracle_error"
    return "match" if reference == candidate else "mismatch"


def environment() -> dict:
    metadata = {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "system": platform.system(),
    }
    try:
        distribution = importlib.metadata.distribution("smolagents")
        direct_url = distribution.read_text("direct_url.json")
        provenance = json.loads(direct_url) if direct_url else None
        # Never publish a local install path or credential-bearing URL.
        commit = (provenance or {}).get("vcs_info", {}).get("commit_id")
        from smolagents import local_python_executor

        source = Path(local_python_executor.__file__).read_bytes()
        metadata.update(
            status="ok",
            smolagents=distribution.version,
            smolagents_commit=commit,
            executor_sha256=hashlib.sha256(source).hexdigest(),
            harness_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        )
    except Exception as exc:
        # Metadata/import errors must not erase the already collected observations.
        metadata.update(status="infrastructure_error", exception=type(exc).__name__)
    return metadata


def build_report(selected, timeout=20.0) -> dict:
    rows = []
    for case in selected:
        reference = run_child(case, "cpython", timeout)
        candidate = run_child(case, "smolagents", timeout)
        rows.append(
            {
                "case": case.name,
                "source": case.source,
                "source_sha256": hashlib.sha256(case.source.encode()).hexdigest(),
                "status": classify(case, reference, candidate),
                "cpython": reference,
                "smolagents": candidate,
            }
        )
    counts = {
        s: sum(r["status"] == s for r in rows)
        for s in ("match", "mismatch", "oracle_error", "infrastructure_error")
    }
    return {"schema_version": 1, "environment": environment(), "counts": counts, "cases": rows}


def exit_code(report: dict) -> int:
    counts = report["counts"]
    if (
        counts["oracle_error"]
        or counts["infrastructure_error"]
        or report.get("environment", {}).get("status") == "infrastructure_error"
    ):
        return 2
    return 1 if counts["mismatch"] else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--case", choices=[c.name for c in CASES], action="append")
    run.add_argument("--timeout", type=float, default=20)
    worker = commands.add_parser("worker", help=argparse.SUPPRESS)
    worker.add_argument("backend", choices=("cpython", "smolagents"))
    worker.add_argument("case", choices=[c.name for c in CASES])
    args = parser.parse_args(argv)
    if args.command == "worker":
        case = next(c for c in CASES if c.name == args.case)
        print(json.dumps(observe(case, args.backend), allow_nan=False))
        return 0
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be a finite positive number")
    selected = [c for c in CASES if not args.case or c.name in args.case]
    report = build_report(selected, args.timeout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"]))
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
