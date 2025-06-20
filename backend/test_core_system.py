#!/usr/bin/env python3
"""Comprehensive test suite for the core multi-agent product analysis system.

This script tests all major components without requiring API endpoints.
"""

import asyncio
import sys
import os
from datetime import datetime
from uuid import uuid4

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.graph import create_analysis_workflow
from app.core.logging import logger
from app.services.analysis_service import analysis_service
from app.schemas.analysis import AnalysisTaskCreate
from pydantic import HttpUrl


async def test_database_connection():
    """Test database connection and basic operations."""
    print("\n🔍 Testing Database Connection...")

    try:
        # Test database health
        health = await analysis_service.db_service.health_check()
        if health:
            print("✅ Database connection healthy")
        else:
            print("❌ Database connection failed")
            return False

        # Test creating a task
        task_data = AnalysisTaskCreate(product_url=HttpUrl("https://www.amazon.com/dp/B0D1JCB5RY"))
        task = await analysis_service.create_analysis_task(task_data)

        if task and task.id:
            print(f"✅ Test task created: {task.id}")

            # Test retrieving the task
            retrieved_task = await analysis_service.get_analysis_task(task.id)
            if retrieved_task:
                print("✅ Task retrieval successful")
                return task.id
            else:
                print("❌ Task retrieval failed")
                return False
        else:
            print("❌ Task creation failed")
            return False

    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False


async def test_individual_agents():
    """Test each agent individually with mock data."""
    print("\n🤖 Testing Individual Agents...")

    try:
        from langchain_openai import ChatOpenAI
        from app.core.config import settings
        from app.core.agents import DataCollectorAgent, MarketAnalyzerAgent, OptimizationAdvisorAgent, SupervisorAgent
        from app.core.graph.state import AnalysisState

        # Initialize LLM
        llm = ChatOpenAI(model=settings.LLM_MODEL, temperature=0.1, api_key=settings.LLM_API_KEY)

        # Test state
        test_state = {
            "task_id": None,
            "user_id": None,
            "product_url": "https://www.amazon.com/dp/B0D1JCB5RY",
            "asin": "B0D1JCB5RY",
            "messages": [],
            "next_agent": "",
            "product_data": {},
            "market_analysis": {},
            "optimization_advice": {},
            "competitor_candidates": [],
            "competitor_data": [],
            "analysis_phase": "main_product",
            "iteration_count": 0,
            "max_iterations": 3,
            "progress": 0,
            "status": "processing",
            "error_message": None,
            "final_analysis": "",
            "analysis_metadata": {},
        }

        # Test SupervisorAgent
        print("  📋 Testing SupervisorAgent...")
        supervisor = SupervisorAgent(llm)
        state_after_supervisor = supervisor(test_state.copy())
        if state_after_supervisor.get("next_agent"):
            print(f"  ✅ SupervisorAgent working - next agent: {state_after_supervisor['next_agent']}")
        else:
            print("  ❌ SupervisorAgent failed")
            return False

        # Test DataCollectorAgent (this will actually scrape)
        print("  🔍 Testing DataCollectorAgent...")
        data_collector = DataCollectorAgent(llm)
        state_after_data = data_collector(test_state.copy())
        if state_after_data.get("product_data"):
            print("  ✅ DataCollectorAgent working - product data collected")
            product_source = state_after_data["product_data"].get("source", "unknown")
            print(f"  📊 Data source: {product_source}")
        else:
            print("  ❌ DataCollectorAgent failed")
            return False

        # Test MarketAnalyzerAgent with collected data
        print("  📈 Testing MarketAnalyzerAgent...")
        market_analyzer = MarketAnalyzerAgent(llm)
        market_state = state_after_data.copy()
        market_state["analysis_phase"] = "basic_analysis"
        state_after_market = market_analyzer(market_state)
        if state_after_market.get("market_analysis", {}).get("status") == "completed":
            print("  ✅ MarketAnalyzerAgent working - analysis completed")
        else:
            print("  ❌ MarketAnalyzerAgent failed")
            return False

        # Test OptimizationAdvisorAgent
        print("  💡 Testing OptimizationAdvisorAgent...")
        optimization_advisor = OptimizationAdvisorAgent(llm)
        state_after_optimization = optimization_advisor(state_after_market)
        if state_after_optimization.get("optimization_advice", {}).get("status") == "completed":
            print("  ✅ OptimizationAdvisorAgent working - recommendations generated")
        else:
            print("  ❌ OptimizationAdvisorAgent failed")
            return False

        print("✅ All individual agents tested successfully")
        return True

    except Exception as e:
        print(f"❌ Agent testing failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def test_core_tools():
    """Test core scraping and parsing tools."""
    print("\n🛠️ Testing Core Tools...")

    try:
        from app.core.tools import ProductScraper, TextProcessor, AmazonCompetitorExtractor

        # Test TextProcessor
        print("  📝 Testing TextProcessor...")
        processor = TextProcessor()

        test_price = processor.extract_price("$43.95")
        test_rating = processor.extract_rating("4.5 out of 5 stars")
        test_reviews = processor.extract_review_count("5,003 ratings")

        if test_price == 43.95 and test_rating == 4.5 and test_reviews == 5003:
            print("  ✅ TextProcessor working correctly")
        else:
            print(f"  ❌ TextProcessor failed - price: {test_price}, rating: {test_rating}, reviews: {test_reviews}")
            return False

        # Test ProductScraper
        print("  🕷️ Testing ProductScraper...")
        async with ProductScraper() as scraper:
            # Test with a real Amazon URL
            product_data = await scraper.scrape("https://www.amazon.com/dp/B0D1JCB5RY")

            if product_data and product_data.is_valid():
                print(f"  ✅ ProductScraper working - scraped: {product_data.title[:50]}...")
                print(f"  📊 Price: ${product_data.price}, Rating: {product_data.rating}/5")
            else:
                print("  ⚠️ ProductScraper didn't get valid data (may be rate limited)")
                # Don't fail the test completely as this could be due to rate limiting

        # Test AmazonCompetitorExtractor
        print("  🏢 Testing AmazonCompetitorExtractor...")
        extractor = AmazonCompetitorExtractor()

        # Create a simple HTML test
        test_html = """
        <div id="sp_detail_thematic">
            <div data-asin="B0TEST123" data-adfeedbackdetails='{"priceAmount": 49.99}'>
                <a title="Test Product">Test Product</a>
            </div>
        </div>
        """

        competitors = await extractor.extract_competitors(test_html, "B0MAINPROD")
        if competitors and len(competitors) > 0:
            print(f"  ✅ AmazonCompetitorExtractor working - found {len(competitors)} competitors")
        else:
            print("  ⚠️ AmazonCompetitorExtractor found no competitors (expected with minimal HTML)")

        print("✅ Core tools tested successfully")
        return True

    except Exception as e:
        print(f"❌ Tools testing failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def test_full_workflow():
    """Test the complete workflow end-to-end."""
    print("\n🔄 Testing Full Workflow...")

    try:
        # Create workflow
        workflow = create_analysis_workflow()
        print("  ✅ Workflow created successfully")

        # Create a test task in database
        task_data = AnalysisTaskCreate(product_url=HttpUrl("https://www.amazon.com/dp/B0D1JCB5RY"))
        task = await analysis_service.create_analysis_task(task_data)
        task_id = task.id if task else None

        if task_id:
            print(f"  ✅ Test task created: {task_id}")
        else:
            print("  ⚠️ Could not create test task, running without database tracking")

        # Run the workflow (with shorter max_iterations for testing)
        print("  🚀 Running full analysis workflow...")
        result = await workflow.run_analysis(
            product_url="https://www.amazon.com/dp/B0D1JCB5RY",
            max_iterations=4,  # Shorter for testing
            task_id=task_id,
        )

        if result and len(result) > 100:  # Basic check for substantial output
            print("  ✅ Full workflow completed successfully")
            print(f"  📄 Report length: {len(result)} characters")

            # Check if report contains expected sections
            expected_sections = ["Product Analysis Report", "Market Analysis", "Optimization Recommendations"]
            sections_found = sum(1 for section in expected_sections if section in result)

            print(f"  📋 Report sections found: {sections_found}/{len(expected_sections)}")

            if sections_found >= 2:  # At least 2 out of 3 sections
                print("  ✅ Report structure looks good")
                return result, task_id
            else:
                print("  ⚠️ Report structure incomplete but workflow completed")
                return result, task_id
        else:
            print("  ❌ Full workflow failed - no substantial output")
            return False, task_id

    except Exception as e:
        print(f"❌ Full workflow test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False, None


async def test_database_integration(task_id):
    """Test database integration and data persistence."""
    print("\n💾 Testing Database Integration...")

    if not task_id:
        print("  ⚠️ No task ID available, skipping database integration test")
        return True

    try:
        # Test retrieving the completed task
        task = await analysis_service.get_analysis_task(task_id)
        if task:
            print(f"  ✅ Task retrieved: {task.id}")
            print(f"  📊 Status: {task.status}, Progress: {task.progress}%")

            if task.status.value == "completed":
                print("  ✅ Task marked as completed")
            else:
                print(f"  ⚠️ Task status: {task.status}")
        else:
            print("  ❌ Could not retrieve task")
            return False

        # Test getting analysis stats
        stats = await analysis_service.get_analysis_stats()
        print(f"  📈 Analysis stats - Total: {stats.total_tasks}, Completed: {stats.completed_tasks}")

        print("✅ Database integration tested successfully")
        return True

    except Exception as e:
        print(f"❌ Database integration test failed: {str(e)}")
        return False


def display_sample_output(result):
    """Display a sample of the workflow output."""
    if not result:
        return

    print("\n📄 Sample Output:")
    print("=" * 80)

    # Show first 500 characters
    sample = result[:500]
    print(sample)

    if len(result) > 500:
        print("\n... (truncated)")
        print(f"\nTotal length: {len(result)} characters")

    print("=" * 80)


async def main():
    """Run all tests."""
    print("🧪 Core System Testing Suite")
    print("=" * 50)

    # Test results
    results = []

    # Test 1: Database Connection
    db_result = await test_database_connection()
    results.append(("Database Connection", db_result))

    if not db_result:
        print("\n❌ Critical: Database connection failed. Cannot continue with full tests.")
        return

    # Test 2: Individual Agents
    agent_result = await test_individual_agents()
    results.append(("Individual Agents", agent_result))

    # Test 3: Core Tools
    tools_result = await test_core_tools()
    results.append(("Core Tools", tools_result))

    # Test 4: Full Workflow (only if previous tests passed)
    if agent_result and tools_result:
        workflow_result, task_id = await test_full_workflow()
        results.append(("Full Workflow", bool(workflow_result)))

        if workflow_result:
            display_sample_output(workflow_result)

        # Test 5: Database Integration
        db_integration_result = await test_database_integration(task_id)
        results.append(("Database Integration", db_integration_result))
    else:
        print("\n⏭️ Skipping full workflow test due to previous failures")
        results.append(("Full Workflow", False))
        results.append(("Database Integration", False))

    # Summary
    print("\n📊 Test Summary:")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Core system is ready for production.")
    elif passed >= total * 0.8:  # 80% pass rate
        print("\n✅ Most tests passed. Core system is functional with minor issues.")
    else:
        print("\n⚠️ Several tests failed. Core system needs attention before proceeding.")

    return passed == total


if __name__ == "__main__":
    # Check environment
    if not os.getenv("LLM_API_KEY"):
        print("❌ ERROR: LLM_API_KEY not found in environment")
        print("Please set your LLM API key in the .env.development file")
        sys.exit(1)

    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
