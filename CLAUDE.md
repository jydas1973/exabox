# Exabox Code Generation Guide

## Project Overview
Exabox is a Python-based agent framework for Oracle ExaCloud infrastructure management. It handles HTTP/HTTPS requests, job scheduling, database operations, key management, and OCI integration.

## Code Structure & Organization

### Directory Layout
- **agent/** - Core agent functionality (Client, Worker, Dispatcher, Scheduler)
- **BaseServer/** - HTTP/HTTPS server infrastructure
- **core/** - Core utilities (Context, Error, DBStore, Threads)
- **config/** - Configuration management
- **exakms/** - Key management system
- **exaoci/** - OCI connectors and integrations
- **exatest/** - Unit tests mirroring main code structure
- **utils/** - Common utilities and helper functions
- **bin/** - Entry point scripts
- **log/** - Logging management

### File Naming Conventions
- Class files: Capitalized names (e.g., `Agent.py`, `Client.py`, `BaseServer.py`)
- Test files: Prefix with `tests_` (e.g., `tests_client.py`, `tests_agent_classes.py`)
- Utilities: Lowercase with underscores (e.g., `common.py`, `oci_region.py`)

## Coding Standards

### File Headers
Every file MUST include:
```python
"""
Copyright (c) YEAR, YEAR, Oracle and/or its affiliates.

NAME:
    FileName - Brief description

FUNCTION:
    Detailed description of functionality

NOTE:
    Additional notes or caveats

History:
    author    MM/DD/YY - Brief description of change
"""
```

### Naming Conventions
- **Classes**: Use `eb` or `exa` prefix (e.g., `ebJobResponse`, `exaBoxNode`, `ExaHTTPSServer`)
- **Methods**: Prefix with `m` (e.g., `mGetConfig()`, `mSetData()`, `mProcessRequest()`)
- **Private attributes**: Use double underscore prefix (e.g., `self.__config`, `self.__log`)
- **Constants**: Use UPPER_CASE (e.g., `SAMPLE_BODY`, `GlobalContext`)

### Code Organization
- Keep related functionality together in logical modules
- Use clear separation between public and private methods
- Implement getter/setter patterns for class attributes
- Follow single responsibility principle for classes and methods

### Import Standards
```python
# Standard library imports first
import os
import sys
import json

# Third-party imports second
from six.moves import urllib
import argparse

# Local imports last
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogInfo
from exabox.agent.Client import ebExaClient
```

### Error Handling
- Use custom error codes defined in `core/Error.py`
- Always provide meaningful error messages
- Log errors appropriately before raising exceptions
- Handle exceptions at appropriate abstraction levels

### Logging
- Use the logging framework from `log/LogMgr` module
- Available log functions: `ebLogInfo`, `ebLogError`, `ebLogDebug`, `ebLogWarn`
- Include context in log messages for debugging
- Log at appropriate levels (INFO, ERROR, DEBUG, WARN)

### Documentation
- Add docstrings for all public classes and methods
- Document parameters, return values, and exceptions
- Include usage examples for complex functionality
- Keep comments concise and meaningful

## Testing Requirements

### Test File Organization
- All unit tests go in the `exatest/` folder
- Mirror the source code directory structure
- Test file naming: `tests_<module_name>.py`
- Example: For `agent/Client.py`, create `exatest/agent/tests_client.py`

### Test Framework
Use Python's **unittest** framework (NOT pytest):
```python
#!/usr/bin/env python
# Copyright header...

import unittest
from unittest.mock import patch, MagicMock, mock_open

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.<module>.<class> import <ClassName>

class Test<ClassName>(unittest.TestCase):

    def setUp(self):
        # Setup test fixtures
        pass

    def tearDown(self):
        # Cleanup after tests
        pass

    def test_<functionality>_success(self):
        # Test expected behavior
        pass

    def test_<functionality>_edge_case(self):
        # Test edge cases
        pass

    def test_<functionality>_error(self):
        # Test error conditions
        pass

if __name__ == '__main__':
    unittest.main()
```

### Test Coverage Requirements
For each new functionality, provide:
1. **Happy path test** - Expected behavior with valid inputs
2. **Edge case tests** - Boundary conditions, empty values, null checks
3. **Error case tests** - Invalid inputs, exception handling
4. **Mock external dependencies** - Database calls, HTTP requests, file I/O

### Running Tests

**Run all tests:**
```bash
cd exatest
python exatest.py -run -all
```

**Run specific test file:**
```bash
cd exatest
python exatest.py -run tests_<module_name>
```

**Run tests with coverage:**
```bash
cd exatest
python exatest.py -run -all --coverage
```

**Run tests for specific component:**
```bash
cd exatest
python exatest.py -run -all agent        # Run all agent tests
python exatest.py -run -all core         # Run all core tests
```

**Shell-based test execution:**
```bash
cd exatest
./exatest.sh -run -all                   # Run all tests
./exatest.sh -run tests_client           # Run specific test
```

### Test Validation
- All tests must pass before committing code
- Verify no regression in existing tests
- Check coverage reports in `exatest/htmlcov/` directory
- Review .suc and .dif files for test results

## Best Practices

### Code Quality
- **No hardcoded values** - Use configuration files or constants
- **Validate inputs** - Check parameters before processing
- **Handle edge cases** - Null values, empty lists, missing keys
- **Use type hints** - Improve code readability (where applicable)
- **Avoid code duplication** - Extract common logic into helper methods

### Security
- Never log sensitive data (passwords, keys, tokens)
- Use secure communication (HTTPS, encrypted connections)
- Validate and sanitize all external inputs
- Follow principle of least privilege

### Performance
- Avoid unnecessary database queries
- Use connection pooling for database and HTTP clients
- Implement proper locking for shared resources
- Clean up resources in finally blocks

### Common Patterns

**Configuration Management:**
```python
from exabox.core.Context import get_gcontext
context = get_gcontext()
config_value = context.mGetConfig().mGetConfigValue("key")
```

**Database Operations:**
```python
from exabox.agent.DBService import ebDBService
db = ebDBService()
result = db.mExecuteQuery(query, params)
```

**Logging Pattern:**
```python
from exabox.log.LogMgr import ebLogInfo, ebLogError
ebLogInfo("Processing request: {0}".format(request_id))
ebLogError("Failed to process: {0}".format(error_msg))
```

**Error Handling:**
```python
from exabox.core.Error import ebError, ebErrorCodes
try:
    # operation
except Exception as e:
    ebLogError("Operation failed: {0}".format(str(e)))
    raise ebError(ebErrorCodes.GENERAL_ERROR, str(e))
```

## Module-Specific Guidelines

### Agent Components
- Use Worker/Dispatcher pattern for job processing
- Implement proper signal handling for graceful shutdown
- Follow job lifecycle: Create → Queue → Execute → Complete
- Store job state in database for recovery

### Server Components
- Inherit from `BaseServer` for consistency
- Implement proper SSL/TLS certificate handling
- Use BaseHandler for request processing
- Configure via BaseConfig

### Database Components
- Use DBStore3 for MySQL operations
- Implement proper connection management
- Use parameterized queries to prevent SQL injection
- Handle database locking with ExaLock

### Infrapatching Module
- **Follow handler hierarchy**: Inherit from `targetHandler`, `taskHandler`, or `pluginHandler` base classes based on functionality
- **Use centralized constants**: Import all constants from `infrapatching/utils/constants.py` (e.g., `PATCH_DOM0`, `PATCH_CELL`, `KEY_NAME_*`)
- **Error handling**: Use error codes from `infrapatching/core/infrapatcherror.py` with proper error actions (PAGE_ONCALL, FAIL_DONTSHOW_PAGE_ONCALL)
- **String formatting**: Always use f-strings for string interpolation (e.g., `f"Error: {error_msg}"`) not `.format()` or `%` formatting
- **Parameter passing**: Pass operation parameters as dictionaries; use factory pattern `getTaskHandlerInstance(operation, params_dict)`
- **Mock support**: Implement corresponding mock handlers in `handlers/mockTargetHandler` or `handlers/mockTaskHandler` for testing
- **Utility functions**: Reuse common methods from `infrapatching/utils/utility.py` to avoid code duplication
- **Target-specific logic**: Separate concerns—dom0, domu, cell, and switch handlers must not share implementation code directly
- **Logging**: Use detailed logging with context (operation type, target, request_id) for debugging patching workflows
- **Testing**: Create tests in `exatest/infrapatching/` mirroring handler structure; validate precheck, patch, rollback, and postcheck operations

## Checklist for New Code

Before submitting new code, ensure:
- [ ] File header with copyright and history added
- [ ] Followed naming conventions (eb/exa prefix, m prefix for methods)
- [ ] All public methods have docstrings
- [ ] Error handling implemented with proper logging
- [ ] Unit tests created in exatest/ folder
- [ ] Tests include happy path, edge cases, and error scenarios
- [ ] All tests pass: `python exatest.py -run -all`
- [ ] No hardcoded credentials or sensitive data
- [ ] Code follows existing patterns in the codebase
- [ ] External dependencies properly mocked in tests
