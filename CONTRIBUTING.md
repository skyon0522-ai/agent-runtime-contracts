# Contributing

Use a small, deterministic case with a concrete reason the behavior matters. Read the Python language contract and runtime implementation first. Include an independent expected CPython result and an observable trace when evaluation order matters. Avoid external APIs, model calls and customer data.

Run the tests, lint and full experiment from README. A new runtime mismatch is a finding, not a reason to weaken the oracle. Record upstream versions and distinguish known reports from new observations. Follow each upstream project's own contribution process before opening issues or patches; this repository does not grant that project's approval.

Fixtures execute Python with the current user's privileges. Do not submit untrusted payloads or sandbox-escape tests. AI assistance is welcome when disclosed with the actual review and validation performed; do not claim review by a human or maintainer when it did not happen.
