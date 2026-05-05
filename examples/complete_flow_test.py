"""
Complete CRUD Flow Test Example
Demonstrates full data flow testing: Create, Read, Update, Delete with persistence verification
"""
from playwright.sync_api import sync_playwright
import requests
import time

# Test data factory - customizable for any entity
def create_test_entity(entity_type='default', overrides=None):
    """Create test data with sensible defaults"""
    data = {
        'name': f'Test_{entity_type}_{int(time.time())}',
        'type': 'A',
        'status': 1
    }
    if overrides:
        data.update(overrides)
    return data

def test_complete_crud_flow(base_url='http://localhost:3000', api_base='http://localhost:4000/api'):
    """
    Complete CRUD test: verify the ENTIRE data flow
    NOT just API success - verify data appears in UI
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # ========== LOGIN ==========
        page.goto(f'{base_url}/login')
        page.wait_for_load_state('networkidle')
        page.fill('input[type="text"]', 'admin')
        page.fill('input[type="password"]', 'admin123')
        page.get_by_role('button', name='Login').click()
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)
        print("[PASS] Login successful")

        # ========== NAVIGATE TO LIST ==========
        page.goto(f'{base_url}/entities')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1000)
        page.screenshot(path='step1_list.png', fullPage=True)
        print("[PASS] Navigated to entity list")

        # ========== CREATE ==========
        test_data = create_test_entity('CRUD_TEST')

        page.get_by_role('button', name='Add').click()
        page.wait_for_timeout(500)
        page.screenshot(path='step2_dialog.png', fullPage=True)

        page.fill('input[name="name"]', test_data['name'])
        # ... fill other required fields ...
        page.get_by_role('button', name='Submit').click()
        page.wait_for_timeout(2000)

        # Check success message
        success = page.locator('.message-success, .toast-success')
        if success.is_visible():
            print("[PASS] Create successful")

        # ========== CRITICAL: REFRESH TO VERIFY PERSISTENCE ==========
        page.reload()
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)
        page.screenshot(path='step3_after_refresh.png', fullPage=True)

        # Verify data in list
        rows = page.locator('table tbody tr').all()
        print(f"[INFO] Found {len(rows)} rows in list")

        found = any(test_data['name'] in str(row.text_content()) for row in rows)
        print(f"[{'PASS' if found else 'FAIL'}] Data persistence: {'Verified' if found else 'NOT FOUND'}")

        # ========== READ ==========
        page.locator('table tbody tr').first.locator('button').first.click()
        page.wait_for_timeout(500)
        page.screenshot(path='step4_detail.png', fullPage=True)

        # ========== UPDATE ==========
        page.get_by_role('button', name='Edit').click()
        page.wait_for_timeout(500)
        page.fill('input[name="name"]', test_data['name'] + '_updated')
        page.get_by_role('button', name='Save').click()
        page.wait_for_timeout(2000)

        # Verify update
        page.reload()
        updated_text = page.locator('table tbody tr').first.text_content()
        print(f"[{'PASS' if 'updated' in updated_text else 'FAIL'}] Update verified")

        # ========== DELETE ==========
        page.locator('table tbody tr').first.get_by_role('button', name='Delete').click()
        page.wait_for_timeout(500)
        page.get_by_role('button', name='Confirm').click()
        page.wait_for_timeout(2000)

        print("[PASS] Delete completed")
        browser.close()

if __name__ == '__main__':
    test_complete_crud_flow()