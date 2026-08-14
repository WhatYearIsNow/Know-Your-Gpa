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
        page.locator("#fileInput").set_input_files(FIXTURES / "synthetic-16axes.jpg")
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
                summary: result.summary,
                confidence: result.confidence,
              };
            }"""
        )
        browser.close()

    # 合成 16 轴图应识别出约 16 门课(允许 ±2 容差)
    assert abs(result["count"] - 16) <= 2, result
    # 成绩应在 0~100
    assert all(0 <= score <= 100 for score in result["scores"]), result
    # 学分应合法
    assert all(0 < credit <= 10 for credit in result["credits"]), result
    # 摘要数字应合法
    assert 0 <= result["summary"]["weighted"] <= 100, result
    assert 0 <= result["summary"]["gpa"] <= 5, result
    assert result["summary"]["credits"] > 0, result
    # 不应有控制台错误
    assert not console_errors, console_errors
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
