# Agent Runtime Contracts

**Check whether a Python code agent preserves both the answer and the actions that produced it.**

A code agent can return the expected value while evaluating an operand that Python would skip. If that operand calls a tool, value-only tests miss the extra action. This small, offline laboratory compares a reviewed corpus against CPython and the real smolagents interpreter, with a fresh process for every execution.

Use it when assessing a code-agent runtime, reproducing a language-semantics regression, or designing acceptance tests before connecting business tools. There are no model calls, API keys, customer records or network requests in the checks.

## Run the experiment

Python 3.12 and Git are required for the recorded environment. Other versions have not been locally validated. Installation downloads dependencies; execution is local.

```bash
python -m venv .venv
# Linux/macOS; on Windows use .venv\Scripts\activate
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python runtime_contracts.py run --output report.json
```

The recorded result is **14 matches and 4 mismatches across 18 deliberately selected cases**, with no oracle or infrastructure errors. The command exits **1** because mismatches were observed. This is diagnostic output, not an installation failure. A count from this targeted corpus is not a general runtime accuracy score.

Exit codes: `0` all selected contracts match; `1` semantic or observable-trace mismatch; `2` oracle/worker failure. Worker import errors and timeouts are not counted as runtime mismatches.

Inspect one contract:

```bash
python runtime_contracts.py run --case chain_false_like_short_circuit --output report.json
python -m pytest -q
ruff check .
ruff format --check .
```

The checked-in [observation report](examples/observed.json) records interpreter versions, exact upstream commit, source hashes, input programs, return values and callback traces. The [validation record](VALIDATION.md) explains what was actually run.

## What the report reveals

| Contract | CPython | Inspected smolagents commit |
| --- | --- | --- |
| Final operand of `and` / `or` | Returns the operand without testing its truth value | Returns the same label but calls `__bool__` |
| False-like result in a chained comparison | Skips the later operand | Calls `later()` even though the returned label is the same |
| Catch a built-in `KeyError` | Runs the matching handler | Raises `InterpreterError` |
| Fourteen control cases | Expected result and callback order | Match |

For the chained comparison, the program is `result = (left < 1 < later()).label`. The host fixture's comparison returns a false-like object. CPython records `compare, bool:false`; the inspected interpreter records `compare, later, bool:false`. Both return `false`. The additional call is the finding.

These are version-specific observations, not claims about all releases. The boolean and exception cases overlap existing upstream reports [#2894](https://github.com/huggingface/smolagents/issues/2894) and [#2904](https://github.com/huggingface/smolagents/issues/2904). This project does not claim those discoveries or submit duplicate fixes. No smolagents source is patched or vendored.

## Method and boundaries

Each reviewed case includes an independently specified expected CPython value and trace. A bad oracle is reported separately, even if both runtimes produce the same wrong result. Values retain their types, so `True` and `1` cannot accidentally compare equal. Only explicit fixture callbacks and truth/comparison probes are traced; this is not a complete trace of filesystem, network or arbitrary runtime effects.

Subprocesses isolate fixture state and bound hangs. **They are not security sandboxes.** The runner accepts only case names from the shipped corpus, not arbitrary code or downloaded datasets. Review source changes before executing them. The corpus does not test sandbox escapes, permissions, prompt injection, model quality, production reliability or performance.

The library is pinned to commit `96f33faaf028479119ec8d34507b47694cf14e34`. Change the pin intentionally, rerun, and compare the individual observations. Do not silently redefine expected behavior to make the output green.

## Research and implementation references

- Wang et al., **Executable Code Actions Elicit Better LLM Agents**, ICML 2024, [paper](https://arxiv.org/abs/2402.01030), [alphaXiv](https://www.alphaxiv.org/abs/2402.01030). CodeAct motivates treating executable Python as an agent's action interface. This repository tests that interface's semantics; it does not reproduce CodeAct's model experiments or reported performance.
- **MASEval: Extending Multi-Agent Evaluation from Models to Systems**, 2026, [paper](https://arxiv.org/abs/2603.08835), [alphaXiv](https://www.alphaxiv.org/abs/2603.08835). Used as context for separating system behavior from model capability, not as evidence for this corpus's results.
- [Python language reference: comparisons and Boolean operations](https://docs.python.org/3/reference/expressions.html). The behavior contract, supplemented by explicit golden expectations and actual CPython execution.
- [smolagents interpreter at the inspected commit](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/local_python_executor.py). The original implementation was inspected before designing probes; existing implementation and contribution rules remain upstream's work.

The patterns adopted are small input programs, independent expectations, observable traces and reproducible environment records. This is an original diagnostic harness, not a new Python interpreter or a model benchmark. See [references.bib](references.bib).

## Provenance and license

This is public engineering work, not a client delivery or an upstream endorsement. AI assistance was used for implementation and review; recorded executions, scope and limitations are the evidence. Original code is MIT-licensed. The installed smolagents dependency retains its own Apache-2.0 license.
