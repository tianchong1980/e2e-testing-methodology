---
name: e2e-testing-methodology
description: Comprehensive E2E testing methodology for web applications. Covers complete data flow testing, boundary testing, error handling verification, and visual validation patterns. Use when testing web applications end-to-end, verifying UI behavior, testing CRUD operations, or debugging navigation/display issues.
---

# E2E Testing Methodology

Comprehensive end-to-end testing methodology for modern web applications.

## Table of Contents

1. [Core Principle](#1-core-principle-complete-data-flow-testing)
2. [Standard Test Process](#2-standard-test-process)
3. [Visual Verification](#3-visual-verification)
4. [Navigation Bug Detection](#4-navigation-bug-detection-patterns)
5. [Field Mapping Error Detection](#5-field-mapping-error-detection)
6. [Module-Level Complete Testing](#6-module-level-complete-testing)
7. [Pre-Test Exploration](#7-pre-test-exploration-principle)
8. [Boundary Testing](#8-boundary-testing-patterns)
9. [Error Handling](#9-error-handling-patterns)
10. [Backend Maintenance](#10-backend-maintenance-during-testing)
11. [Test Patterns](#11-test-patterns)
12. [Test Data Management](#12-test-data-management)
13. [Regression Strategy](#13-regression-testing-strategy)
14. [Data Persistence Troubleshooting](#14-data-persistence-troubleshooting)

---

## 1. Core Principle: Complete Data Flow Testing

**Problem**: Verifying an API returns 200 is NOT sufficient. You must verify the complete data flow from user action to visible result.

**Data Flow Chain**:
```
User Action → API Request → Server Processing → Database Write → API Response → Frontend Read → Field Mapping → UI Render → User Sees Result
```

**Mandatory Test Steps**:
1. **API Call Verification**: Request sent with correct parameters, correct status code
2. **Database Verification**: Data actually persisted (query database to confirm)
3. **Page Refresh Verification**: Data still present after refresh (not just in memory)
4. **List Display Verification**: Table/list columns display correctly
5. **Detail Display Verification**: Detail view/drawer/modal fields are correct
6. **Screenshot Comparison**: Key steps captured for expected vs actual comparison

---

## 2. Standard Test Process Template

```
1. Execute operation (create/modify/delete)
2. Wait for operation to complete (networkidle)
3. Screenshot current state
4. Refresh page (or re-navigate)
5. Wait for page to load
6. Screenshot after refresh state
7. Check page element CONTENT (not just element exists)
8. Compare input values with display values
9. Clean up test data (if needed)
```

**Test Checklist**:
- [ ] API call returns success
- [ ] Data saved to database
- [ ] Data persists after refresh
- [ ] List columns display correctly
- [ ] Detail fields display correctly
- [ ] Input values match display values

---

## 3. Visual Verification

**Problem**: URL changing does NOT mean page content updated. JavaScript errors can cause URL to change but page fails to render.

**Correct Approach**:
- Check page title or primary heading (H1, H2)
- Check key element content
- Take screenshots for comparison
- Verify actual DOM element values, not just presence

**Example Pattern**:
```
URL changed to /module/page2 ✓
But page content still shows page1 ✗
Root cause: JavaScript error prevented component from rendering
```

**Visual Verification Template**:
```javascript
// Verify page content actually changed
const h1 = page.locator('h1').first;
const actualText = h1.textContent();
if (!expectedText.includes(actualText)) {
    throw new Error(`Page content mismatch: expected "${expectedText}", got "${actualText}"`);
}
```

---

## 4. Navigation Bug Detection Patterns

**Critical Pattern**: A specific page can "poison" the global application state, breaking ALL subsequent navigation.

**Symptom**: After visiting Page A, navigating to Page B shows Page A's content despite URL changing to Page B.

**Root Cause**: Uncaught exception in Page A's component (e.g., template field mapping error) crashes the component instance. The crashed instance remains in memory and continues rendering despite router navigation.

**Detection Test Template**:
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
        // Use menu click, not page.goto (simulates real user behavior)
        await page.locator(`text="${menuText}"`).click();
        await page.waitForTimeout(2000);

        // Check URL changed
        const urlOk = page.url().includes(expectedUrl);

        // Check content changed (critical!)
        const contentOk = await page.locator(expectedSelector).count() > 0;

        // Check no render errors
        const renderOk = !bodyText.includes('NaN') && !bodyText.includes('undefined');

        const status = urlOk && contentOk && renderOk ? "PASS" : "FAIL";
        console.log(`[${status}] ${menuText}: url=${urlOk}, content=${contentOk}, render=${renderOk}`);
    }
}
```

**Why Menu Click vs page.goto Matters**:
- `page.goto()` creates a fresh application state
- Menu click uses router programmatically, preserving any corrupted state
- The bug only manifests when using menu click after visiting the problematic page

---

## 5. Field Mapping Error Detection

**Problem**: Missing fields in API response cause template errors (e.g., `undefined` → `NaN` in template rendering).

**Detection Signs**:
1. Body text contains "NaN" or "undefined"
2. Console shows render errors
3. API returns 200 but page doesn't render correctly
4. Specific page causes subsequent navigation to fail

**Investigation Process**:
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
    // Get expected fields from component source
    // Get actual fields from API response
    // Find missing fields
}
```

**Layer-by-Layer Debugging Process**:

```
Step 1: API Test
    curl http://{api_host}:{api_port}/{module}/{entity}
    → Check status, error messages

Step 2: Database Schema Check
    SELECT column_name FROM information_schema.columns
    WHERE table_name = '{entity_table}';
    → Compare with what API should return

Step 3: Code Layer Check
    - Entity: Has all fields the API needs to return?
    - DTO: Has all fields the API needs to return?
    - Service: Does mapping include ALL fields?
    - Controller: Does path match what frontend calls?

Step 4: Fix All Layers
    - Database: Add missing columns
    - Entity: Add missing fields
    - DTO: Add missing fields
    - Service: Update mapping methods
```

---

## 6. Module-Level Complete Testing

**Problem**: Only testing the reported page is NOT sufficient. You must test ALL pages in a module.

**Common Mistake**:
```
Found /module/pageA has problem → Only test this page
Fixed pageA and assume module is fine → But pageB and pageC also have errors
```

**Why This Is Wrong**:
- Each page calls different APIs
- Each page has different data processing logic
- Each page may have different error scenarios

**Module Testing Template**:
```javascript
async function testModuleComplete(page, moduleName, pagesConfig) {
    const results = [];
    for (const pageInfo of pagesConfig) {
        await page.goto(`${BASE_URL}${pageInfo.url}`);
        await page.waitForLoadState('networkidle');
        await page.screenshot({ path: `${pageInfo.name}.png`, fullPage: true });

        // Check for console errors
        const errors = captureConsoleErrors(page);

        results.push({
            name: pageInfo.name,
            urlOk: page.url().includes(pageInfo.url),
            contentOk: (await page.locator('body').innerText()).includes(pageInfo.checkText),
            hasErrors: errors.length > 0
        });
    }

    // ALL pages must pass, not just the one you tested
    for (const r of results) {
        if (!r.urlOk || !r.contentOk || r.hasErrors) {
            throw new Error(`${r.name} failed`);
        }
    }
}
```

**Module Testing Checklist**:
```
Module: XXX
├── [ ] Page 1 - URL accessible
│   ├── [ ] API works
│   ├── [ ] Content renders
│   └── [ ] No console errors
├── [ ] Page 2 - URL accessible
│   └── ...
├── [ ] Page 3 - URL accessible
│   └── ...
└── [ ] Page N - URL accessible
    └── ...
```

---

## 7. Pre-Test Exploration Principle

**Critical**: Always explore the actual structure BEFORE writing tests. Do NOT assume what pages exist.

**Common Mistake**:
```
I assumed "Module X" has only 1 page.
In reality it has N pages.
Result: Only tested 1 page, leaving N-1 untested.
```

**Correct Approach**:
```javascript
// Step 1: BEFORE testing, explore the actual structure
// Read frontend router configuration
const routerFile = 'frontend/src/router/index.ts';
const menuFile = 'frontend/src/components/Layout.vue';

// Step 2: Extract ALL routes from the router
// NOT just the ones you "think" exist

// Step 3: Build complete test list by exploring ALL menu items

// Step 4: Test EVERY page in the list, not just a sample
```

**Pre-Test Checklist**:
```
[ ] Did you read the frontend router configuration?
[ ] Do you know exactly how many pages each menu has?
[ ] Is your test list complete, not assumed?

Avoid:
[ ] Don't assume "this menu probably has 1-2 pages"
[ ] Don't test only routes you already know
[ ] Don't use "I think" instead of "it actually has"
```

---

## 8. Boundary Testing Patterns

| Test Scenario | Example Values |
|--------------|-----------------|
| Pagination | page=0, page=-1, page=1, size=0, size=MAX (define MAX for your system) |
| String length | empty string, single char, 255 chars, 256 chars, 1000 chars |
| Number range | 0, negative value, minimum, maximum, maximum+1 |
| Required fields | all omitted, some omitted, one omitted, whitespace only |

**Example Test Scenarios**:
```
- GET /api/{module}/list?page=0      → Expected: validation error
- GET /api/{module}/list?page=-1     → Expected: validation error
- GET /api/{module}/list?size=0      → Expected: validation error
- POST /api/{module} + empty JSON    → Expected: 400 validation error
- POST /api/{module} + missing required fields → Expected: 400 with clear message
```

---

## 9. Error Handling Patterns

**Required Error Scenarios to Test**:

| Error Type | What to Verify | Expected Result |
|------------|----------------|-----------------|
| Validation failure | Missing required fields | 400 + clear error message |
| Resource not found | Query non-existent ID | 404 or empty data |
| Authentication failure | Token expired/invalid | 401 |
| Permission denied | Operation without permission | 403 |
| Server error | Simulate exception | 500 + friendly message |
| Timeout | API response exceeds limit | 504 or timeout handling |
| Empty data | Query returns no records | Empty array, no crash |
| Concurrent access | Multiple simultaneous requests | Data integrity maintained |

**API Path Consistency Verification**:
```
[ ] Frontend calls: /api/{module}/{entity}s (plural or singular?)
[ ] Backend has: /api/{module}/{entity} (matching?) → 404 if mismatch
[ ] Fix: Add path variants to @RequestMapping if needed
```

**Error Analysis Checklist** (MUST complete for every 500 error):
```
[ ] 1. Identify specific API path (from frontend code or network request)
[ ] 2. Check if backend has this endpoint (curl test)
[ ] 3. If not, determine what the correct endpoint is
[ ] 4. Compare frontend call vs backend implementation
[ ] 5. Determine root cause:
    ├── PATH_MISMATCH: Frontend/backend path inconsistency
    ├── PARAM_ERROR: Parameter format/type error
    ├── BACKEND_BUG: Backend code issue
    └── DB_ERROR: Database error
[ ] 6. Fix immediately if obvious (e.g., path mismatch)
```

---

## 10. Backend Maintenance During Testing

**Important**: When testing reveals backend issues, you MUST be able to restart the backend yourself.

### Restart Backend Process

```bash
# 1. Find process on API port (e.g., 8080)
netstat -ano | grep {port} | grep LISTENING

# 2. Kill the process
taskkill //F //PID {PID}

# 3. Start backend in background
cd {backend-root}
./mvnw spring-boot:run > backend.log 2>&1 &

# 4. Wait for startup and verify
sleep 30
curl -s -o /dev/null -w "%{http_code}" http://{api_host}:{api_port}/api/health
```

### When to Restart Backend

| Test Finding | Action |
|-------------|--------|
| New Controller added | Restart backend |
| Controller returns 500 but code looks correct | Restart backend |
| API behavior inconsistent | Restart backend |
| Database connection issues | Restart backend |

---

## 11. Test Patterns

### Complete Data Flow Test

```javascript
const { chromium } = require('playwright');

async function testCrudCompleteFlow() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();

    // 1. Login
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    // ... login steps ...
    await page.waitForTimeout(2000);

    // 2. Navigate to target page
    await page.goto(`${BASE_URL}/{module}/{entity}-list`);
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'step1_list.png', fullPage: true });

    // 3. Click add button (use framework-agnostic selector)
    await page.getByRole('button', { name: /add|create|new/i }).click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'step2_dialog.png', fullPage: true });

    // 4. Fill form with test data
    await page.fill('input[name="name"]', 'Test Entity');
    // ... fill other fields ...

    // 5. Submit
    await page.getByRole('button', { name: /submit|save/i }).click();
    await page.waitForTimeout(2000);

    // 6. Check success message
    const success = page.locator('.message:has-text("Success"), .toast:has-text("Success")');
    if (await success.isVisible()) {
        console.log("SUCCESS: Add successful");
    }

    // 7. CRITICAL: Refresh page to verify persistence
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

### Visual Content Verification

```javascript
async function verifyPageContentChanged(page, expectedText, selector = 'h1') {
    const element = page.locator(selector).first;
    if (await element.isVisible()) {
        const actualText = await element.textContent();
        return expectedText.includes(actualText);
    }
    return false;
}

async function testNavigationVisualVerification(page) {
    // ... login and navigate ...

    // After clicking a menu
    await page.locator('nav >> text=MenuLabel').click();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Verify URL changed
    expect(page.url()).toContain('/{module}/page');

    // CRITICAL: Verify page content changed
    const h1Text = await page.locator('h1').first.textContent();
    expect(h1Text).toContain('ExpectedContent');

    // Screenshot comparison
    await page.screenshot({ path: 'nav_result.png', fullPage: true });
}
```

### AAA Pattern

**Arrange**: Prepare test data
```javascript
function createTestEntity(overrides = {}) {
    const data = {
        name: 'Test Entity',
        type: 'A',
        status: 1
    };
    return { ...data, ...overrides };
}
```

**Act**: Execute the operation
```javascript
await page.fill('input[name="name"]', 'Test Entity');
await page.getByRole('button', { name: 'Submit' }).click();
```

**Assert**: Verify expected results
```javascript
const success = page.locator('.message-success');
expect(await success.isVisible()).toBe(true);
```

### CRUD Operations Template

```javascript
async function testCrudTemplate(page) {
    // CREATE
    await page.getByRole('button', { name: /add|create/i }).click();
    // ... fill form ...
    await page.getByRole('button', { name: /submit|save/i }).click();
    expect(await page.locator('.message-success').isVisible()).toBe(true);

    // READ - verify in list
    await page.reload();
    expect(await page.locator('text=NewItemName').isVisible()).toBe(true);

    // UPDATE
    await page.locator('.action-btns >> button >> nth=0').click();
    // ... modify form ...
    await page.getByRole('button', { name: /save/i }).click();
    expect(await page.locator('.message-success').isVisible()).toBe(true);

    // DELETE
    await page.locator('.action-btns .icon-delete').click();
    await page.getByRole('button', { name: /confirm/i }).click();
    expect(await page.locator('.message-success').isVisible()).toBe(true);
}
```

### Form Validation

```javascript
async function testFormValidation(page) {
    // Leave required field empty
    await page.getByRole('button', { name: /submit/i }).click();

    // Check for validation error
    const errors = page.locator('.form-error, .field-error, [role="alert"]');
    expect(await errors.count()).toBeGreaterThan(0);

    const errorTexts = await errors.allTextContents();
    console.log(`Validation errors: ${errorTexts}`);
}
```

---

## 12. Test Data Management

### Test Data Cleanup

```javascript
// Use fixture for automatic cleanup
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

// Use beforeEach/afterEach for isolation
beforeEach(async () => {
    await cleanupTestData();
    await setupTestData();
});

afterEach(async () => {
    await cleanupTestData();
});
```

### Test Data Factory

```javascript
class TestDataFactory {
    static createEntity(type = 'default') {
        return {
            name: `Test_${Date.now()}`,
            type,
            status: 1,
            createdAt: new Date().toISOString()
        };
    }

    static createBulk(count = 5) {
        return Array.from({ length: count }, (_, i) =>
            this.createEntity(`type_${i}`)
        );
    }
}
```

---

## 13. Regression Testing Strategy

| Test Level | Trigger | Coverage |
|-----------|---------|----------|
| Smoke Tests | Every commit | Login, main page, critical CRUD |
| Module Tests | Every PR | All pages in modified module |
| Full Regression | Before merge | All tests |

**Smoke Tests** (run on every commit):
- Login/logout
- Main dashboard loads
- Critical CRUD operations

**Full Regression** (run before PR merge):
- All unit tests
- All integration tests
- All E2E tests

---

## 14. Data Persistence Troubleshooting

### Core Principle

**When data is lost/overwritten/wrong, systematically check ALL data write/delete paths, not just recently modified code.**

### Problem Types

| Type | Symptom | Check First |
|------|---------|------------|
| Data Lost | Missing after restart | `sql.init.mode`, initialization scripts |
| Data Overwritten | Becomes default after restart | Data initialization logic |
| Data Duplicated | Two identical records | Unique constraints, idempotency |

### Configuration Safety Rules

```yaml
# DANGEROUS - Will reset database on every startup
spring:
  sql:
    init:
      mode: always  # WRONG!

# SAFE - Only application manages data
spring:
  sql:
    init:
      mode: never   # CORRECT!
```

### Data Persistence Verification Template

```javascript
async function testDataPersistenceAfterRestart() {
    // 1. Start fresh
    await restartBackend();

    // 2. Create test data via API
    const response = await fetch(`${API_BASE_URL}/{module}/{entity}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testData)
    });
    expect(response.status).toBe(200);
    const dataId = (await response.json()).data.id;

    // 3. FIRST verification: Data exists immediately after creation
    const verify1 = await fetch(`${API_BASE_URL}/{module}/{entity}/${dataId}`);
    expect(verify1.status).toBe(200);

    // 4. Restart backend (THE CRITICAL TEST)
    await restartBackend();

    // 5. SECOND verification: Data still exists after restart
    const verify2 = await fetch(`${API_BASE_URL}/{module}/{entity}/${dataId}`);
    expect(verify2.status).toBe(200), "Data lost after restart!";

    // 6. Verify via browser
    await page.goto(`${BASE_URL}/{module}/{entity}-list`);
    await page.waitForLoadState('networkidle');
    expect((await page.locator('body').innerText()).includes(testData.name)).toBe(true);
}
```

### Investigation Order for Data Issues

```
Data Problem Detected
    ↓
Check 1: Configuration sql.init.mode
    ├── mode: always → Found root cause!
    └── mode: never → Continue
    ↓
Check 2: Initialization scripts for DROP TABLE statements
    ├── Has DROP TABLE → Found root cause!
    └── No DROP TABLE → Continue
    ↓
Check 3: Data initialization logic
    ├── Overwrites data → Fix logic
    └── Preserves data → Continue
    ↓
Check 4: API endpoints
    └── Check INSERT/UPDATE logic
```

---

## Placeholder Component Problem Pattern

**Problem**: A component file contains only a placeholder ("Coming soon" or "Under development") instead of actual implementation. When routing points to this component, the page appears blank or shows a stub, causing navigation to freeze.

**Symptom**:
- Click menu → URL changes → Page shows placeholder text or blank
- After visiting the page, clicking other menus does NOT change content (navigation freezes)

**Root Cause**:
- Two files exist for the same route: `FullView.vue` (complete) and `Stub.vue` (placeholder)
- Router imports `FullView.vue` but `Stub.vue` was previously modified to be a placeholder
- When application renders, it may load the wrong file or have stale cached state

**Detection Method**:
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

        results.push({
            file,
            lines,
            status: isPlaceholder ? 'PLACEHOLDER' : 'OK'
        });
    }

    return results;
}
```

**Prevention Checklist**:
```
Before modifying any component:
[ ] Check if multiple versions exist for the same route
[ ] Verify router points to the correct file
[ ] Confirm target file has actual implementation
[ ] Check if file contains placeholder text

After modifying any component:
[ ] Verify page renders correctly (not blank)
[ ] Test navigation TO this page
[ ] Test navigation FROM this page to other pages
[ ] Test navigation AFTER visiting this page (state pollution check)
```

---

## Field Mapping Error Patterns (Critical)

**Root Cause**: Uncaught exceptions in template expressions crash the component instance, causing state pollution that breaks ALL subsequent navigation.

**Common Patterns**:

| Error | Cause | Fix |
|-------|-------|-----|
| `null.split is not a function` | `field.split()` when field is null | `(field \|\| '').split()` |
| `undefined.charCodeAt(0)` | `prop.charCodeAt(0)` when prop is null | `if (!prop) return 'default'` |
| `NaN` in display | Numeric field undefined | `field \|\| 0` |
| Comparison never matches | API returns number, comparison uses string | `status === 1` not `status === '1'` |

**Prevention Checklist**:
- [ ] All template expressions handle null/undefined
- [ ] Numeric comparisons use correct types
- [ ] Functions accept null parameters
- [ ] Numeric fields have defaults

---

## Best Practices Summary

1. **Always refresh page** after create/update to verify persistence
2. **Always check actual UI content**, not just API response
3. **Always take screenshots** for key steps
4. **Always verify error handling** - test both success and failure paths
5. **Wait for networkidle** before taking actions
6. **Verify complete data flow** from user action to visible result
7. **Test navigation AFTER visiting problematic pages** - detect state pollution
8. **Analyze every error** - don't just mark FAIL
9. **Defensive null checking** in all template expressions
10. **Test complete modules**, not just reported pages

---

## Example Files

Reference implementations are available in the `examples/` directory:
- **complete_flow_test.py** - Full CRUD with data verification
- **visual_verification.py** - Page content verification patterns