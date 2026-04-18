from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    page.goto(
        "https://account.reverso.net/Account/Login?lang=en&utm_source=context&utm_medium=user-menu-header&returnUrl=https%3A%2F%2Fcontext.reverso.net%2Ftranslation%2F"
    )

    print("🔑 Login manually")
    print("👉 after press enter")

    input()

    context.storage_state(path="state.json")

    print("✅ saved in state.json")

    browser.close()