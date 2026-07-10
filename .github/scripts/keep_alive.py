"""Visit the deployed Prism app and wake it up if Streamlit Community Cloud
has put it to sleep due to inactivity.

Streamlit Cloud shows a "Zzzz... This app has gone to sleep due to
inactivity." screen with a "Yes, get this app back up!" button after a period
of inactivity. A plain HTTP ping can't get past the cookie-based auth
redirect in front of the app, and even if it could, waking the app requires
an actual button click in a rendered page — so this uses a real (headless)
browser session.

Exit code is non-zero if the app never finishes loading, so a genuine
failure shows red in CI instead of silently succeeding.

Note: Streamlit Community Cloud renders the actual app inside a child iframe
(observed at "<app>/~/+/") beneath its own viewer chrome (the outer page,
which is what shows the sleep/wake screen). page.get_by_text() only searches
the frame it's called on, so the readiness check must look across every
frame, not just the top-level page.
"""

import sys

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

APP_URL = "https://prism-by-hn.streamlit.app"
WAKE_BUTTON_TEXT = "Yes, get this app back up!"
# Unique to Prism's own loaded UI (see app.py's "hero-sub" tagline) — only
# present once the real app has rendered, not on the sleep/wake screen.
READY_TEXT = "Upload a spreadsheet. Ask a question. Get an answer."


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(APP_URL, timeout=60_000)

        # The wake button is rendered client-side a moment after initial
        # load, not present at goto() time. .click() auto-waits for it to
        # appear; a timeout here just means the app was already awake.
        try:
            page.get_by_role("button", name=WAKE_BUTTON_TEXT).first.click(timeout=15_000)
            print("Wake-up button found and clicked.")
        except PlaywrightTimeoutError:
            print("No wake-up button found — app was likely already awake.")

        deadline_ms = 240_000
        poll_interval_ms = 3_000
        waited_ms = 0
        while waited_ms < deadline_ms:
            for frame in page.frames:
                try:
                    if frame.get_by_text(READY_TEXT).first.is_visible():
                        print(f"App is awake and rendered (frame: {frame.url}).")
                        browser.close()
                        return 0
                except Exception:
                    continue
            page.wait_for_timeout(poll_interval_ms)
            waited_ms += poll_interval_ms

        print("Timed out waiting for the app to finish loading.", file=sys.stderr)
        browser.close()
        return 1


if __name__ == "__main__":
    sys.exit(main())
