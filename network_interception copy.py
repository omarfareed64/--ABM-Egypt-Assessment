from playwright.sync_api import sync_playwright
import re

URL = "https://cd.captchaaiplus.com/turnstile.html"

def extract_params(url):
    params = {}

    sitekey = re.search(r"0x[a-zA-Z0-9]+", url)
    if sitekey:
        params["sitekey"] = sitekey.group(0)

    pageaction = re.search(r"pageaction=([^&]+)", url)
    if pageaction:
        params["pageaction"] = pageaction.group(1)

    cdata = re.search(r"cdata=([^&]+)", url)
    if cdata:
        params["cdata"] = cdata.group(1)

    pagedata = re.search(r"pagedata=([^&]+)", url)
    if pagedata:
        params["pagedata"] = pagedata.group(1)

    return params


def main():
    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        def intercept(route, request):
            url = request.url

            if "challenge-platform" in url:
                print("\nTurnstile request intercepted")
                print("URL:", url)

                params = extract_params(url)

                for k, v in params.items():
                    print(f"{k}: {v}")

            route.continue_()

        page.route("**/*", intercept)

        page.goto(URL)

        print("Waiting for captcha verification...")

        # wait until token appears after solving captcha
        page.wait_for_function(
            """() => {
                const el = document.querySelector('input[name="cf-turnstile-response"]');
                return el && el.value.length > 0;
            }"""
        )

        token = page.eval_on_selector(
            'input[name="cf-turnstile-response"]',
            "el => el.value"
        )

        print("\nTurnstile Token:")
        print(token)

        page.click("input[type=submit]")

        page.wait_for_selector("#result")

        result = page.inner_text("#result")

        print("\nResult:", result)

        page.wait_for_timeout(5000)

        browser.close()


if __name__ == "__main__":
    main()