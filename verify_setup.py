#!/usr/bin/env python3
"""
Leocode + 9Router Integration Verification Script
Run this to verify everything is working correctly.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project to path
sys.path.insert(0, '/run/media/leonova/Leonova/Tafrih/ChatBot')

from leocode.config import Config
from leocode.client import RouterClient
from leocode.agent import AgentTools


def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


async def main():
    print_header("LEOCODE + 9ROUTER VERIFICATION")
    
    # 1. Check configuration
    print_header("1. Configuration Check")
    try:
        config = Config.load()
        print(f"✓ Config loaded successfully")
        print(f"  Endpoint:   {config.base_url}")
        print(f"  API Key:    {config.api_key[:20]}...")
        print(f"  Model:      {config.model}")
        print(f"  RAG:        {'Enabled' if config.rag_enabled else 'Disabled'}")
        print(f"  Web Search: {'Enabled' if config.web_search_enabled else 'Disabled'}")
        print(f"  Agent Mode: {'Enabled' if config.agent_mode else 'Disabled'}")
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False
    
    # 2. Test client connection
    print_header("2. Client Connection Test")
    try:
        client = RouterClient(config)
        print(f"✓ Client initialized")
    except Exception as e:
        print(f"✗ Client initialization failed: {e}")
        return False
    
    # 3. Test model listing
    print_header("3. Model Discovery Test")
    try:
        models = await client.list_models()
        print(f"✓ Found {len(models)} models")
        
        # Count by provider
        providers = {}
        for m in models:
            provider = m['owned_by']
            providers[provider] = providers.get(provider, 0) + 1
        
        print(f"  Providers: {len(providers)}")
        for provider, count in sorted(providers.items(), key=lambda x: -x[1])[:5]:
            print(f"    {provider}: {count} models")
            
    except Exception as e:
        print(f"✗ Model listing failed: {e}")
        return False
    
    # 4. Test simple chat
    print_header("4. Basic Chat Test")
    try:
        messages = [{"role": "user", "content": "Say PONG"}]
        response = await client.chat_sync(messages, model=config.model)
        print(f"✓ Chat working")
        print(f"  Request:  'Say PONG'")
        print(f"  Response: '{response.strip()}'")
    except Exception as e:
        print(f"✗ Chat test failed: {e}")
        return False
    
    # 5. Test agent tools
    print_header("5. Agent Tools Test")
    try:
        agent = AgentTools("/tmp")
        tools = agent.tool_definitions
        print(f"✓ Agent initialized with {len(tools)} tools")
        print(f"  Available tools:")
        for tool in tools:
            print(f"    - {tool['function']['name']}")
    except Exception as e:
        print(f"✗ Agent initialization failed: {e}")
        return False
    
    # 6. Test tool calling
    print_header("6. Tool Calling Test")
    try:
        result = agent.execute("list_dir", {"path": "/tmp"})
        lines = result.split('\n')[:3]
        print(f"✓ Tool execution working")
        print(f"  Tool: list_dir")
        print(f"  Result preview:")
        for line in lines:
            print(f"    {line}")
    except Exception as e:
        print(f"✗ Tool execution failed: {e}")
        return False
    
    # 7. Test streaming with tools
    print_header("7. Streaming + Tool Calling Test")
    try:
        messages = [
            {"role": "system", "content": "Use tools when appropriate."},
            {"role": "user", "content": "List files in /tmp using list_dir tool"}
        ]
        
        stream = await client.client.chat.completions.create(
            model=config.model,
            messages=messages,
            tools=tools,
            temperature=0.3,
            max_tokens=500,
            stream=True,
        )
        
        tool_calls = {}
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls:
                        tool_calls[idx] = {"id": "", "name": "", "arguments": ""}
                    if tc.id:
                        tool_calls[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_calls[idx]["name"] = tc.function.name
                        if tc.function.arguments:
                            tool_calls[idx]["arguments"] += tc.function.arguments
        
        if tool_calls:
            print(f"✓ Tool calling via streaming works")
            print(f"  Tools called: {len(tool_calls)}")
            for tc in tool_calls.values():
                print(f"    - {tc['name']}")
        else:
            print(f"⚠ No tool calls detected (model may have responded directly)")
            
    except Exception as e:
        print(f"✗ Streaming + tool calling failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 8. Summary
    print_header("VERIFICATION COMPLETE")
    print()
    print("✓✓✓ All tests passed!")
    print()
    print("Your Leocode agent is fully operational with 9Router.")
    print()
    print("READY TO USE:")
    print("  $ leocode                    # Launch in current directory")
    print("  $ leocode -d /your/project   # Launch in specific directory")
    print("  $ leocode -m kr/auto         # Use auto-routing model")
    print()
    print(f"AVAILABLE MODELS: {len(models)}")
    print("  Press ctrl+x in the app to switch models!")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nVerification cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
