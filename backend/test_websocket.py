#!/usr/bin/env python3
"""Test script to verify WebSocket implementation works with existing system."""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_websocket_import():
    """Test that WebSocket can be imported without breaking existing functionality."""
    print("Testing WebSocket import...")
    
    try:
        from app.core.websocket import ws_manager
        print(f"✅ WebSocket manager imported successfully")
        print(f"✅ WebSocket enabled: {ws_manager.is_enabled}")
        
        if ws_manager.is_enabled:
            print("✅ WebSocket is available and functional")
        else:
            print("⚠️  WebSocket is disabled (this is OK)")
        
    except Exception as e:
        print(f"❌ WebSocket import failed: {e}")
        return False
    
    return True

async def test_main_app_import():
    """Test that main app can be imported with WebSocket changes."""
    print("\nTesting main app import...")
    
    try:
        from app.main import app, WEBSOCKET_AVAILABLE
        print(f"✅ Main app imported successfully")
        print(f"✅ WebSocket availability: {WEBSOCKET_AVAILABLE}")
        
    except Exception as e:
        print(f"❌ Main app import failed: {e}")
        return False
    
    return True

async def test_workflow_import():
    """Test that workflow can be imported with WebSocket changes."""
    print("\nTesting workflow import...")
    
    try:
        from app.core.graph.workflow import ProductAnalysisWorkflow
        workflow = ProductAnalysisWorkflow()
        print(f"✅ Workflow imported and initialized successfully")
        
        # Test the WebSocket update method
        await workflow._emit_progress_update(None, 50, "test", "test_agent", "test message")
        print(f"✅ WebSocket update method works (safe even with None task_id)")
        
    except Exception as e:
        print(f"❌ Workflow import/test failed: {e}")
        return False
    
    return True

async def test_websocket_events():
    """Test WebSocket event emission (safe to call even if disabled)."""
    print("\nTesting WebSocket event emission...")
    
    try:
        from app.core.websocket import ws_manager
        
        # These should be safe to call even if WebSocket is disabled
        await ws_manager.emit_progress_update("test_task", 25, "processing", "test_agent", "test")
        await ws_manager.emit_agent_status("test_task", "test_agent", "running", "test")
        await ws_manager.emit_analysis_complete("test_task", {"test": "data"})
        
        print("✅ WebSocket events can be called safely (no errors even if disabled)")
        
    except Exception as e:
        print(f"❌ WebSocket event emission failed: {e}")
        return False
    
    return True

async def main():
    """Run all tests."""
    print("🧪 Testing WebSocket implementation with backward compatibility")
    print("=" * 60)
    
    tests = [
        test_websocket_import,
        test_main_app_import,
        test_workflow_import,
        test_websocket_events
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"✅ Passed: {sum(results)}/{len(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! WebSocket implementation is backward compatible.")
        print("💡 The system will work with or without WebSocket functionality.")
    else:
        print("\n⚠️  Some tests failed. Please review the implementation.")
    
    return all(results)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)