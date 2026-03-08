from seleniumbase import SB

for headless in [False, True]:
    print(f"\n--- Running headless={headless} ---")

    with SB(uc=True, headless=headless) as sb:
        sb.open("https://cd.captchaaiplus.com/turnstile.html")
        sb.sleep(3)
        sb.solve_captcha()
        sb.wait_for_element_absent("input[disabled]")
        sb.sleep(2)

        # ✅ Extract and print the Turnstile token
        token = sb.get_attribute(
            "input[name='cf-turnstile-response']", 
            "value"
        )
        print(f"Turnstile token: {token}")

        sb.click("input[type=submit]")
        sb.sleep(2)