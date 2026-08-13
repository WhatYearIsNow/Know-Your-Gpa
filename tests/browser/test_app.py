import json
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        console_errors: list[str] = []
        page.on(
            "console",
            lambda message: console_errors.append(message.text)
            if message.type == "error"
            else None,
        )
        page.goto((ROOT / "radar_gpa.html").as_uri())
        page.wait_for_load_state("networkidle")
        page.locator("#fileInput").set_input_files(FIXTURES / "occluded-sample.jpg")
        page.wait_for_function(
            "document.querySelector('#results').dataset.ready === 'true'",
            timeout=60_000,
        )
        result = page.evaluate(
            """() => {
              const result = window.RadarGPA.getResult();
              return {
                count: result.courses.length,
                center: result.center,
                innerRadius: result.innerRadius,
                scores: result.courses.map(course => course.score),
                credits: result.courses.map(course => course.credit),
                displayedCredits: result.displayedCredits,
                creditConstraint: result.creditConstraint,
                summary: result.summary,
                confidence: result.confidence,
                notice: document.querySelector('#notice').textContent,
                inferredRows: document.querySelectorAll(
                  '#courseRows tr.inferred',
                ).length,
              };
            }"""
        )
        browser.close()

    assert result["count"] == 17, result
    assert abs(result["center"]["x"] - 396) <= 12, result
    assert abs(result["center"]["y"] - 936) <= 12, result
    assert abs(result["innerRadius"] - 327) <= 4, result
    assert result["displayedCredits"]["text"] == "38.0", result
    assert result["summary"]["credits"] == 38, result
    assert any(score < 100 for score in result["scores"]), result
    assert result["creditConstraint"]["reference"] == "TERM_B", result
    assert result["creditConstraint"]["insertedCredit"] == 2, result
    assert result["credits"] == [
        4,
        3,
        1,
        4,
        2,
        2,
        1,
        2,
        1,
        3,
        1,
        2,
        5,
        3,
        2,
        1,
        1,
    ], result
    assert result["confidence"] < 72, result
    assert "圆形裁剪和文字遮挡" in result["notice"], result
    assert result["inferredRows"] >= 1, result
    assert not console_errors, console_errors
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
