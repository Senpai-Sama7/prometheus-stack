#!/bin/bash
set -e

echo "========================================"
echo "PROMETHEUS Test Suite"
echo "========================================"
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "[!] Virtual environment not activated"
    echo "[*] Activating virtual environment..."
    source venv/bin/activate || {
        echo "[!] Failed to activate venv. Run: bash scripts/bootstrap.sh"
        exit 1
    }
fi

echo "[*] Python: $(python --version)"
echo "[*] Pytest: $(pytest --version)"
echo ""

# Run unit tests
echo "========================================"
echo "Running Unit Tests"
echo "========================================"
echo ""

if [ -d "tests" ]; then
    pytest tests/ -v --tb=short -x || {
        echo ""
        echo "[!] Unit tests failed"
        exit 1
    }
    echo ""
    echo "[+] Unit tests passed"
else
    echo "[!] tests/ directory not found"
fi

echo ""

# Run acceptance tests
echo "========================================"
echo "Running Acceptance Tests"
echo "========================================"
echo ""

if [ -d "tests/acceptance" ]; then
    pytest tests/acceptance/ -v --tb=short -x || {
        echo ""
        echo "[!] Acceptance tests failed"
        exit 1
    }
    echo ""
    echo "[+] Acceptance tests passed"
else
    echo "[!] tests/acceptance/ directory not found. Skipping."
fi

echo ""
echo "========================================"
echo "All Tests Passed!"
echo "========================================"
echo ""
echo "Summary:"
echo "  [+] Unit tests: PASS"
echo "  [+] Acceptance tests: PASS"
echo ""
