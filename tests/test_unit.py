#!/usr/bin/env python3
"""
Unit tests for agent tools - fast, isolated tests.
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from leocode.agent import AgentTools


def test_read_file():
    """Test read_file tool."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("line 1\nline 2\nline 3\n")
        f.flush()
        temp_path = f.name
    
    try:
        agent = AgentTools()
        result = agent.execute("read_file", {"path": temp_path})
        
        assert "line 1" in result
        assert "line 2" in result
        assert "line 3" in result
        print("✓ test_read_file passed")
        return True
    finally:
        os.unlink(temp_path)


def test_write_file():
    """Test write_file tool."""
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, "test_write.txt")
    
    try:
        agent = AgentTools()
        result = agent.execute("write_file", {
            "path": temp_path,
            "content": "test content\n"
        })
        
        assert "Written" in result
        assert os.path.exists(temp_path)
        
        with open(temp_path) as f:
            content = f.read()
        assert content == "test content\n"
        
        print("✓ test_write_file passed")
        return True
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        os.rmdir(temp_dir)


def test_edit_file():
    """Test edit_file tool."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello world\nTest line\n")
        f.flush()
        temp_path = f.name
    
    try:
        agent = AgentTools()
        result = agent.execute("edit_file", {
            "path": temp_path,
            "old": "world",
            "new": "universe"
        })
        
        assert "Replaced" in result
        
        with open(temp_path) as f:
            content = f.read()
        assert "universe" in content
        assert "world" not in content
        
        print("✓ test_edit_file passed")
        return True
    finally:
        os.unlink(temp_path)


def test_list_dir():
    """Test list_dir tool."""
    temp_dir = tempfile.mkdtemp()
    
    # Create some files
    Path(temp_dir, "file1.txt").write_text("test")
    Path(temp_dir, "file2.txt").write_text("test")
    os.mkdir(Path(temp_dir, "subdir"))
    
    try:
        agent = AgentTools()
        result = agent.execute("list_dir", {"path": temp_dir})
        
        assert "file1.txt" in result
        assert "file2.txt" in result
        assert "subdir/" in result
        
        print("✓ test_list_dir passed")
        return True
    finally:
        # Cleanup
        Path(temp_dir, "file1.txt").unlink()
        Path(temp_dir, "file2.txt").unlink()
        Path(temp_dir, "subdir").rmdir()
        os.rmdir(temp_dir)


def test_run_command():
    """Test run_command tool."""
    agent = AgentTools()
    result = agent.execute("run_command", {"command": "echo test123"})
    
    assert "test123" in result
    print("✓ test_run_command passed")
    return True


def test_search_files():
    """Test search_files tool."""
    temp_dir = tempfile.mkdtemp()
    
    # Create test files
    Path(temp_dir, "test.py").write_text("# Python")
    Path(temp_dir, "test.txt").write_text("text")
    Path(temp_dir, "other.py").write_text("# Python")
    
    try:
        agent = AgentTools(temp_dir)
        result = agent.execute("search_files", {"pattern": "*.py"})
        
        assert "test.py" in result
        assert "other.py" in result
        assert "test.txt" not in result
        
        print("✓ test_search_files passed")
        return True
    finally:
        Path(temp_dir, "test.py").unlink()
        Path(temp_dir, "test.txt").unlink()
        Path(temp_dir, "other.py").unlink()
        os.rmdir(temp_dir)


def test_search_content():
    """Test search_content tool."""
    temp_dir = tempfile.mkdtemp()
    
    # Create test files
    Path(temp_dir, "file1.txt").write_text("Hello world\nTest pattern\n")
    Path(temp_dir, "file2.txt").write_text("Other content\n")
    Path(temp_dir, "file3.txt").write_text("Test pattern again\n")
    
    try:
        agent = AgentTools(temp_dir)
        result = agent.execute("search_content", {"pattern": "Test pattern"})
        
        assert "file1.txt" in result
        assert "file3.txt" in result
        assert "Test pattern" in result
        
        print("✓ test_search_content passed")
        return True
    finally:
        Path(temp_dir, "file1.txt").unlink()
        Path(temp_dir, "file2.txt").unlink()
        Path(temp_dir, "file3.txt").unlink()
        os.rmdir(temp_dir)


def run_all_tests():
    """Run all unit tests."""
    print("\n" + "="*60)
    print("  LEOCODE AGENT UNIT TESTS")
    print("="*60 + "\n")
    
    tests = [
        test_read_file,
        test_write_file,
        test_edit_file,
        test_list_dir,
        test_run_command,
        test_search_files,
        test_search_content,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
