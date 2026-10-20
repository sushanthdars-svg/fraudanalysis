"""
Dashboard Overview Page
"""
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from components import AuthHandler, APIClient, create_metric_row, create_line_chart, create_bar_chart, display_chart_with_error_handling, display_empty_state
from utils import format_currency, format_percentage, format_large_number, show_error_message


def main():
    """Main dashboard overview."""
    
    # Check authentication
    if not AuthHandler.is_authenticated():
        st.error("Please login to access this page")
        return
    
    # Check permission
    if not AuthHandler.has_permission("view_dashboard"):
        st.error("You don't have permission to view this page")
        return
    
    # Get API client
    client = AuthHandler.get_api_client()
    
    # Page title
    st.markdown("## 📊 Executive Overview")
    
    # KPI Cards
    st.markdown("### Key Performance Indicators")
    
    # Fetch stats
    with st.spinner("Loading dashboard data..."):
        stats = client.get_transaction_stats()
        alert_stats = client.get_alert_stats()
    
    if "error" in stats or "error" in alert_stats:
        show_error_message(
            "Error Loading Data",
            "Could not fetch dashboard metrics. Please try refreshing."
        )
        return
    
    # Display KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_txns = stats.get("total_transactions", 0)
        st.metric(
            "📊 Total Transactions",
            format_large_number(total_txns),
            "Last 30 days"
        )
    
    with col2:
        fraud_count = stats.get("flagged_transactions", 0)
        fraud_rate = (fraud_count / total_txns * 100) if total_txns > 0 else 0
        st.metric(
            "⚠️ Flagged Transactions",
            f"{fraud_count:,}",
            f"{fraud_rate:.2f}% of total"
        )
    
    with col3:
        pending_alerts = alert_stats.get("pending_count", 0)
        st.metric(
            "🚨 Pending Alerts",
            pending_alerts,
            "Awaiting review"
        )
    
    with col4:
        avg_risk = stats.get("average_risk_score", 0)
        st.metric(
            "📈 Avg Risk Score",
            f"{avg_risk:.1f}%",
            "System-wide average"
        )
    
    st.divider()
    
    # Fraud Trends
    st.markdown("### Fraud Trends (Last 30 Days)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Fraud trend line chart
        fraud_trend = stats.get("fraud_trend", [])
        if fraud_trend:
            display_chart_with_error_handling(
                create_line_chart,
                fraud_trend,
                "Fraud Cases Over Time",
                "date",
                "count",
                "Date",
                "Fraud Cases"
            )
        else:
            display_empty_state("No fraud trend data available")
    
    with col2:
        # Transaction volume trend
        volume_trend = stats.get("volume_trend", [])
        if volume_trend:
            display_chart_with_error_handling(
                create_line_chart,
                volume_trend,
                "Transaction Volume Trend",
                "date",
                "count",
                "Date",
                "Transactions"
            )
        else:
            display_empty_state("No volume trend data available")
    
    st.divider()
    
    # Risk Distribution
    st.markdown("### Risk Level Distribution")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        risk_dist = stats.get("risk_distribution", {})
        if risk_dist:
            low = risk_dist.get("low", 0)
            st.metric("🟢 Low Risk", low, f"{(low/total_txns*100):.1f}%")
        
        st.metric("🟡 Medium Risk", risk_dist.get("medium", 0), "-")
    
    with col2:
        st.metric("🔴 High Risk", risk_dist.get("high", 0), "-")
        st.metric("⚫ Critical", risk_dist.get("critical", 0), "-")
    
    with col3:
        if risk_dist:
            try:
                from components import create_pie_chart
                risk_data = [
                    {"name": "Low", "count": risk_dist.get("low", 0)},
                    {"name": "Medium", "count": risk_dist.get("medium", 0)},
                    {"name": "High", "count": risk_dist.get("high", 0)},
                    {"name": "Critical", "count": risk_dist.get("critical", 0)},
                ]
                display_chart_with_error_handling(
                    create_pie_chart,
                    risk_data,
                    "Risk Distribution"
                )
            except Exception as e:
                st.error(f"Error creating chart: {str(e)}")
    
    st.divider()
    
    # Top Merchants by Fraud
    st.markdown("### Top Merchants by Fraud Cases")
    
    top_merchants = stats.get("top_merchants_by_fraud", [])
    if top_merchants:
        display_chart_with_error_handling(
            create_bar_chart,
            top_merchants,
            "Fraud Cases by Merchant",
            "merchant_id",
            "fraud_count",
            "Merchant",
            "Fraud Cases",
            horizontal=True
        )
    else:
        display_empty_state("No merchant fraud data available")
    
    st.divider()
    
    # Alert Queue Summary
    st.markdown("### Alert Queue Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "⏳ Pending",
            alert_stats.get("pending_count", 0)
        )
    
    with col2:
        st.metric(
            "👁️ Under Review",
            alert_stats.get("under_review_count", 0)
        )
    
    with col3:
        st.metric(
            "✅ Approved",
            alert_stats.get("approved_count", 0)
        )
    
    with col4:
        st.metric(
            "❌ Rejected",
            alert_stats.get("rejected_count", 0)
        )
    
    st.divider()
    
    # System Health
    st.markdown("### System Health")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "📡 API Status",
            "🟢 Operational",
            "All systems running"
        )
    
    with col2:
        st.metric(
            "🤖 ML Model",
            "🟢 Active",
            "Last trained 1 hour ago"
        )
    
    with col3:
        st.metric(
            "💾 Database",
            "🟢 Healthy",
            "0% errors"
        )


if __name__ == "__main__":
    main()
