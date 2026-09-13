#!/usr/bin/env -S uv run python3
"""
screenshot_game.py - Screenshots the .f4-game card from a standalone Find4 HTML file.

Produces a PNG preview suitable for inline display in mobile chat UIs (e.g. Claude app).
The Play button is hidden so the image reads cleanly as a non-interactive preview.

Backend selection (automatic, or override with --backend):
  docker   -- builds/uses a local Docker image with Playwright pre-installed; no local
             Python playwright needed. Works on macOS/Linux wherever Docker Desktop runs.
  local    -- uses locally installed playwright Python package.
             Works in sandboxed CI/Claude environments where Docker is unavailable.
  auto     -- tries Docker first, falls back to local (default).

Usage:
    python3 screenshot_game.py \\
        --html output/games/html/my-theme.html \\
        [--output output/games/screenshots/my-theme.html.png] \\
        [--width 520] \\
        [--show-play-btn] \\
        [--backend auto|docker|local] \\
        [--element CSS_SELECTOR]

Default output: sibling screenshots/ directory, filename = <html-filename>.png.
Example: output/games/html/cncf-graduated-projects.html -> output/games/screenshots/cncf-graduated-projects.html.png
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


DOCKER_IMAGE_TAG = "rondomondo/screenshot:latest"
DOCKERFILE_DIR = Path(__file__).parent


def docker_available() -> bool:
    """Return True if Docker is running and reachable."""
    return shutil.which("docker") is not None and subprocess.run(
        ["docker", "info"], capture_output=True, timeout=5
    ).returncode == 0


def _ensure_docker_image() -> None:
    """Build the screenshotter image if it is not already present."""
    check = subprocess.run(
        ["docker", "image", "inspect", DOCKER_IMAGE_TAG],
        capture_output=True,
        timeout=10,
    )
    if check.returncode != 0:
        print(f"Building Docker image {DOCKER_IMAGE_TAG} (first run, ~1 min)...")
        subprocess.run(
            ["docker", "build", "-t", DOCKER_IMAGE_TAG, str(DOCKERFILE_DIR)],
            check=True,
            timeout=300,
        )


def screenshot_via_docker(html_abs: Path, output_abs: Path, width: int, show_play_btn: bool, element: str = '.f4-game') -> None:
    """Run Playwright inside a pre-built Docker image using Node.js.

    A temporary JS script is written into the HTML's directory (mounted as /work)
    to avoid shell-quoting issues with inline -e arguments.
    """
    _ensure_docker_image()

    work_dir = html_abs.parent
    html_name = html_abs.name
    png_name = output_abs.name

    hide_js = (
        "" if show_play_btn else
        "await page.evaluate(() => {"
        "  document.querySelectorAll('.play-btn,#play-btn,[class*=play]')"
        "  .forEach(el => { if (el.tagName === 'A' || el.getAttribute('href')) el.style.display = 'none'; });"
        "});"
    )

    js_script = f"""const {{ chromium }} = require('playwright');
(async () => {{
  const browser = await chromium.launch();
  const page = await browser.newPage({{ viewport: {{ width: {width}, height: 1200 }} }});
  await page.goto('file:///work/{html_name}');
  await page.waitForLoadState('domcontentloaded');
  {hide_js}
  const loc = page.locator('{element}').first();
  if (await loc.count() === 0) {{
    console.error('ERROR: No .f4-game element found');
    process.exit(1);
  }}
  await loc.screenshot({{ path: '/work/{png_name}' }});
  await browser.close();
  console.log('Screenshot saved: /work/{png_name}');
}})();
"""

    script_path = work_dir / "_screenshot_tmp.js"
    script_path.write_text(js_script, encoding="utf-8")

    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{work_dir}:/work",
                "-e", "NODE_PATH=/app/node_modules",
                DOCKER_IMAGE_TAG,
                "node", "/work/_screenshot_tmp.js",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    finally:
        script_path.unlink(missing_ok=True)

    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"Docker Playwright failed (exit {result.returncode})")

    produced = work_dir / png_name
    if produced.resolve() != output_abs.resolve():
        produced.rename(output_abs)

    print(result.stdout.strip())


def screenshot_via_local(html_abs: Path, output_abs: Path, width: int, show_play_btn: bool, element: str = '.f4-game') -> None:
    """Use locally installed playwright Python package (sandbox / CI environments)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "ERROR: playwright not installed and Docker is unavailable.\n"
            "  Local install:  pip install playwright && playwright install chromium\n"
            "  Or run Docker Desktop and retry.",
            file=sys.stderr,
        )
        sys.exit(1)

    output_abs.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 1200})
        page.goto(f"file://{html_abs}")
        page.wait_for_load_state("domcontentloaded")

        if not show_play_btn:
            page.evaluate(
                "document.querySelectorAll('.play-btn, #play-btn, [class*=\"play\"]')"
                ".forEach(el => { if (el.tagName === 'A' || el.getAttribute('href')) el.style.display='none'; })"
            )

        locator = page.locator(element).first
        if locator.count() == 0:
            print(f"ERROR: No element matching '{element}' found in HTML", file=sys.stderr)
            browser.close()
            sys.exit(1)

        locator.screenshot(path=str(output_abs))
        browser.close()

    print(f"Screenshot saved: {output_abs}")


def default_output_path(html_path: Path) -> Path:
    """Derive the default screenshot path from an HTML file path.

    Replaces the html/ directory component with screenshots/ and appends .png.
    Falls back to a screenshots/ sibling of the HTML file's parent if no html/ component exists.

    Args:
        html_path: Resolved path to the HTML file.

    Returns:
        Derived output path.
    """
    parts = html_path.parts
    try:
        idx = len(parts) - 1 - list(reversed(parts)).index("html")
        screenshots_dir = Path(*parts[:idx]) / "screenshots" / Path(*parts[idx + 1 : -1])
    except ValueError:
        screenshots_dir = html_path.parent.parent / "screenshots"
    return screenshots_dir / (html_path.name + ".png")


def screenshot_game(
    html_path: str,
    output_path: str | None = None,
    width: int = 520,
    show_play_btn: bool = False,
    backend: str = "auto",
    element: str = ".f4-game",
) -> None:
    """Screenshot an element from a standalone Find4 HTML file.

    Args:
        html_path: Path to the standalone HTML file.
        output_path: Output PNG path. Defaults to a screenshots/ sibling directory with .png appended.
        width: Viewport width in pixels.
        show_play_btn: When True, keep the Play button visible in the screenshot.
        backend: 'auto', 'docker', or 'local'.
        element: CSS selector for the element to screenshot.
    """
    html_abs = Path(html_path).resolve()
    if not html_abs.exists():
        print(f"ERROR: HTML file not found: {html_path}", file=sys.stderr)
        sys.exit(1)

    output_abs = Path(output_path).resolve() if output_path else default_output_path(html_abs)
    output_abs.parent.mkdir(parents=True, exist_ok=True)

    use_docker = False
    if backend == "docker":
        use_docker = True
    elif backend == "local":
        use_docker = False
    else:  # auto
        use_docker = docker_available()
        if use_docker:
            print(f"Backend: Docker ({DOCKER_IMAGE_TAG})")
        else:
            print("Backend: local playwright (Docker not available)")

    if use_docker:
        screenshot_via_docker(html_abs, output_abs, width, show_play_btn, element)
    else:
        screenshot_via_local(html_abs, output_abs, width, show_play_btn, element)


def main() -> None:
    """Entry point for the screenshot_game CLI."""
    parser = argparse.ArgumentParser(
        description="Screenshot a Find4 game card from its standalone HTML."
    )
    parser.add_argument("--html", required=True, help="Path to the standalone HTML file")
    parser.add_argument(
        "--output",
        default=None,
        help="Output PNG path (default: screenshots/ sibling dir, <html-filename>.png)",
    )
    parser.add_argument("--width", type=int, default=520, help="Viewport width (default: 520)")
    parser.add_argument(
        "--show-play-btn", action="store_true", help="Keep the Play button visible"
    )
    parser.add_argument(
        "--backend",
        choices=["auto", "docker", "local"],
        default="auto",
        help="Backend: auto (default), docker, or local",
    )
    parser.add_argument(
        "--element",
        default=".f4-game",
        help="CSS selector for the element to screenshot (default: .f4-game)",
    )
    args = parser.parse_args()
    screenshot_game(args.html, args.output, args.width, args.show_play_btn, args.backend, args.element)


if __name__ == "__main__":
    main()
