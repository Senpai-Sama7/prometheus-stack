#!/bin/bash
set -e

echo "========================================"
echo "PROMETHEUS Bootstrap"
echo "========================================"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "[*] Python version: $PYTHON_VERSION"

if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    echo "[!] ERROR: Python 3.10+ required. Found: $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv venv
    echo "[+] Virtual environment created"
fi

# Activate virtual environment
echo "[*] Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "[*] Upgrading pip..."
pip install -q --upgrade pip

# Install dependencies
echo "[*] Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
    echo "[+] Dependencies installed"
else
    echo "[!] WARNING: requirements.txt not found"
fi

# Create audit log directory
echo "[*] Creating audit log directory..."
mkdir -p audit_logs
echo "[+] Audit log directory created"

# Create src directory structure if not exists
echo "[*] Creating source directory structure..."
mkdir -p src/{gates,uncertainty,mcp,orchestrator}
echo "[+] Source directories created"

echo ""
echo "========================================"
echo "Bootstrap Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Review docs/BUILD_SPEC.md for 16-week plan"
echo "  2. Run tests: bash scripts/run_tests.sh"
echo "  3. See docs/ folder for contract specs"
echo ""
echo "Venv activated. To deactivate: deactivate"
echo ""
