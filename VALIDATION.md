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

## Linux installation and HTML increment, 2026-10-15

The new optional HTML view reuses this runner's collected JSON and retains the
same 18 cases, independent expectations, comparison logic and subprocess behavior.
The core function/class ASTs and corpus are unchanged. All 18 complete case
observations match the historical JSON above, including its 14 matches and 4
differences. A mismatch remains diagnostic exit 1; it is not an installation error.

| Local check | Observed result |
| --- | --- |
| Fresh native Linux environment | Ubuntu 24.04 under WSL2, CPython 3.12.3; existing pinned requirements installed with the pip cache disabled; dependency consistency passed. |
| Product tests | 48 passed: the 39 existing tests and 9 HTML/output regressions. |
| Static checks | Ruff lint and formatting passed. |
| Installed invocation outside checkout | Full corpus JSON+HTML exit 1; selected false-like comparison exit 1; legacy arithmetic JSON exit 0. |
| Existing HTML repeat | Exit 2 before execution; both original JSON and HTML hashes unchanged. |
| Final wheel | Tested source, wheel and installed module bytes match; original and reused MIT notices are included; installed arithmetic JSON+HTML passed. |
| Offline display | Desktop 1440 and mobile 390, native keyboard details, print and reduced motion checked with JavaScript disabled; no external request or page error observed. |

The new tests cover escaped programs/metadata, distinct diagnostic statuses,
exclusive HTML output, colliding paths, pre-execution refusal and output errors.
The HTML writer returns 2 on an output failure; a completed JSON can remain when
HTML creation fails. JSON keeps its existing replacement behavior. The
[machine-readable local summary](verification/linux-report.json) records this
scope. [Presentation design and reuse](docs/report-design.md) separates the view
from the unchanged comparison engine.

The final package metadata adds the reused MIT notice and requires setuptools 77
or newer for that license-file declaration. The final distribution check verifies
that these packaging changes do not alter the executable module bytes tested by
the 48-test run. Build tooling and dependency artifacts are not fully hash-locked.

This local increment does not include a new Windows run, independent review or
remote candidate CI. The prepared CI adds installed-command verification and
uploads both JSON and HTML. Do not treat those prepared steps as executed results.
