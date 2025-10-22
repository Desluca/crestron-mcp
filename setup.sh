#!/bin/bash
# Crestron MCP Server - Quick Setup Script

set -e

echo "=========================================="
echo "Crestron MCP Server - Quick Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
python_major=$(echo $python_version | cut -d. -f1)
python_minor=$(echo $python_version | cut -d. -f2)

if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 10 ]); then
    echo "❌ Error: Python 3.10 or higher is required"
    echo "   Current version: $python_version"
    exit 1
fi
echo "✅ Python $python_version detected"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found"
    echo "   Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your Crestron credentials"
    echo "   1. Set CRESTRON_HOST to your Crestron Home IP"
    echo "   2. Set CRESTRON_AUTH_TOKEN from Crestron Home app"
    echo ""
else
    echo "✅ .env file exists"
    echo ""
fi

# Validate Python syntax
echo "Validating Python syntax..."
python -m py_compile crestron_mcp.py
echo "✅ Syntax validation passed"
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo ""
echo "1. Configure Credentials:"
echo "   Edit .env file with your Crestron Home credentials"
echo ""
echo "2. Get Auth Token:"
echo "   Crestron Home App → Installer Settings →"
echo "   System Control Options → Web API Settings → Update Token"
echo ""
echo "3. Test the Server:"
echo "   python crestron_mcp.py --help"
echo ""
echo "4. Integration:"
echo "   See README.md for Claude Desktop integration"
echo ""
echo "For full documentation, see README.md"
echo ""
