"""Prints a Markdown summary of a JUnit XML file (used for the GitHub Actions job summary).

    python -m tests.ui.support.junit_summary reports/junit.xml >> "$GITHUB_STEP_SUMMARY"
"""
import sys
import xml.etree.ElementTree as ET


def summarize(path: str) -> str:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        return "### UI tests\n\nNo JUnit report was produced (the run stopped before the tests finished).\n"
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    total = sum(int(s.get("tests", 0)) for s in suites)
    failures = sum(int(s.get("failures", 0)) for s in suites)
    errors = sum(int(s.get("errors", 0)) for s in suites)
    skipped = sum(int(s.get("skipped", 0)) for s in suites)
    seconds = sum(float(s.get("time", 0)) for s in suites)
    passed = total - failures - errors - skipped
    lines = [
        "### UI tests (Playwright)", "",
        "| total | passed | failed | errors | skipped/xfailed | time |",
        "|---|---|---|---|---|---|",
        f"| {total} | {passed} | {failures} | {errors} | {skipped} | {seconds:.0f}s |", "",
    ]
    bad = [case for case in root.iter("testcase") if case.find("failure") is not None or case.find("error") is not None]
    if bad:
        lines += ["**Failing tests**", ""]
        lines += [f"- `{case.get('classname', '')}::{case.get('name', '')}`" for case in bad[:40]]
        if len(bad) > 40:
            lines.append(f"- ... and {len(bad) - 40} more")
        lines += ["", "Traces and screenshots are in the `ui-test-results` artifact "
                      "(`npx playwright show-trace <trace.zip>` or `poetry run playwright show-trace <trace.zip>`)."]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(summarize(sys.argv[1] if len(sys.argv) > 1 else "reports/junit.xml"))
