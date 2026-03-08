
from playwright.sync_api import sync_playwright
import argparse


def main(token: str | None, headless = False) -> None:
    details: dict[str, object] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        def handle_route(route, request):
            url = request.url
            # only abort the *challenge-platform* call which is what actually
            # fetches the captcha widget data.  let the API script itself load so
            # we can see the sitekey in the DOM if needed.
            if "cdn-cgi/challenge-platform" in url:
                print(f"[intercept] {request.method} {url}")

                # record some details from the URL path segments
                parts = url.split("/")
                for seg in parts:
                    if seg.startswith("0x"):
                        details.setdefault("sitekey", seg)
                # the segments following the sitekey typically include pageaction,
                # cdata, pagedata, etc.  capture them verbatim so the user can
                # examine their positions.
                details.setdefault("segments", parts)

                route.abort()
            else:
                route.continue_()

        # a catch-all route that will abort the actual captcha request and
        # record metadata.  register this first so more specific routes can
        # override it.
        page.route("**/*", handle_route)

        # Do not intercept the verification; let it go to the real endpoint
        # so the site shows the actual success message if the token is valid.

        page.goto("https://cd.captchaaiplus.com/turnstile.html")
        page.bring_to_front()
        # wait a short moment so the widget would normally attempt to load
        page.wait_for_timeout(3000)

        # the iframe should not exist because we aborted its requests
        iframe = page.query_selector("iframe")
        print("iframe present?", bool(iframe))
        print("captured details:", details)

        if token:
            # check if the hidden input exists (created by Turnstile script)
            input_exists = page.evaluate("() => !!document.querySelector('input[name=\"cf-turnstile-response\"]')")
            if not input_exists:
                print("hidden input not found; cannot inject token")
                return
            # inject token into the hidden input
            page.evaluate(
                "(t) => { document.querySelector('input[name=\"cf-turnstile-response\"]').value = t; }",
                token,
            )
            print("injected token", token)
            page.click("input[type=submit]")
            # wait for the success message to appear
            page.wait_for_selector("#result")
            result = page.inner_text("#result")
            # avoid encoding errors by writing UTF-8 bytes directly
            import sys
            sys.stdout.buffer.write(f"result message: {result}\n".encode("utf-8", errors="ignore"))
            # keep the browser open for a few seconds so the user can see the success message
            page.wait_for_timeout(5000)
        else:
            print("no token supplied; skipping submission")

        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Intercept Turnstile widget and optionally inject a token.")
    parser.add_argument("--token", help="The Turnstile response token to inject.")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (default: show browser).",
    )
    args = parser.parse_args()
    main(args.token, headless=args.headless)
