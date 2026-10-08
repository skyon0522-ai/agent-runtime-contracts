# Validation record

Recorded 2026-10-08, CPython 3.12.3 on Linux (Ubuntu under WSL).

| Check | Observed result |
| --- | --- |
| `python -m pytest -q` | 39 passed |
| `ruff check .` | Passed |
| `ruff format --check .` | Passed |
| `python runtime_contracts.py run --output examples/observed.json` | Exit 1: 14 matches, 4 mismatches, 0 oracle errors, 0 infrastructure errors |

The subprocess CLI test imports and exercises the actual installed smolagents runtime. Tests also verify independent CPython expectations, trace-sensitive comparison, type preservation, oracle-error detection, worker protocol failures, timeouts and exit statuses. Every corpus case is executed in a separate process for each backend.

An independent code review found two defects in the initial harness: incomplete worker messages were treated as semantic mismatches, and dependency metadata failures could abort the report with the wrong exit code. Both were corrected. Additional regressions check malformed observations, preservation of collected results when the dependency is missing, and infrastructure-error exit code 2. The 39-test result and stored experiment reflect the corrected source.

The dependency commit and executor/harness SHA-256 values are in the report. `requirements-lock.txt` was captured from the dedicated test environment; it contains no local paths or credentials. It pins transitive package versions but does not provide a supply-chain security guarantee.

This is a semantic experiment, not a security audit or a performance benchmark. No language model, customer environment or production service was exercised. Linux/Python 3.12 is the local validation scope. GitHub CI status, once published, is additional evidence and should be checked on the exact commit.
