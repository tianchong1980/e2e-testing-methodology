"""
Visual Verification Patterns
Demonstrates how to verify page content actually changed, not just URL
"""
from playwright.sync_api import sync_playwright

def verify_h1_contains(page, expected_text):
    """Verify H1 contains expected text"""
    h1 = page.locator('h1').first
    if h1.is_visible():
        actual = h1.text_content()
        return expected_text in actual, actual
    return False, None

def verify_element_text(page, selector, expected_text):
    """Verify specific element contains expected text"""
    el = page.locator(selector).first
    if el.is_visible():
        actual = el.text_content()
        return expected_text in actual, actual
    return False, actual

def test_navigation_visual_verification(base_url='http://localhost:3000'):
    """
    Test navigation with visual verification
    Critical: URL changing does NOT mean page content updated
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Login
        page.goto(f'{base_url}/login')
        page.wait_for_load_state('networkidle')
        page.fill('input[type="text"]', 'admin')
        page.fill('input[type="password"]', 'admin123')
        page.get_by_role('button', name='Login').click()
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)
        print("[PASS] Logged in")

        # Define navigation test cases
        pages_to_test = [
            {'menu': 'Dashboard', 'url_part': '/dashboard', 'check_text': 'Dashboard'},
            {'menu': 'Settings', 'url_part': '/settings', 'check_text': 'Settings'},
        ]

        for page_info in pages_to_test:
            # Use menu click (not page.goto) to test real navigation
            page.locator(f'nav >> text={page_info["menu"]}').click()
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(1000)

            # Verify URL changed
            url_ok = page_info['url_part'] in page.url
            print(f"[{'PASS' if url_ok else 'FAIL'}] URL: {page.url}")

            # CRITICAL: Verify page content changed (not just URL)
            h1_ok, h1_text = verify_h1_contains(page, page_info['check_text'])
            print(f"[{'PASS' if h1_ok else 'FAIL'}] Content: {h1_text}")

            # Screenshot
            page.screenshot(path=f'nav_{page_info["menu"].lower()}.png', fullPage=True)

        browser.close()

def test_state_pollution_detection(base_url='http://localhost:3000'):
    """
    Test for navigation state pollution
    A problematic page can "poison" global state, breaking ALL subsequent navigation
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Login
        page.goto(f'{base_url}/login')
        page.wait_for_load_state('networkidle')
        # ... login logic ...

        # Step 1: Visit potentially problematic page
        page.goto(f'{base_url}/problematic-page')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)

        # Check for render errors
        body_text = page.locator('body').inner_text()
        has_nan = 'NaN' in body_text
        has_undefined = 'undefined' in body_text
        print(f"[INFO] Problematic page: NaN={has_nan}, undefined={has_undefined}")

        # Step 2: Navigate to subsequent pages using menu click
        subsequent_pages = [
            ('Page 1', '/page1', 'h1'),
            ('Page 2', '/page2', 'h1'),
            ('Page 3', '/page3', 'h1'),
        ]

        for menu_text, expected_url, selector in subsequent_pages:
            page.locator(f'nav >> text="{menu_text}"').click()
            page.wait_for_timeout(2000)

            url_ok = expected_url in page.url
            content_ok = page.locator(selector).count() > 0

            status = "PASS" if (url_ok and content_ok) else "FAIL"
            print(f"[{status}] {menu_text}: url={url_ok}, content={content_ok}")

        browser.close()

def test_api_ui_consistency(api_base='http://localhost:4000/api', page_url='http://localhost:3000/entities'):
    """Verify API data matches UI display exactly"""
    import requests

    # 1. Call API directly
    response = requests.get(f'{api_base}/entities')
    api_data = response.json()

    # 2. UI verification
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(page_url)
        page.wait_for_load_state('networkidle')

        rows = page.locator('table tbody tr').all()
        for i, row in enumerate(rows):
            cells = row.locator('td').all()
            if len(cells) >= 2:
                ui_value = cells[1].text_content()
                if i < len(api_data.get('data', {}).get('records', [])):
                    api_value = api_data['data']['records'][i].get('name', '')
                    match = ui_value == api_value
                    print(f"[{'PASS' if match else 'FAIL'}] Row {i}: UI '{ui_value}' vs API '{api_value}'")

        browser.close()

if __name__ == '__main__':
    test_navigation_visual_verification()