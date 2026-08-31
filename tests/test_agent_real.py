#!/usr/bin/env python3
"""
Real agent testing - tests actual agent responses with command-line interface.
Run tests against real 9Router API and validate responses.
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, List, Any

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from leocode.config import Config
from leocode.client import RouterClient
from leocode.agent import AgentTools


class TestCase:
    """Single test case for agent testing."""
    
    def __init__(
        self,
        name: str,
        input_text: str,
        expected_keywords: List[str] = None,
        use_tools: bool = False,
        validate_func: Optional[callable] = None,
        timeout: int = 30,
    ):
        self.name = name
        self.input_text = input_text
        self.expected_keywords = expected_keywords or []
        self.use_tools = use_tools
        self.validate_func = validate_func
        self.timeout = timeout
        self.result: Optional[str] = None
        self.passed: bool = False
        self.error: Optional[str] = None
        self.duration: float = 0.0


class AgentTester:
    """Real agent testing system."""
    
    def __init__(self, working_dir: str = "/tmp"):
        self.config = Config.load()
        self.client = RouterClient(self.config)
        self.agent = AgentTools(working_dir)
        self.working_dir = working_dir
        self.test_results: List[TestCase] = []
    
    async def run_test_case(self, test: TestCase) -> TestCase:
        """Run a single test case and validate response."""
        import time
        
        print(f"\n{'='*70}")
        print(f"TEST: {test.name}")
        print(f"{'='*70}")
        print(f"INPUT: {test.input_text}")
        print(f"TOOLS: {'Enabled' if test.use_tools else 'Disabled'}")
        print(f"TIMEOUT: {test.timeout}s")
        print("-" * 70)
        
        start_time = time.time()
        
        try:
            # Build messages
            messages = [
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": test.input_text}
            ]
            
            tools = self.agent.tool_definitions if test.use_tools else None
            
            # Get response from agent
            print("REQUESTING...")
            
            if tools:
                # With tools - handle tool calling
                response_parts = []
                
                stream = await self.client.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    tools=tools,
                    temperature=0.3,
                    max_tokens=2000,
                    stream=True,
                )
                
                tool_calls = {}
                async for chunk in stream:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if not delta:
                        continue
                    
                    if delta.content:
                        response_parts.append(delta.content)
                        print(delta.content, end="", flush=True)
                    
                    if delta.tool_calls:
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
                
                # Execute tool calls
                if tool_calls:
                    print("\n" + "=" * 70)
                    print("TOOL CALLS DETECTED")
                    print("=" * 70)
                    
                    for idx in sorted(tool_calls.keys()):
                        tc = tool_calls[idx]
                        name = tc["name"]
                        try:
                            args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                        except json.JSONDecodeError:
                            args = {}
                        
                        print(f"\nTOOL: {name}")
                        print(f"ARGS: {json.dumps(args, indent=2)}")
                        
                        result = self.agent.execute(name, args)
                        print(f"RESULT: {result[:500]}{'...' if len(result) > 500 else ''}")
                        
                        response_parts.append(f"\n[TOOL: {name}]\n{result}")
                        
                        # Add tool call to messages
                        messages.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": tc["id"],
                                "type": "function",
                                "function": {"name": name, "arguments": tc["arguments"]},
                            }],
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": result[:5000],
                        })
                    
                    # Get follow-up response - may contain more tool calls
                    print("\n" + "=" * 70)
                    print("FOLLOW-UP RESPONSE")
                    print("=" * 70)
                    
                    # Allow up to 3 rounds of tool calling
                    for round_num in range(3):
                        tool_calls_round = {}
                        
                        stream2 = await self.client.client.chat.completions.create(
                            model=self.config.model,
                            messages=messages,
                            tools=tools,
                            temperature=0.3,
                            max_tokens=1000,
                            stream=True,
                        )
                        
                        follow_up_content = []
                        async for chunk in stream2:
                            delta = chunk.choices[0].delta if chunk.choices else None
                            if not delta:
                                continue
                            
                            if delta.content:
                                follow_up_content.append(delta.content)
                                response_parts.append(delta.content)
                                print(delta.content, end="", flush=True)
                            
                            if delta.tool_calls:
                                for tc in delta.tool_calls:
                                    idx = tc.index
                                    if idx not in tool_calls_round:
                                        tool_calls_round[idx] = {"id": "", "name": "", "arguments": ""}
                                    if tc.id:
                                        tool_calls_round[idx]["id"] = tc.id
                                    if tc.function:
                                        if tc.function.name:
                                            tool_calls_round[idx]["name"] = tc.function.name
                                        if tc.function.arguments:
                                            tool_calls_round[idx]["arguments"] += tc.function.arguments
                        
                        print()
                        
                        # If no more tool calls, we're done
                        if not tool_calls_round:
                            break
                        
                        # Execute additional tool calls
                        print("\n" + "=" * 70)
                        print(f"ADDITIONAL TOOL CALLS (Round {round_num + 1})")
                        print("=" * 70)
                        
                        for idx in sorted(tool_calls_round.keys()):
                            tc = tool_calls_round[idx]
                            name = tc["name"]
                            try:
                                args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                            except json.JSONDecodeError:
                                args = {}
                            
                            print(f"\nTOOL: {name}")
                            print(f"ARGS: {json.dumps(args, indent=2)}")
                            
                            result = self.agent.execute(name, args)
                            print(f"RESULT: {result[:500]}{'...' if len(result) > 500 else ''}")
                            
                            response_parts.append(f"\n[TOOL: {name}]\n{result}")
                            
                            # Add tool call to messages
                            messages.append({
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [{
                                    "id": tc["id"],
                                    "type": "function",
                                    "function": {"name": name, "arguments": tc["arguments"]},
                                }],
                            })
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc["id"],
                                "content": result[:5000],
                            })
                
                test.result = "".join(response_parts)
            else:
                # Without tools - simple chat
                response = await self.client.chat_sync(messages, model=self.config.model)
                test.result = response
                print(response)
            
            test.duration = time.time() - start_time
            
            # Validate response
            print("\n" + "=" * 70)
            print("VALIDATION")
            print("=" * 70)
            
            if test.validate_func:
                # Custom validation
                test.passed = test.validate_func(test.result)
                print(f"Custom validation: {'PASS' if test.passed else 'FAIL'}")
            else:
                # Keyword validation
                if test.expected_keywords:
                    found_keywords = []
                    missing_keywords = []
                    
                    for keyword in test.expected_keywords:
                        if keyword.lower() in test.result.lower():
                            found_keywords.append(keyword)
                        else:
                            missing_keywords.append(keyword)
                    
                    test.passed = len(missing_keywords) == 0
                    
                    print(f"Expected keywords: {test.expected_keywords}")
                    print(f"Found: {found_keywords}")
                    if missing_keywords:
                        print(f"Missing: {missing_keywords}")
                else:
                    # Just check if response is non-empty
                    test.passed = len(test.result.strip()) > 0
                    print(f"Response length: {len(test.result)} chars")
            
            print(f"Duration: {test.duration:.2f}s")
            print(f"Result: {'✓ PASS' if test.passed else '✗ FAIL'}")
            
        except asyncio.TimeoutError:
            test.error = f"Timeout after {test.timeout}s"
            test.passed = False
            print(f"✗ TIMEOUT: {test.error}")
        except Exception as e:
            test.error = str(e)
            test.passed = False
            print(f"✗ ERROR: {test.error}")
            import traceback
            traceback.print_exc()
        
        return test
    
    async def run_test_suite(self, tests: List[TestCase]) -> Dict[str, Any]:
        """Run all tests and return summary."""
        print("\n" + "╔" + "═" * 68 + "╗")
        print("║" + " " * 20 + "LEOCODE AGENT TEST SUITE" + " " * 24 + "║")
        print("╚" + "═" * 68 + "╝")
        
        print(f"\nConfiguration:")
        print(f"  Endpoint: {self.config.base_url}")
        print(f"  Model: {self.config.model}")
        print(f"  Working Dir: {self.working_dir}")
        print(f"  Total Tests: {len(tests)}")
        
        results = []
        for i, test in enumerate(tests, 1):
            print(f"\n[Test {i}/{len(tests)}]")
            result = await self.run_test_case(test)
            results.append(result)
            self.test_results.append(result)
        
        # Summary
        passed = sum(1 for t in results if t.passed)
        failed = sum(1 for t in results if not t.passed)
        total_duration = sum(t.duration for t in results)
        
        print("\n" + "╔" + "═" * 68 + "╗")
        print("║" + " " * 26 + "TEST SUMMARY" + " " * 30 + "║")
        print("╚" + "═" * 68 + "╝")
        
        print(f"\nTotal: {len(results)}")
        print(f"Passed: {passed} ✓")
        print(f"Failed: {failed} ✗")
        print(f"Success Rate: {(passed/len(results)*100) if results else 0:.1f}%")
        print(f"Total Duration: {total_duration:.2f}s")
        print(f"Average Duration: {(total_duration/len(results)) if results else 0:.2f}s")
        
        if failed > 0:
            print("\nFailed Tests:")
            for t in results:
                if not t.passed:
                    print(f"  ✗ {t.name}")
                    if t.error:
                        print(f"    Error: {t.error}")
        
        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / len(results) * 100) if results else 0,
            "total_duration": total_duration,
            "tests": results,
        }


def create_test_suite() -> List[TestCase]:
    """Create default test suite."""
    return [
        # Basic chat tests
        TestCase(
            name="Basic greeting",
            input_text="Say 'Hello from test'",
            expected_keywords=["hello", "test"],
            use_tools=False,
        ),
        
        TestCase(
            name="Simple math",
            input_text="What is 2 + 2?",
            expected_keywords=["4"],
            use_tools=False,
        ),
        
        # Tool calling tests
        TestCase(
            name="List directory",
            input_text="List files in /tmp directory using list_dir tool",
            expected_keywords=["tmp"],
            use_tools=True,
        ),
        
        TestCase(
            name="Read file",
            input_text="Read the /etc/hostname file using read_file tool",
            use_tools=True,
            validate_func=lambda r: "hostname" in r.lower() or len(r) > 10,
        ),
        
        TestCase(
            name="Run command",
            input_text="Run 'echo test123' using run_command tool",
            expected_keywords=["test123"],
            use_tools=True,
        ),
        
        TestCase(
            name="Search files",
            input_text="Search for Python files (*.py) in current directory using search_files tool",
            use_tools=True,
            validate_func=lambda r: ".py" in r or "no files" in r.lower(),
        ),
        
        # Complex tests
        TestCase(
            name="Multi-step task",
            input_text="Create a file /tmp/test_leocode.txt with content 'Agent test passed', then read it back",
            expected_keywords=["test_leocode.txt", "Agent test passed"],
            use_tools=True,
        ),
        
        TestCase(
            name="Code generation",
            input_text="Write a Python function that calculates factorial",
            expected_keywords=["def", "factorial"],
            use_tools=False,
        ),
    ]


async def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Leocode Agent Real Testing")
    parser.add_argument(
        "-d", "--dir",
        default="/tmp",
        help="Working directory for agent",
    )
    parser.add_argument(
        "-t", "--test",
        help="Run specific test by name",
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List available tests",
    )
    parser.add_argument(
        "-o", "--output",
        help="Save results to JSON file",
    )
    
    args = parser.parse_args()
    
    # Create test suite
    tests = create_test_suite()
    
    if args.list:
        print("\nAvailable Tests:")
        for i, test in enumerate(tests, 1):
            print(f"  {i}. {test.name}")
            print(f"     Input: {test.input_text[:60]}...")
            print(f"     Tools: {'Yes' if test.use_tools else 'No'}")
        return 0
    
    # Filter tests if specific test requested
    if args.test:
        tests = [t for t in tests if args.test.lower() in t.name.lower()]
        if not tests:
            print(f"No tests matching: {args.test}")
            return 1
    
    # Run tests
    tester = AgentTester(working_dir=args.dir)
    summary = await tester.run_test_suite(tests)
    
    # Save results if requested
    if args.output:
        output_data = {
            "summary": {
                "total": summary["total"],
                "passed": summary["passed"],
                "failed": summary["failed"],
                "success_rate": summary["success_rate"],
                "total_duration": summary["total_duration"],
            },
            "tests": [
                {
                    "name": t.name,
                    "input": t.input_text,
                    "passed": t.passed,
                    "duration": t.duration,
                    "result": t.result[:500] if t.result else None,
                    "error": t.error,
                }
                for t in summary["tests"]
            ],
        }
        Path(args.output).write_text(json.dumps(output_data, indent=2))
        print(f"\nResults saved to: {args.output}")
    
    # Exit code based on success
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTests cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
