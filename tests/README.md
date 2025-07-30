# Integration Tests

This directory contains integration tests for the AI Virtual Agent application.

## Quick Start

### 1. Start Services Manually

First, start all required services:
Follow the steps in [Conribution](../CONTRIBUTING.md)

Make sure that the only model served is `llama3.2:3b-instruct-fp16`

### 2. Run Tests

Once services are running:

```bash
# Run all integration tests
./run_tests.sh

# Run specific test file
./run_tests.sh tests/integration/test_chat_pipeline.tavern.yaml

# Run specific Tavern test file
./run_tests.sh tests/integration/test_chat_pipeline.tavern.yaml

# Run with custom configuration
TEST_FRONTEND_URL="http://localhost:3000" ./run_tests.sh
```

## Test Configuration

### Environment Variables

Configure test URLs using environment variables:

```bash
# Development (default)
export TEST_FRONTEND_URL="http://localhost:5173"
export TEST_BACKEND_URL="http://localhost:8000"
export TEST_LLAMASTACK_URL="http://localhost:8321"

# Custom configuration
export TEST_FRONTEND_URL="http://localhost:3000"
export TEST_BACKEND_URL="http://localhost:8080"
export TEST_LLAMASTACK_URL="http://localhost:8888"
```

### Podman/Container Setup

For containerized environments:

```bash
export TEST_FRONTEND_URL="http://frontend:5173"
export TEST_BACKEND_URL="http://backend:8000"
export TEST_LLAMASTACK_URL="http://llamastack:8321"
```

## Running Tests

### All Tests

```bash
# Run all integration tests
./run_tests.sh

# Run all tests with custom configuration
TEST_FRONTEND_URL="http://localhost:3000" ./run_tests.sh
```

### Specific Tests

```bash
# Run specific test file
./run_tests.sh tests/integration/test_chat_pipeline.tavern.yaml

# Run with pattern
./run_tests.sh tests/integration/test_specific_*

# Run with pytest options
./run_tests.sh \"tests/integration/test_endpoints.tavern.yaml::Test Models API Endpoint\"
```

## Service Management

### Manual Service Management

The test runner requires all services to be running before executing tests:

- **Backend**: `http://localhost:8000` (or `$TEST_BACKEND_URL`)
- **Frontend**: `http://localhost:5173` (or `$TEST_FRONTEND_URL`)
- **LlamaStack**: `http://localhost:8321` (or `$TEST_LLAMASTACK_URL`)

### Service Verification

The script checks if services are running and provides helpful instructions if they're not:

```bash
🔍 Checking if services are running...
✅ Backend is running at http://localhost:8000
✅ Frontend is running at http://localhost:5173
✅ LlamaStack is running at http://localhost:8321
```

If any service is not running, the script will exit with clear instructions on how to start them.

## Test Structure

### Test Files

**Tavern Tests (YAML-based):**
- `test_chat_pipeline.tavern.yaml` - End-to-end chat functionality with response validation
- `test_models_api.tavern.yaml` - API endpoint testing with structured validation
- `test_llama_stack_api.tavern.yaml` - LlamaStack service integration tests

**Shared Resources:**
- `validators.py` - Custom validation functions for both Python and Tavern tests

## Dependencies

Test dependencies are managed in `requirements-test.txt`:

```
pytest>=7.0.0
requests>=2.25.0
```

## CI/CD Integration

The test runner is designed to work in CI/CD environments where services are pre-started:

```bash
# GitLab CI example
before_script:
  - ./scripts/dev/run_local.sh &
  - sleep 30  # Wait for services to start
script:
  - ./run_tests.sh

# GitHub Actions example
- name: Start Services
  run: ./scripts/dev/run_local.sh &
- name: Wait for Services
  run: sleep 30
- name: Run Integration Tests
  run: ./run_tests.sh
```

For more detailed configuration options, see [Config](CONFIG.md).
