#!/bin/bash
# Schnitzel Framework - Development Environment Setup
# Module: module_00_foundation (CLI Foundation)

set -e  # Exit on error

echo "========================================"
echo "Schnitzel Framework - Environment Setup"
echo "Module: Foundation (MVP)"
echo "========================================"
echo ""

# Check Python version
echo "[1/8] Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3.11+ is required but not found."
    echo "Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

if (( $(echo "$PYTHON_VERSION < $REQUIRED_VERSION" | bc -l) )); then
    echo "ERROR: Python $PYTHON_VERSION found, but Python $REQUIRED_VERSION+ is required."
    exit 1
fi

echo "   Found Python $PYTHON_VERSION ✓"
echo ""

# Check UV package manager
echo "[2/8] Checking UV package manager..."
if ! command -v uv &> /dev/null; then
    echo "   UV not found. Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
else
    echo "   Found UV $(uv --version) ✓"
fi
echo ""

# Check Flutter
echo "[3/8] Checking Flutter SDK..."
if ! command -v flutter &> /dev/null; then
    echo "WARNING: Flutter SDK not found."
    echo "Flutter is required for full project generation."
    echo "Install from: https://flutter.dev/docs/get-started/install"
    echo "Continuing without Flutter..."
else
    FLUTTER_VERSION=$(flutter --version | head -n1 | cut -d' ' -f2)
    echo "   Found Flutter $FLUTTER_VERSION ✓"
fi
echo ""

# Check Docker
echo "[4/8] Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "WARNING: Docker not found."
    echo "Docker is required for infrastructure generation."
    echo "Install from: https://docs.docker.com/get-docker/"
    echo "Continuing without Docker..."
else
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    echo "   Found Docker $DOCKER_VERSION ✓"
fi
echo ""

# Create virtual environment for CLI development
echo "[5/8] Setting up Python virtual environment..."
if [ ! -d "schnitzel-cli/.venv" ]; then
    cd schnitzel-cli
    uv venv
    cd ..
    echo "   Virtual environment created ✓"
else
    echo "   Virtual environment already exists ✓"
fi
echo ""

# Install CLI dependencies
echo "[6/8] Installing Schnitzel CLI dependencies..."
cd schnitzel-cli
uv pip install -e ".[dev]"
cd ..
echo "   Dependencies installed ✓"
echo ""

# Install development tools
echo "[7/8] Installing development tools..."
uv pip install --system ruff pyright pytest pytest-cov
echo "   Development tools installed ✓"
echo ""

# Verify installation
echo "[8/8] Verifying installation..."
if command -v schnitzel &> /dev/null; then
    echo "   Schnitzel CLI installed successfully ✓"
    schnitzel --version
else
    echo "WARNING: 'schnitzel' command not found in PATH."
    echo "You may need to activate the virtual environment:"
    echo "   source schnitzel-cli/.venv/bin/activate"
fi
echo ""

echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next Steps:"
echo "1. Activate virtual environment:"
echo "      source schnitzel-cli/.venv/bin/activate"
echo ""
echo "2. Run tests:"
echo "      pytest schnitzel-cli/tests/"
echo ""
echo "3. Create a test project:"
echo "      schnitzel init test-project --template minimal"
echo ""
echo "4. Generate code:"
echo "      cd test-project && schnitzel generate"
echo ""
echo "Documentation: https://github.com/moinsen/schnitzel"
echo "========================================"
