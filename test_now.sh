#!/bin/bash
clear
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║          LEOCODE + 9ROUTER - FINAL VERIFICATION              ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Running final checks..."
echo ""

cd /run/media/leonova/Leonova/Tafrih/ChatBot

# Check 1: Config
echo "1. Checking configuration..."
if [ -f ~/.config/leocode/config.json ]; then
    MODEL=$(grep -o '"model": "[^"]*"' ~/.config/leocode/config.json | cut -d'"' -f4)
    echo "   ✓ Config exists: $MODEL"
else
    echo "   ✗ Config missing"
    exit 1
fi

# Check 2: Code fix
echo "2. Checking bug fix..."
if grep -q "stream = await self.client.client.chat.completions.create" leocode/app.py; then
    echo "   ✓ Bug fix applied"
else
    echo "   ✗ Bug fix missing"
    exit 1
fi

# Check 3: Quick agent test
echo "3. Testing agent response..."
python3 - <<'PYTEST'
import asyncio, sys
sys.path.insert(0, '/run/media/leonova/Leonova/Tafrih/ChatBot')
from leocode.config import Config
from leocode.client import RouterClient
async def test():
    config = Config.load()
    client = RouterClient(config)
    response = await client.chat_sync([{"role":"user","content":"Hi"}], model=config.model)
    return len(response.strip()) > 0
result = asyncio.run(test())
sys.exit(0 if result else 1)
PYTEST

if [ $? -eq 0 ]; then
    echo "   ✓ Agent responds correctly"
else
    echo "   ✗ Agent test failed"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ ALL CHECKS PASSED!"
echo ""
echo "Your Leocode agent is ready to use."
echo ""
echo "To start:"
echo "  $ leocode"
echo ""
echo "Then try:"
echo "  • Hi"
echo "  • Create a Python script to parse JSON"
echo "  • What files are in /tmp?"
echo ""
echo "Press ctrl+x in the app to browse 224+ models!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
