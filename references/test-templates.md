# Test Templates Reference

> This file contains detailed code templates referenced by SKILL.md.

## Navigation Bug Detection

```javascript
async function testNavigationAfterPage(page, poisonPageUrl, subsequentPages) {
    // 1. Login
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    // ... login logic ...

    // 2. Visit the potentially problematic page
    await page.goto(`${BASE_URL}${poisonPageUrl}`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // 3. Check for render errors on the page itself
    const bodyText = await page.locator('body').innerText();
    const hasNaN = bodyText.includes('NaN');
    const hasUndefined = bodyText.includes('undefined');
    console.log(`Poison page: NaN=${hasNaN}, undefined=${hasUndefined}`);

    // 4. Navigate to each subsequent page and verify
    for (const { menuText, expectedUrl, expectedSelector } of subsequentPages) {
        await page.locator(`text="${menuText}"`).click();
        await page.waitForTimeout(2000);

        const urlOk = page.url().includes(expectedUrl);
        const contentOk = await page.locator(expectedSelector).count() > 0;
        const renderOk = !bodyText.includes('NaN') && !bodyText.includes('undefined');

        const status = urlOk && contentOk && renderOk ? "PASS" : "FAIL";
        console.log(`[${status}] ${menuText}: url=${urlOk}, content=${contentOk}, render=${renderOk}`);
    }
}
```

**Why Menu Click vs `page.goto` Matters**:
- `page.goto()` creates a fresh application state
- Menu click uses router programmatically, preserving any corrupted state
- The bug only manifests when using menu click after visiting the problematic page

## Field Mapping Error Investigation

```javascript
async function investigateFieldMappingError(page, pageUrl) {
    await page.goto(`${BASE_URL}${pageUrl}`);
    await page.waitForLoadState('networkidle');

    // 1. Check for NaN/undefined in body
    const body = await page.locator('body').innerText();
    if (body.includes('NaN') || body.includes('undefined')) {
        console.log(`[FIELD_MAPPING_ERROR] Detected in ${pageUrl}`);
    }

    // 2. Capture console errors
    page.on('console', msg => {
        if (msg.type() === 'error') {
            console.log(`Console error: ${msg.text()}`);
        }
    });

    // 3. Check API response directly
    const apiPath = extractApiPathFromNetwork(page);
    const response = await fetch(`${API_BASE_URL}${apiPath}`);
    console.log(`API status: ${response.status}`);

    // 4. Compare API fields vs component expectations
}
```

## Module-Level Complete Testing

```javascript
async function testModuleComplete(page, moduleName, pagesConfig) {
    const results = [];
    for (const pageInfo of pagesConfig) {
        await page.goto(`${BASE_URL}${pageInfo.url}`);
        await page.waitForLoadState('networkidle');
        await page.screenshot({ path: `${pageInfo.name}.png`, fullPage: true });

        const errors = captureConsoleErrors(page);
        results.push({
            name: pageInfo.name,
            urlOk: page.url().includes(pageInfo.url),
            contentOk: (await page.locator('body').innerText()).includes(pageInfo.checkText),
            hasErrors: errors.length > 0
        });
    }

    for (const r of results) {
        if (!r.urlOk || !r.contentOk || r.hasErrors) {
            throw new Error(`${r.name} failed`);
        }
    }
}
```

## Complete CRUD Test

```javascript
const { chromium } = require('playwright');

async function testCrudCompleteFlow() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();

    // 1. Login
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // 2. Navigate to target page
    await page.goto(`${BASE_URL}/{module}/{entity}-list`);
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'step1_list.png', fullPage: true });

    // 3. Click add button
    await page.getByRole('button', { name: /add|create|new/i }).click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'step2_dialog.png', fullPage: true });

    // 4. Fill form
    await page.fill('input[name="name"]', 'Test Entity');

    // 5. Submit
    await page.getByRole('button', { name: /submit|save/i }).click();
    await page.waitForTimeout(2000);

    // 6. Check success
    const success = page.locator('.message:has-text("Success"), .toast:has-text("Success")');
    if (await success.isVisible()) {
        console.log("SUCCESS: Add successful");
    }

    // 7. Refresh to verify persistence
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'step4_after_refresh.png', fullPage: true });

    // 8. Verify data in list
    const rows = page.locator('table tbody tr').all();
    console.log(`Found ${rows.length} rows in list`);

    // 9. Verify detail display
    await page.locator('.action-buttons button').first.click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'step5_detail.png', fullPage: true });

    await browser.close();
}
```

## CRUD Operations Template

```javascript
async function testCrudTemplate(page) {
    // CREATE
    await page.getByRole('button', { name: /add|create/i }).click();
    await page.getByRole('button', { name: /submit|save/i }).click();
    expect(await page.locator('.message-success').isVisible()).toBe(true);

    // READ - verify in list
    await page.reload();
    expect(await page.locator('text=NewItemName').isVisible()).toBe(true);

    // UPDATE
    await page.locator('.action-btns >> button >> nth=0').click();
    await page.getByRole('button', { name: /save/i }).click();
    expect(await page.locator('.message-success').isVisible()).toBe(true);

    // DELETE
    await page.locator('.action-btns .icon-delete').click();
    await page.getByRole('button', { name: /confirm/i }).click();
    expect(await page.locator('.message-success').isVisible()).toBe(true);
}
```

## Test Data Cleanup Fixture

```javascript
async function setupTestData() {
    const response = await fetch(`${API_BASE_URL}/test/setup`, {
        method: 'POST',
        body: JSON.stringify(testData)
    });
    return response.json();
}

async function cleanupTestData() {
    await fetch(`${API_BASE_URL}/test/cleanup`, { method: 'DELETE' });
}

beforeEach(async () => { await cleanupTestData(); await setupTestData(); });
afterEach(async () => { await cleanupTestData(); });
```

## Placeholder Component Detection

```javascript
const fs = require('fs');
const path = require('path');

function checkComponentIntegrity(viewsDir, expectedMinLines = 50) {
    const results = [];
    const files = fs.readdirSync(viewsDir).filter(f => f.endsWith('.vue'));

    for (const file of files) {
        const filepath = path.join(viewsDir, file);
        const content = fs.readFileSync(filepath, 'utf-8');
        const lines = content.split('\n').length;

        const isPlaceholder = (
            content.includes('Coming soon') ||
            content.includes('Under development') ||
            content.includes('建设中') ||
            content.includes('开发中') ||
            lines < expectedMinLines
        );

        results.push({ file, lines, status: isPlaceholder ? 'PLACEHOLDER' : 'OK' });
    }
    return results;
}
```
