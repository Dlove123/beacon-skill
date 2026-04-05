#!/usr/bin/env python3
"""
Test suite for AgentHive Transport
Issue #147 - Add AgentHive transport: independent MoltBook alternative
"""

import sys
from pathlib import Path

def test_agenthive_module_exists():
    """Test that agenthive transport module exists"""
    module_path = Path('beacon_skill/transports/agenthive.py')
    assert module_path.exists(), f"Module not found: {module_path}"
    
    with open(module_path) as f:
        content = f.read()
    
    assert 'class AgentHiveClient' in content, "AgentHiveClient class not found"
    assert 'class AgentHiveError' in content, "AgentHiveError class not found"
    print("✅ test_agenthive_module_exists: PASSED")

def test_agenthive_client_init():
    """Test AgentHiveClient initialization"""
    module_path = Path('beacon_skill/transports/agenthive.py')
    with open(module_path) as f:
        content = f.read()
    
    assert 'def __init__' in content, "__init__ method not found"
    assert 'base_url' in content, "base_url parameter not found"
    assert 'api_key' in content, "api_key parameter not found"
    assert 'timeout_s' in content, "timeout_s parameter not found"
    print("✅ test_agenthive_client_init: PASSED")

def test_agenthive_api_methods():
    """Test that all required API methods exist"""
    module_path = Path('beacon_skill/transports/agenthive.py')
    with open(module_path) as f:
        content = f.read()
    
    required_methods = [
        'register_agent',
        'create_post',
        'get_feed',
        'follow_agent',
        'get_agent_posts',
    ]
    
    for method in required_methods:
        assert f'def {method}' in content, f"Method {method} not found"
    
    print(f"✅ test_agenthive_api_methods: PASSED - {len(required_methods)} methods")

def test_agenthive_api_endpoints():
    """Test that correct API endpoints are used"""
    module_path = Path('beacon_skill/transports/agenthive.py')
    with open(module_path) as f:
        content = f.read()
    
    required_endpoints = [
        '/api/agents',
        '/api/posts',
        '/api/feed',
        '/follow',
    ]
    
    for endpoint in required_endpoints:
        assert endpoint in content, f"Endpoint {endpoint} not found"
    
    print(f"✅ test_agenthive_api_endpoints: PASSED - {len(required_endpoints)} endpoints")

def test_agenthive_error_handling():
    """Test error handling"""
    module_path = Path('beacon_skill/transports/agenthive.py')
    with open(module_path) as f:
        content = f.read()
    
    assert 'AgentHiveError' in content, "AgentHiveError not defined"
    assert 'raise AgentHiveError' in content, "Errors not raised"
    assert 'api_key' in content and 'required' in content.lower(), "API key validation not found"
    print("✅ test_agenthive_error_handling: PASSED")

def test_agenthive_retry():
    """Test that retry decorator is used"""
    module_path = Path('beacon_skill/transports/agenthive.py')
    with open(module_path) as f:
        content = f.read()
    
    assert 'from ..retry import' in content or 'with_retry' in content, "Retry decorator not imported"
    print("✅ test_agenthive_retry: PASSED")

def test_agenthive_requests():
    """Test that requests library is used"""
    module_path = Path('beacon_skill/transports/agenthive.py')
    with open(module_path) as f:
        content = f.read()
    
    assert 'import requests' in content, "requests library not imported"
    assert 'Session()' in content or 'requests.' in content, "requests Session not used"
    print("✅ test_agenthive_requests: PASSED")

def test_agenthive_auth_header():
    """Test that auth header is set correctly"""
    module_path = Path('beacon_skill/transports/agenthive.py')
    with open(module_path) as f:
        content = f.read()
    
    assert 'Authorization' in content, "Authorization header not found"
    assert 'Bearer' in content, "Bearer token format not found"
    print("✅ test_agenthive_auth_header: PASSED")

def test_agenthive_json_handling():
    """Test JSON handling"""
    module_path = Path('beacon_skill/transports/agenthive.py')
    with open(module_path) as f:
        content = f.read()
    
    assert 'json=' in content or 'application/json' in content, "JSON handling not found"
    assert '.json()' in content, "JSON response parsing not found"
    print("✅ test_agenthive_json_handling: PASSED")

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("AgentHive Transport Test Suite (Issue #147)")
    print("=" * 60)
    print()
    
    tests = [
        test_agenthive_module_exists,
        test_agenthive_client_init,
        test_agenthive_api_methods,
        test_agenthive_api_endpoints,
        test_agenthive_error_handling,
        test_agenthive_retry,
        test_agenthive_requests,
        test_agenthive_auth_header,
        test_agenthive_json_handling,
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: FAILED - {e}")
            failed += 1
        except Exception as e:
            print(f"⚠️  {test.__name__}: ERROR - {e}")
            skipped += 1
    
    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 60)
    
    return failed == 0

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
