import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import runtime_contracts as lab


@pytest.mark.parametrize("case", lab.CASES, ids=lambda c: c.name)
def test_cpython_matches_independent_golden(case):
    actual = lab.observe(case, "cpython")
    assert actual == {
        "status": "ok",
        "result": lab.freeze(case.expected),
        "trace": list(case.trace),
    }


def test_types_are_not_erased():
    assert lab.freeze(True) != lab.freeze(1)
    assert lab.freeze([1]) != lab.freeze((1,))
    with pytest.raises(TypeError):
        lab.freeze(float("nan"))


def test_result_equality_does_not_hide_extra_side_effect():
    case = lab.CASES[0]
    reference = lab.observe(case, "cpython")
    candidate = {**reference, "trace": ["unexpected write"]}
    assert lab.classify(case, reference, candidate) == "mismatch"


def test_two_wrong_answers_do_not_match():
    case = lab.CASES[0]
    wrong = {"status": "ok", "result": lab.freeze(15), "trace": []}
    assert lab.classify(case, wrong, wrong) == "oracle_error"


def test_timeout_is_not_a_semantic_failure():
    with patch.object(lab.subprocess, "run", side_effect=subprocess.TimeoutExpired("worker", 0.01)):
        observation = lab.run_child(lab.CASES[0], "cpython", 0.01)
    assert observation == {"status": "infrastructure_error", "reason": "worker_timeout"}


@pytest.mark.parametrize(
    "stdout",
    [
        "noise",
        "[]",
        "{}",
        '{"status":"ok"}',
        '{"status":"ok","trace":[]}',
        '{"status":"exception","trace":[]}',
        '{"status":"ok","trace":[],"result":{"type":"int","value":true}}',
        '{"status":"ok","trace":[7],"result":{"type":"str","value":"x"}}',
    ],
)
def test_corrupt_worker_protocol(stdout):
    with patch.object(
        lab.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout, "")
    ):
        assert lab.run_child(lab.CASES[0], "cpython")["status"] == "infrastructure_error"


@pytest.mark.parametrize(
    "counts,expected",
    [
        ({"match": 1, "mismatch": 0, "oracle_error": 0, "infrastructure_error": 0}, 0),
        ({"match": 1, "mismatch": 1, "oracle_error": 0, "infrastructure_error": 0}, 1),
        ({"match": 1, "mismatch": 1, "oracle_error": 1, "infrastructure_error": 0}, 2),
        ({"match": 1, "mismatch": 0, "oracle_error": 0, "infrastructure_error": 1}, 2),
    ],
)
def test_exit_status(counts, expected):
    assert lab.exit_code({"counts": counts}) == expected


def test_cli_real_process_and_runtime(tmp_path):
    target = tmp_path / "report.json"
    command = [
        sys.executable,
        str(Path(lab.__file__)),
        "run",
        "--case",
        "arithmetic",
        "--output",
        str(target),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=60)
    assert completed.returncode == 0, completed.stderr
    report = json.loads(target.read_text())
    assert report["counts"]["match"] == 1
    assert len(report["environment"]["executor_sha256"]) == 64


def test_worker_state_is_fresh():
    case = next(c for c in lab.CASES if c.name == "ordered_arguments")
    assert lab.run_child(case, "cpython") == lab.run_child(case, "cpython")


def test_unique_case_names():
    assert len({c.name for c in lab.CASES}) == len(lab.CASES)


def test_missing_distribution_preserves_report_and_infrastructure_exit(tmp_path):
    target = tmp_path / "missing.json"
    with patch.object(
        lab.importlib.metadata,
        "distribution",
        side_effect=lab.importlib.metadata.PackageNotFoundError("smolagents"),
    ):
        with patch.object(lab, "run_child", return_value={"status": "infrastructure_error"}):
            status = lab.main(["run", "--case", "arithmetic", "--output", str(target)])
    report = json.loads(target.read_text())
    assert status == 2
    assert report["counts"]["infrastructure_error"] == 1
    assert report["environment"]["exception"] == "PackageNotFoundError"


def test_metadata_failure_does_not_label_successful_workers_a_mismatch():
    report = {
        "counts": {"match": 1, "mismatch": 0, "oracle_error": 0, "infrastructure_error": 0},
        "environment": {"status": "infrastructure_error"},
    }
    assert lab.exit_code(report) == 2
