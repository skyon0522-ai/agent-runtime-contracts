# Offline report design

The view adapts the inspected [Signed Webhook Inbox offline report](https://github.com/skyon0522-ai/signed-webhook-inbox/blob/5d54b8700198640c26ffd15a47b2d82151151bd1/src/signed_webhook_inbox/html_report.py): a self-contained document, escaped values, native keyboard-accessible details, responsive summaries, print styles and exclusive HTML creation. The original MIT notice is retained in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) and distributed with the package.

This project retains its existing fixed corpus, CPython expectations, subprocess observations, classifier and 0/1/2 diagnostic exit codes. The HTML shows the JSON collected by that run; it does not rerun programs, change expected results or introduce a runtime score. The input program, typed return observation, callback trace and input hash remain inspectable for each case. Errors and differences are expanded first; matches stay collapsed.

The view has no JavaScript, external assets, remote data request or approval control. Report content is HTML-escaped, including programs, callbacks and diagnostic metadata. The CSP blocks scripts and external resources. Reports can still contain useful diagnostic paths and should be reviewed before sharing. A metadata failure marks the experiment incomplete even when case counts show no execution errors.

JSON keeps the existing replacement behavior. HTML is opt-in, uses a new path and refuses overwrite. Its path cannot equal the JSON output. A write failure returns 2 rather than describing an incomplete export as a semantic mismatch; an already completed JSON can remain. This is not an atomic two-file transaction.
