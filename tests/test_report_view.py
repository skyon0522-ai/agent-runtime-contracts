import json
from html.parser import HTMLParser
from unittest.mock import patch

import pytest

import runtime_contracts as lab
from report_view import render_html, write_html


def report(status="mismatch"):
    return {
        "counts": {
            key: int(key == status)
            for key in ("match", "mismatch", "oracle_error", "infrastructure_error")
        },
        "environment": {"status": "ok", "python": "3.12.3"},
        "cases": [
            {
                "case": "probe",
                "status": status,
                "source": "result = 1",
                "source_sha256": "a" * 64,
                "cpython": {"trace": []},
                "smolagents": {"trace": ["later"]},
            }
        ],
    }


class Tags(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)


def test_report_escapes_programs_values_and_metadata_without_mutating_observations():
    value = report()
    payload = '<script>alert("x")</script><img src="https://invalid.test/x">'
    value["cases"][0]["source"] = payload
    value["cases"][0]["smolagents"]["trace"] = [payload]
    value["environment"]["exception"] = payload
    before = json.dumps(value)
    text = render_html(value, 1)
    assert not {"script", "img", "iframe", "form"} & set(Tags(text).tags)
    assert "&lt;script&gt;" in text and "later" not in text
    assert json.dumps(value) == before


@pytest.mark.parametrize(
    "status,code,title",
    [
        ("match", 0, "All selected contracts match"),
        ("mismatch", 1, "Differences observed"),
        ("oracle_error", 2, "Experiment incomplete"),
        ("infrastructure_error", 2, "Experiment incomplete"),
    ],
)
def test_semantic_differences_and_failed_experiments_keep_distinct_status(status, code, title):
    page = render_html(report(status), code)
    assert title in page and f"diagnostic exit code {code}" in page
    assert status in page


def test_existing_html_is_never_overwritten(tmp_path):
    target = tmp_path / "report.html"
    target.write_text("keep")
    with pytest.raises(FileExistsError):
        write_html(report(), 1, target)
    assert target.read_text() == "keep"


def test_cli_refuses_colliding_outputs_before_execution(tmp_path):
    target = tmp_path / "same.json"
    target.write_text("keep")
    with patch.object(lab, "build_report") as build:
        with pytest.raises(SystemExit) as error:
            lab.main(["run", "--output", str(target), "--html", str(target)])
    assert error.value.code == 2 and not build.called
    assert target.read_text() == "keep"


def test_cli_refuses_existing_html_before_workers_or_json_changes(tmp_path):
    target = tmp_path / "report.html"
    output = tmp_path / "report.json"
    target.write_text("keep html")
    output.write_text("keep json")
    with patch.object(lab, "build_report") as build:
        with pytest.raises(SystemExit) as error:
            lab.main(["run", "--output", str(output), "--html", str(target)])
    assert error.value.code == 2 and not build.called
    assert target.read_text() == "keep html" and output.read_text() == "keep json"


def test_report_write_failure_is_not_reported_as_a_semantic_difference(tmp_path):
    with patch.object(lab, "build_report", return_value=report()):
        with patch.object(lab, "write_html", side_effect=OSError("fixture failure")):
            assert (
                lab.main(
                    [
                        "run",
                        "--output",
                        str(tmp_path / "report.json"),
                        "--html",
                        str(tmp_path / "report.html"),
                    ]
                )
                == 2
            )
    assert json.loads((tmp_path / "report.json").read_text())["counts"]["mismatch"] == 1
