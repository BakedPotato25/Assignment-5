from pathlib import Path
import argparse

from playwright.sync_api import sync_playwright


ROUTES = [
    ("books", "/books/"),
    ("login", "/login/"),
    ("register", "/register/"),
    ("cart", "/cart/"),
    ("staff-list", "/staff/books/"),
    ("staff-form", "/staff/books/add/"),
]

VIEWPORTS = [
    ("desktop", {"width": 1440, "height": 900}),
    ("mobile", {"width": 390, "height": 844}),
]


def take_batch(base_url: str, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for viewport_name, viewport in VIEWPORTS:
            context = browser.new_context(viewport=viewport)
            page = context.new_page()

            for slug, route in ROUTES:
                page.goto(f"{base_url}{route}", wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(500)
                output = out_dir / f"{slug}-{viewport_name}.png"
                page.screenshot(path=str(output), full_page=True)

            context.close()
        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture UI screenshots for phase 7 demo")
    parser.add_argument("--target", choices=["before", "after"], required=True)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--output-root", default="scripts/phase7/artifacts")
    args = parser.parse_args()

    output_dir = Path(args.output_root) / args.target
    take_batch(args.base_url.rstrip("/"), output_dir)
    print(f"Saved screenshots to: {output_dir}")
