"""Static presentation of the existing typed observations; no execution or scoring."""

# HTML/CSS structure adapted from Signed Webhook Inbox's MIT-licensed offline view.
# ruff: noqa: E501 -- keep static HTML/CSS rules together.

import json
from html import escape
from pathlib import Path


def _json(value) -> str:
    return escape(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False))


def render_html(report: dict, code: int) -> str:
    title = {
        0: "All selected contracts match",
        1: "Differences observed",
        2: "Experiment incomplete",
    }[code]
    counts = report["counts"]
    cards = "".join(
        f'<div class="stat"><strong>{counts[key]}</strong><span>{label}</span></div>'
        for key, label in (
            ("match", "Matches"),
            ("mismatch", "Differences"),
            ("oracle_error", "Oracle errors"),
            ("infrastructure_error", "Execution errors"),
        )
    )
    rank = {"infrastructure_error": 0, "oracle_error": 1, "mismatch": 2, "match": 3}
    observations = []
    for row in sorted(report["cases"], key=lambda item: rank[item["status"]]):
        name, status = escape(row["case"]), escape(row["status"])
        expanded = " open" if row["status"] != "match" else ""
        observations.append(f"""<details class="case"{expanded}>
<summary><span class="badge">{status}</span> <code>{name}</code></summary>
<p>Input program</p><pre>{escape(row["source"])}</pre>
<div class="observations"><div><h3>CPython</h3><pre>{_json(row["cpython"])}</pre></div>
<div><h3>smolagents</h3><pre>{_json(row["smolagents"])}</pre></div></div>
<p class="fingerprint">Input SHA-256: <code>{escape(row["source_sha256"])}</code></p>
</details>""")
    # minimalism: native details controls replace a JavaScript dashboard or new renderer.
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<meta name="color-scheme" content="light"><title>Agent Runtime Contracts — {title}</title>
<style>
:root{{--ink:#172c3e;--muted:#516678;--line:#d6e0e6;--brand:#16615c;--bg:#f3f6f8}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,sans-serif}}
main{{max-width:1120px;margin:auto;padding:40px 28px 60px}}h1{{font-size:clamp(28px,4vw,40px);line-height:1.2}}h2{{font-size:24px}}h3{{font-size:18px}}
.eyebrow,.outcome{{color:var(--brand);font-weight:700}}.intro{{max-width:78ch;color:var(--muted)}}
.stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin:28px 0}}
.stat,section{{background:white;border:1px solid var(--line);border-radius:10px}}.stat{{padding:20px}}.stat strong{{display:block;font-size:32px}}.stat span{{color:var(--muted)}}
section{{padding:24px;margin-bottom:24px}}.case{{border-top:1px solid var(--line);padding:12px 0}}summary{{cursor:pointer;min-height:44px;overflow-wrap:anywhere}}
summary:focus-visible,a:focus-visible{{outline:3px solid var(--brand);outline-offset:3px}}.badge{{font-size:14px;font-weight:700;margin-right:8px}}
code,pre{{font:14px/1.6 ui-monospace,monospace;white-space:pre-wrap;overflow-wrap:anywhere}}pre{{padding:16px;background:#edf3f5;border-radius:6px}}
.observations{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}.observations>div{{min-width:0}}.fingerprint,footer{{color:var(--muted);font-size:14px}}
@media(max-width:700px){{main{{padding:24px 16px 40px}}section{{padding:16px}}.stats{{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}}.stat{{padding:12px}}.observations{{grid-template-columns:1fr}}}}
@media print{{body{{background:white}}main{{max-width:none;padding:0}}section{{border:0;padding:12px}}.case{{break-inside:avoid}}}}
</style></head><body><main>
<header><p class="eyebrow">LOCAL RUNTIME OBSERVATIONS</p><h1>Agent Runtime Contracts</h1>
<p class="intro">Compare typed return values and recorded callback order for a fixed, reviewed Python corpus. Equal answers can hide an extra action.</p>
<p class="outcome">{title} · diagnostic exit code {code}</p></header>
<div class="stats" aria-label="Observed contract counts">{cards}</div>
<section aria-labelledby="cases-title"><h2 id="cases-title">Contract observations</h2>
<p id="case-note">Errors and differences appear first and are expanded. Matching cases can be opened with the keyboard. These counts describe this selected corpus, not general runtime accuracy.</p>
{"".join(observations)}</section>
<section aria-labelledby="environment-title"><h2 id="environment-title">Runtime and source identity</h2>
<p>Check the dependency commit and source fingerprints before comparing runs. Metadata failure makes the experiment incomplete even if individual observations match.</p>
<pre>{_json(report["environment"])}</pre></section>
<section aria-labelledby="scope-title"><h2 id="scope-title">Scope and handling</h2>
<p>This is a snapshot of the JSON from this run. It does not refresh, approve a runtime or change the expected behavior. Execution errors and a bad CPython oracle are separate from semantic differences.</p>
<p>Only explicit fixture callbacks are traced. Subprocesses are not security sandboxes. No model quality, sandbox escape, production reliability or performance claim follows from these checks.</p>
<p>Reports contain fixture programs, values, callback labels and possible diagnostic paths. Review a report before sharing it.</p></section>
<footer>Offline HTML · no scripts or external assets · no upload</footer>
</main></body></html>"""


def write_html(report: dict, code: int, path: Path) -> None:
    page = render_html(report, code)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(page)
