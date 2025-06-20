"""Streamlit Frontend for Amazon Product Analyzer
===============================================

This is a web interface for testing the Amazon Product Analyzer API.
It provides an intuitive way to submit product URLs, monitor analysis progress,
and view results.
"""

import time
import requests
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List


# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
HEALTH_URL = "http://localhost:8000/health"


class ProductAnalyzerAPI:
    """Client for interacting with the Product Analyzer API."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()

    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        try:
            response = self.session.get(f"{HEALTH_URL}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"status": "error", "error": str(e)}

    def create_analysis(self, product_url: str) -> Dict[str, Any]:
        """Create a new analysis task."""
        try:
            response = self.session.post(
                f"{self.base_url}/product-analysis/analyze", json={"product_url": product_url}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status and progress."""
        try:
            response = self.session.get(f"{self.base_url}/product-analysis/tasks/{task_id}/status")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def get_task_details(self, task_id: str) -> Dict[str, Any]:
        """Get detailed task information."""
        try:
            response = self.session.get(f"{self.base_url}/product-analysis/tasks/{task_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def list_tasks(self, limit: int = 10, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List analysis tasks."""
        try:
            params = {"limit": limit}
            if status_filter:
                params["status_filter"] = status_filter

            response = self.session.get(f"{self.base_url}/product-analysis/tasks", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get analysis statistics."""
        try:
            response = self.session.get(f"{self.base_url}/product-analysis/stats")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def delete_task(self, task_id: str) -> bool:
        """Delete an analysis task."""
        try:
            response = self.session.delete(f"{self.base_url}/product-analysis/tasks/{task_id}")
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False

    def create_batch_analysis(self, product_urls: List[str]) -> Dict[str, Any]:
        """Create batch analysis."""
        try:
            response = self.session.post(
                f"{self.base_url}/product-analysis/batch", json={"product_urls": product_urls}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Amazon Product Analyzer", page_icon="🛒", layout="wide", initial_sidebar_state="expanded"
    )

    # Initialize API client
    api = ProductAnalyzerAPI(API_BASE_URL)

    # Header
    st.title("🛒 Amazon Product Analyzer")
    st.markdown("**Multi-Agent Product Analysis System**")
    st.markdown("---")

    # Sidebar
    st.sidebar.title("🔧 控制台")

    # Health Check
    st.sidebar.subheader("🏥 系統狀態")
    if st.sidebar.button("檢查健康狀態"):
        health = api.health_check()
        if health.get("status") == "healthy":
            st.sidebar.success("✅ 系統正常")
            with st.sidebar.expander("詳細狀態"):
                st.json(health)
        else:
            st.sidebar.error("❌ 系統異常")
            with st.sidebar.expander("錯誤詳情"):
                st.json(health)

    # Navigation
    page = st.sidebar.selectbox("選擇頁面", ["🚀 新建分析", "📊 儀表板", "📋 任務管理", "📈 統計數據", "🔄 批量分析"])

    if page == "🚀 新建分析":
        show_new_analysis_page(api)
    elif page == "📊 儀表板":
        show_dashboard_page(api)
    elif page == "📋 任務管理":
        show_task_manager_page(api)
    elif page == "📈 統計數據":
        show_statistics_page(api)
    elif page == "🔄 批量分析":
        show_batch_analysis_page(api)


def show_new_analysis_page(api: ProductAnalyzerAPI):
    """Show the new analysis creation page."""
    st.header("🚀 創建新的產品分析")

    # Input form
    with st.form("new_analysis_form"):
        product_url = st.text_input(
            "Amazon 產品 URL", placeholder="https://www.amazon.com/dp/B0D1JCB5RY", help="請輸入有效的Amazon產品URL"
        )

        submitted = st.form_submit_button("🔍 開始分析", use_container_width=True)

        if submitted and product_url:
            if not any(domain in product_url.lower() for domain in ["amazon.com", "amazon.co.uk", "amazon.de"]):
                st.error("❌ 請輸入有效的Amazon產品URL")
                return

            with st.spinner("正在創建分析任務..."):
                result = api.create_analysis(product_url)

                if "error" in result:
                    st.error(f"❌ 錯誤: {result['error']}")
                else:
                    st.success("✅ 分析任務創建成功！")

                    # Store task ID in session state for tracking
                    st.session_state.current_task_id = result["id"]

                    # Display task info
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**任務ID:** {result['id']}")
                        st.info(f"**ASIN:** {result['asin']}")
                        st.info(f"**狀態:** {result['status']}")

                    with col2:
                        st.info(f"**進度:** {result['progress']}%")
                        st.info(f"**創建時間:** {result['created_at']}")

    # Auto-refresh section outside of form
    if hasattr(st.session_state, 'current_task_id') and st.session_state.current_task_id:
        show_task_progress(api, st.session_state.current_task_id)


def show_task_progress(api: ProductAnalyzerAPI, task_id: str):
    """Show real-time task progress."""
    st.subheader("📈 任務進度")

    # Create placeholders for dynamic updates
    status_placeholder = st.empty()
    progress_placeholder = st.empty()
    details_placeholder = st.empty()

    # Auto-refresh toggle
    auto_refresh = st.checkbox("🔄 自動刷新 (每5秒)", value=True)

    if auto_refresh:
        max_iterations = 60  # Maximum 5 minutes of auto-refresh
        for i in range(max_iterations):
            status_data = api.get_task_status(task_id)

            if "error" in status_data:
                status_placeholder.error(f"❌ 獲取狀態錯誤: {status_data['error']}")
                break

            # Update status
            status_emoji = {"pending": "🟡", "processing": "🔵", "completed": "🟢", "failed": "🔴"}.get(
                status_data["status"], "⚪"
            )

            status_placeholder.markdown(f"**狀態:** {status_emoji} {status_data['status'].upper()}")

            # Update progress bar
            progress = status_data.get("progress", 0)
            progress_placeholder.progress(progress / 100)

            # Show details
            with details_placeholder.container():
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("進度", f"{progress}%")
                with col2:
                    st.metric("狀態", status_data["status"])
                with col3:
                    if status_data.get("error_message"):
                        st.error(f"錯誤: {status_data['error_message']}")
                    else:
                        st.metric("更新時間", status_data.get("updated_at", "")[:19])

            # If completed or failed, get detailed results
            if status_data["status"] in ["completed", "failed"]:
                st.subheader("📄 分析結果")

                if status_data["status"] == "completed":
                    details = api.get_task_details(task_id)

                    if "error" not in details:
                        if details.get("reports"):
                            for report in details["reports"]:
                                st.markdown("### 📋 分析報告")
                                with st.expander("查看完整報告", expanded=True):
                                    st.markdown(report["content"])
                        else:
                            st.warning("暫無可用報告")
                            # Show raw product data if available
                            if details.get("product"):
                                st.subheader("📊 產品數據")
                                st.json(details["product"])
                    else:
                        st.error(f"獲取詳情失敗: {details['error']}")
                else:
                    st.error("❌ 任務執行失敗")
                    if status_data.get("error_message"):
                        st.text(f"錯誤信息: {status_data['error_message']}")

                break

            if not auto_refresh:
                break

            time.sleep(5)

    # Manual refresh button
    if st.button("🔄 手動刷新狀態"):
        status_data = api.get_task_status(task_id)
        st.json(status_data)


def show_dashboard_page(api: ProductAnalyzerAPI):
    """Show the main dashboard with recent tasks."""
    st.header("📊 控制面板")

    # Get statistics first
    stats = api.get_stats()
    if "error" not in stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("總任務數", stats["total_tasks"])
        with col2:
            st.metric("已完成", stats["completed_tasks"])
        with col3:
            st.metric("失敗任務", stats["failed_tasks"])
        with col4:
            success_rate = (stats["completed_tasks"] / max(stats["total_tasks"], 1)) * 100
            st.metric("成功率", f"{success_rate:.1f}%")

    st.markdown("---")

    # Get recent tasks
    recent_tasks = api.list_tasks(limit=5)

    if not recent_tasks:
        st.info("未找到任務。創建您的第一個分析！")
        return

    # Recent tasks
    st.subheader("🕒 最近任務")

    for task in recent_tasks:
        status_emoji = {"pending": "🟡", "processing": "🔵", "completed": "🟢", "failed": "🔴"}.get(
            task["status"], "⚪"
        )

        with st.expander(f"{status_emoji} {task['asin']} - {task['status'].upper()}", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**ID:** {task['id'][:12]}...")
                st.write(f"**ASIN:** {task['asin']}")

            with col2:
                st.write(f"**狀態:** {task['status']}")
                st.write(f"**進度:** {task['progress']}%")

            with col3:
                st.write(f"**創建:** {task['created_at'][:19]}")
                if task.get("completed_at"):
                    st.write(f"**完成:** {task['completed_at'][:19]}")

            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📊 查看詳情", key=f"view_{task['id']}"):
                    details = api.get_task_details(task["id"])
                    st.json(details)

            with col2:
                if st.button("🔄 刷新狀態", key=f"refresh_{task['id']}"):
                    status = api.get_task_status(task["id"])
                    st.json(status)

            with col3:
                if st.button("🗑️ 刪除", key=f"delete_{task['id']}"):
                    if api.delete_task(task["id"]):
                        st.success("任務已刪除！")
                        st.rerun()
                    else:
                        st.error("刪除任務失敗")


def show_task_manager_page(api: ProductAnalyzerAPI):
    """Show the task management page."""
    st.header("📋 任務管理")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("按狀態篩選", ["全部", "pending", "processing", "completed", "failed"])
    with col2:
        limit = st.number_input("任務數量", min_value=1, max_value=100, value=20)
    with col3:
        if st.button("🔄 刷新任務"):
            st.rerun()

    # Get tasks
    filter_value = None if status_filter == "全部" else status_filter
    tasks = api.list_tasks(limit=limit, status_filter=filter_value)

    if not tasks:
        st.info("未找到符合條件的任務。")
        return

    # Convert to DataFrame for better display
    df_data = []
    for task in tasks:
        df_data.append(
            {
                "ID": task["id"][:8] + "...",
                "ASIN": task["asin"],
                "產品標題": task.get("product_title", "N/A")[:30] + "..." if task.get("product_title") else "N/A",
                "狀態": task["status"],
                "進度": f"{task['progress']}%",
                "創建時間": task["created_at"][:19],
                "完成時間": task.get("completed_at", "N/A")[:19] if task.get("completed_at") else "N/A",
            }
        )

    df = pd.DataFrame(df_data)

    # Display table
    st.dataframe(df, use_container_width=True)

    # Bulk actions
    st.subheader("🔧 批量操作")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ 刪除失敗任務"):
            failed_tasks = [task for task in tasks if task["status"] == "failed"]
            deleted_count = 0
            for task in failed_tasks:
                if api.delete_task(task["id"]):
                    deleted_count += 1
            st.success(f"已刪除 {deleted_count} 個失敗任務")

    with col2:
        if st.button("📊 導出任務CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="💾 下載 CSV",
                data=csv,
                file_name=f"tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )


def show_statistics_page(api: ProductAnalyzerAPI):
    """Show system statistics."""
    st.header("📈 系統統計")

    # Get stats
    stats = api.get_stats()

    if "error" in stats:
        st.error(f"❌ 獲取統計數據錯誤: {stats['error']}")
        return

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("總任務數", stats["total_tasks"])
    with col2:
        st.metric("已完成", stats["completed_tasks"])
    with col3:
        st.metric("失敗", stats["failed_tasks"])
    with col4:
        if stats["total_tasks"] > 0:
            success_rate = (stats["completed_tasks"] / stats["total_tasks"]) * 100
            st.metric("成功率", f"{success_rate:.1f}%")
        else:
            st.metric("成功率", "0%")

    # More detailed stats
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 任務狀態分佈")
        status_data = {
            "待處理": stats["pending_tasks"],
            "處理中": stats["processing_tasks"],
            "已完成": stats["completed_tasks"],
            "失敗": stats["failed_tasks"],
        }

        # Create a simple bar chart
        st.bar_chart(status_data)

    with col2:
        st.subheader("⏱️ 性能指標")
        if stats.get("avg_completion_time_minutes"):
            st.metric("平均完成時間", f"{stats['avg_completion_time_minutes']:.1f} 分鐘")
        else:
            st.info("暫無完成時間數據")

        # Additional metrics
        if stats["total_tasks"] > 0:
            processing_rate = (stats["processing_tasks"] / stats["total_tasks"]) * 100
            st.metric("處理中比率", f"{processing_rate:.1f}%")


def show_batch_analysis_page(api: ProductAnalyzerAPI):
    """Show batch analysis page."""
    st.header("🔄 批量分析")
    st.markdown("一次分析多個產品")

    # URL input methods
    input_method = st.radio("輸入方式", ["手動輸入", "粘貼URLs"])

    product_urls = []

    if input_method == "手動輸入":
        st.subheader("手動輸入URLs")
        num_urls = st.number_input("URL數量", min_value=1, max_value=10, value=3)

        for i in range(num_urls):
            url = st.text_input(f"產品 URL {i + 1}", key=f"url_{i}")
            if url:
                product_urls.append(url)

    elif input_method == "粘貼URLs":
        st.subheader("粘貼URLs（每行一個）")
        urls_text = st.text_area(
            "URLs",
            height=200,
            placeholder="https://www.amazon.com/dp/B0D1JCB5RY\nhttps://www.amazon.com/dp/B0BZXLMM3H",
        )

        if urls_text:
            product_urls = [url.strip() for url in urls_text.split("\n") if url.strip()]

    # Validate URLs
    valid_urls = []
    invalid_urls = []

    for url in product_urls:
        if any(domain in url.lower() for domain in ["amazon.com", "amazon.co.uk", "amazon.de"]):
            valid_urls.append(url)
        else:
            invalid_urls.append(url)

    if invalid_urls:
        st.warning(f"❌ 發現 {len(invalid_urls)} 個無效URLs（將被跳過）")
        with st.expander("顯示無效URLs"):
            for url in invalid_urls:
                st.write(f"❌ {url}")

    if valid_urls:
        st.success(f"✅ 發現 {len(valid_urls)} 個有效URLs")

        # Preview URLs
        with st.expander("預覽有效URLs"):
            for i, url in enumerate(valid_urls, 1):
                st.write(f"{i}. {url}")

        if st.button("🚀 開始批量分析", use_container_width=True):
            with st.spinner("正在創建批量分析..."):
                result = api.create_batch_analysis(valid_urls)

                if "error" in result:
                    st.error(f"❌ 錯誤: {result['error']}")
                else:
                    st.success("✅ 批量分析創建成功！")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**批次ID:** {result['batch_id']}")
                        st.info(f"**總任務數:** {result['total_tasks']}")

                    with col2:
                        st.info(f"**創建時間:** {result['created_at']}")

                    # Show task IDs
                    with st.expander("📋 任務IDs"):
                        for i, task_id in enumerate(result["task_ids"], 1):
                            st.write(f"{i}. {task_id}")

                    st.info("💡 提示：前往「任務管理」頁面查看所有任務的詳細狀態")


if __name__ == "__main__":
    main()
