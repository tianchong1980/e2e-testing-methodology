# E2E Testing Methodology

Comprehensive end-to-end testing methodology for web applications.

## Overview

This skill provides a complete testing methodology for testing web applications end-to-end. It covers complete data flow testing, visual verification, navigation bug detection, and data persistence verification.

## Features

- **Complete Data Flow Testing**: Verify the entire chain from user action to visible result
- **Visual Verification**: Ensure page content actually changes, not just URL
- **Navigation Bug Detection**: Detect state pollution that breaks subsequent navigation
- **Field Mapping Error Detection**: Identify template errors that crash components
- **Module-Level Complete Testing**: Test ALL pages in a module, not just the reported one
- **Boundary Testing**: Pagination, string length, number range, required fields
- **Error Handling Patterns**: Validation, 404, 401, 403, 500, timeout scenarios
- **Data Persistence Verification**: Ensure data survives application restart

## Usage

When testing web applications end-to-end, use this skill to:
- Verify UI behavior and data flow
- Test CRUD operations with persistence
- Debug navigation and display issues
- Perform regression testing

## Structure

```
e2e-testing-methodology/
├── SKILL.md                      # Main skill definition
├── .claude-plugin/
│   ├── plugin.json              # Skill metadata
│   └── marketplace.json          # Marketplace entry
├── references/
│   ├── test-templates.md        # Code templates for testing patterns
│   └── data-persistence.md      # Data persistence verification
├── examples/
│   ├── complete_flow_test.py     # Full CRUD with data verification
│   └── visual_verification.py    # Page content verification patterns
└── README.md
```

## Installation

```bash
npx skills add tianchong1980/e2e-testing-methodology
```

Or install via [skills.sh](https://skills.sh).

## Requirements

- Playwright for browser automation
- Python 3.7+ or Node.js for test scripts
- A running web application to test

## License

MIT