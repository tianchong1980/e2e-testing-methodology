---
name: e2e-testing-methodology
description: Comprehensive E2E testing methodology for web applications. Covers complete data flow testing, boundary testing, error handling verification, and visual validation patterns. Use when testing web applications end-to-end, verifying UI behavior, testing CRUD operations, or debugging navigation/display issues.
author: tianchong1980
license: MIT
---

# E2E Testing Methodology

Comprehensive end-to-end testing methodology for modern web applications.

## Table of Contents

1. [Core Principle: Complete Data Flow Testing](#1-core-principle-complete-data-flow-testing)
2. [Standard Test Process](#2-standard-test-process)
3. [Visual Verification](#3-visual-verification)
4. [Navigation Bug Detection](#4-navigation-bug-detection-patterns)
5. [Field Mapping Error Detection](#5-field-mapping-error-detection)
6. [Module-Level Complete Testing](#6-module-level-complete-testing)
7. [Pre-Test Exploration](#7-pre-test-exploration-principle)
8. [Boundary Testing](#8-boundary-testing-patterns)
9. [Error Handling](#9-error-handling-patterns)
10. [Backend Maintenance During Testing](#10-backend-maintenance-during-testing)
11. [Test Patterns](#11-test-patterns)
12. [Test Data Management](#12-test-data-management)
13. [Regression Strategy](#13-regression-testing-strategy)
14. [Data Persistence Troubleshooting](#14-data-persistence-troubleshooting)

> **Full code templates**: See [references/test-templates.md](references/test-templates.md) and [references/data-persistence.md](references/data-persistence.md).

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

**Example**:
```
URL changed to /module/page2 ✓
But page content still shows page1 ✗
Root cause: JavaScript error prevented component from rendering
```

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

**Detection Strategy**:
1. Visit the potentially problematic page
2. Check for `NaN`/`undefined` in body text
3. Navigate to subsequent pages via **menu click** (not `page.goto`)
4. Verify URL changed, content changed, and no render errors on each subsequent page

> **Full template**: See [references/test-templates.md](references/test-templates.md#navigation-bug-detection)

**Why Menu Click vs `page.goto` Matters**:
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

**Layer-by-Layer Debugging Process**:
```
Step 1: API Test — curl http://{api_host}:{api_port}/{module}/{entity}
Step 2: Database Schema Check — Compare columns with API expectations
Step 3: Code Layer Check — Entity, DTO, Service, Controller
Step 4: Fix All Layers — DB → Entity → DTO → Service
```

> **Full template**: See [references/test-templates.md](references/test-templates.md#field-mapping-error-investigation)

---

## 6. Module-Level Complete Testing

**Problem**: Only testing the reported page is NOT sufficient. You must test ALL pages in a module.

**Common Mistake**:
```
Found /module/pageA has problem → Only test this page
Fixed pageA and assume module is fine → But pageB and pageC also have errors
```

**Module Testing Checklist**:
```
Module: XXX
├── [ ] Page 1 — URL accessible, API works, Content renders, No errors
├── [ ] Page 2 — URL accessible, API works, Content renders, No errors
├── [ ] Page 3 — URL accessible, API works, Content renders, No errors
└── [ ] Page N — URL accessible, API works, Content renders, No errors
```

> **Full template**: See [references/test-templates.md](references/test-templates.md#module-level-complete-testing)

---

## 7. Pre-Test Exploration Principle

**Critical**: Always explore the actual structure BEFORE writing tests. Do NOT assume what pages exist.

**Correct Approach**:
```javascript
// Step 1: Read frontend router configuration
const routerFile = 'frontend/src/router/index.ts';
const menuFile = 'frontend/src/components/Layout.vue';

// Step 2: Extract ALL routes — NOT just the ones you "think" exist
// Step 3: Build complete test list by exploring ALL menu items
// Step 4: Test EVERY page, not just a sample
```

**Pre-Test Checklist**:
- [ ] Read the frontend router configuration
- [ ] Know exactly how many pages each menu has
- [ ] Test list is complete, not assumed
- [ ] Don't assume "this menu probably has 1-2 pages"
- [ ] Don't test only routes you already know

---

## 8. Boundary Testing Patterns

| Test Scenario | Example Values |
|--------------|-----------------|
| Pagination | page=0, page=-1, page=1, size=0, size=MAX |
| String length | empty string, single char, 255 chars, 256 chars, 1000 chars |
| Number range | 0, negative value, minimum, maximum, maximum+1 |
| Required fields | all omitted, some omitted, one omitted, whitespace only |

```
GET  /api/{module}/list?page=0       → Expected: validation error
GET  /api/{module}/list?page=-1      → Expected: validation error
POST /api/{module} + empty JSON      → Expected: 400 validation error
POST /api/{module} + missing fields  → Expected: 400 with clear message
```

---

## 9. Error Handling Patterns

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

**API Path Consistency**:
- Frontend calls: `/api/{module}/{entity}s` (plural or singular?)
- Backend has: `/api/{module}/{entity}` (matching?)
- Fix: Add path variants to `@RequestMapping` if needed

---

## 10. Backend Maintenance During Testing

```bash
# Find process on API port
netstat -ano | grep {port} | grep LISTENING

# Kill and restart
taskkill //F //PID {PID}
cd {backend-root}
./mvnw spring-boot:run > backend.log 2>&1 &

# Verify
sleep 30
curl -s -o /dev/null -w "%{http_code}" http://{api_host}:{api_port}/api/health
```

**When to Restart**: New Controller added, API behavior inconsistent, controller returns 500 but code looks correct, database connection issues.

---

## 11. Test Patterns

### Complete Data Flow Test

See [references/test-templates.md](references/test-templates.md#complete-crud-test) for the full Playwright template.

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
```

### AAA Pattern (Arrange-Act-Assert)

```javascript
// Arrange
function createTestEntity(overrides = {}) {
    const data = { name: 'Test Entity', type: 'A', status: 1 };
    return { ...data, ...overrides };
}

// Act
await page.fill('input[name="name"]', 'Test Entity');
await page.getByRole('button', { name: 'Submit' }).click();

// Assert
const success = page.locator('.message-success');
expect(await success.isVisible()).toBe(true);
```

### Form Validation

```javascript
async function testFormValidation(page) {
    // Leave required field empty and submit
    await page.getByRole('button', { name: /submit/i }).click();
    const errors = page.locator('.form-error, .field-error, [role="alert"]');
    expect(await errors.count()).toBeGreaterThan(0);
    const errorTexts = await errors.allTextContents();
    console.log(`Validation errors: ${errorTexts}`);
}
```

---

## 12. Test Data Management

Use fixtures for automatic cleanup:

```javascript
beforeEach(async () => { await cleanupTestData(); await setupTestData(); });
afterEach(async () => { await cleanupTestData(); });
```

> **Full templates**: See [references/test-templates.md](references/test-templates.md#test-data-cleanup-fixture) and [references/data-persistence.md](references/data-persistence.md#test-data-factory)

---

## 13. Regression Testing Strategy

| Level | Trigger | Coverage |
|-----------|---------|----------|
| Smoke Tests | Every commit | Login, main page, critical CRUD |
| Module Tests | Every PR | All pages in modified module |
| Full Regression | Before merge | All tests |

---

## 14. Data Persistence Troubleshooting

**Core Principle**: When data is lost/overwritten/wrong, systematically check ALL data write/delete paths, not just recently modified code.

| Type | Symptom | Check First |
|------|---------|-------------|
| Data Lost | Missing after restart | `sql.init.mode`, initialization scripts |
| Data Overwritten | Becomes default after restart | Data initialization logic |
| Data Duplicated | Two identical records | Unique constraints, idempotency |

**Configuration Safety**:
```yaml
# DANGEROUS — resets database on every startup
spring:
  sql:
    init:
      mode: always  # WRONG!

# SAFE — only application manages data
spring:
  sql:
    init:
      mode: never   # CORRECT!
```

> **Full verification template and investigation order**: See [references/data-persistence.md](references/data-persistence.md)

---

## Placeholder Component Problem Pattern

**Problem**: A component file contains only a placeholder ("Coming soon" / "Under development") instead of actual implementation. When routing points to this component, the page appears blank or shows a stub, causing navigation to freeze.

**Symptom**: Click menu → URL changes → Page shows placeholder text or blank → Subsequent menu clicks do NOT change content (navigation freezes).

**Detection**: Check for files containing `Coming soon`, `Under development`, `建设中`, `开发中` in Vue component files.

> **Full detection script**: See [references/test-templates.md](references/test-templates.md#placeholder-component-detection)

**Prevention Checklist**:
- [ ] Check if multiple versions exist for the same route
- [ ] Verify router points to the correct file
- [ ] Confirm target file has actual implementation
- [ ] Test navigation TO this page and FROM this page

---

## Field Mapping Error Patterns (Critical)

**Root Cause**: Uncaught exceptions in template expressions crash the component instance, causing state pollution that breaks ALL subsequent navigation.

| Error | Cause | Fix |
|-------|-------|-----|
| `null.split is not a function` | `field.split()` when field is null | `(field \|\| '').split()` |
| `undefined.charCodeAt(0)` | `prop.charCodeAt(0)` when prop is null | `if (!prop) return 'default'` |
| `NaN` in display | Numeric field undefined | `field \|\| 0` |
| Comparison never matches | API returns number, comparison uses string | Use strict type comparison |

**Prevention**:
- All template expressions handle null/undefined
- Numeric comparisons use correct types
- Functions accept null parameters
- Numeric fields have defaults

---

## Best Practices Summary

1. **Always refresh page** after create/update to verify persistence
2. **Always check actual UI content**, not just API response
3. **Always take screenshots** for key steps
4. **Always verify error handling** — test both success and failure paths
5. **Wait for networkidle** before taking actions
6. **Verify complete data flow** from user action to visible result
7. **Test navigation AFTER visiting problematic pages** — detect state pollution
8. **Analyze every error** — don't just mark FAIL
9. **Defensive null checking** in all template expressions
10. **Test complete modules**, not just reported pages

---

## Example Files

Reference implementations in the `examples/` directory:
- [complete_flow_test.py](examples/complete_flow_test.py) — Full CRUD with data verification
- [visual_verification.py](examples/visual_verification.py) — Page content verification patterns

See also:
- [references/test-templates.md](references/test-templates.md) — Code templates for navigation, module, and CRUD testing
- [references/data-persistence.md](references/data-persistence.md) — Data persistence verification
