# Data Persistence Verification Reference

> This file contains detailed code templates and troubleshooting patterns referenced by SKILL.md.

## Data Persistence Verification Template

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

    // 3. Verify immediately after creation
    const verify1 = await fetch(`${API_BASE_URL}/{module}/{entity}/${dataId}`);
    expect(verify1.status).toBe(200);

    // 4. Restart backend (the critical test)
    await restartBackend();

    // 5. Verify data still exists after restart
    const verify2 = await fetch(`${API_BASE_URL}/{module}/{entity}/${dataId}`);
    expect(verify2.status).toBe(200), "Data lost after restart!";

    // 6. Verify via browser
    await page.goto(`${BASE_URL}/{module}/{entity}-list`);
    await page.waitForLoadState('networkidle');
    expect((await page.locator('body').innerText()).includes(testData.name)).toBe(true);
}
```

## Test Data Factory

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

## Data Issue Investigation Order

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
