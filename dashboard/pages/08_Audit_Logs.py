"""
Audit Logs Page
"""
import streamlit as st
from datetime import datetime, timedelta
from components import (
    AuthHandler,
    create_audit_table,
    create_export_button,
    display_empty_state,
)
from utils import show_error_message


def main():
    """Main audit logs page."""
    
    # Check authentication
    if not AuthHandler.is_authenticated():
        st.error("Please login to access this page")
        return
    
    if not AuthHandler.has_permission("view_audit_logs"):
        st.error("You don't have permission to view audit logs")
        return
    
    client = AuthHandler.get_api_client()
    
    st.markdown("## 📋 Audit Logs")
    
    # Tabs
    tab1, tab2 = st.tabs(["Audit Trail", "Compliance Report"])
    
    with tab1:
        st.markdown("### Event Logs")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            actor = st.text_input(
                "Actor (Email)",
                placeholder="user@example.com",
                key="audit_actor"
            )
        
        with col2:
            action_type = st.selectbox(
                "Action Type",
                [
                    "All",
                    "LOGIN",
                    "LOGOUT",
                    "CREATE",
                    "UPDATE",
                    "DELETE",
                    "REVIEW",
                    "EXPORT",
                    "PERMISSION_CHANGE"
                ],
                index=0,
                key="audit_action"
            )
        
        with col3:
            target_entity = st.selectbox(
                "Target Entity",
                ["All", "User", "Rule", "Alert", "Transaction", "Model"],
                index=0,
                key="audit_entity"
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Start Date",
                datetime.now() - timedelta(days=30),
                key="audit_start_date"
            )
        
        with col2:
            end_date = st.date_input(
                "End Date",
                datetime.now(),
                key="audit_end_date"
            )
        
        # Search button
        if st.button("🔍 Search Logs", use_container_width=True):
            with st.spinner("Loading audit logs..."):
                filters = {
                    "actor": actor if actor else None,
                    "action_type": None if action_type == "All" else action_type,
                    "target_entity": None if target_entity == "All" else target_entity.lower(),
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "limit": 1000
                }
                
                response = client.get_audit_logs(**filters)
                
                if "error" in response:
                    show_error_message("Error", response.get("error"))
                else:
                    audit_logs = response.get("items", [])
                    
                    if not audit_logs:
                        display_empty_state("No audit events found")
                    else:
                        st.markdown(f"### {len(audit_logs)} Event(s) Found")
                        
                        # Export button
                        st.markdown("**Export:**")
                        create_export_button(audit_logs, "audit_logs")
                        
                        # Create audit table
                        audit_table = create_audit_table(audit_logs)
                        st.dataframe(audit_table, use_container_width=True, hide_index=True)
                        
                        st.divider()
                        
                        # Event details
                        st.markdown("### Event Details")
                        
                        event_summaries = [
                            f"{e.get('timestamp', '-')} | {e.get('actor', '-')} | {e.get('action_type', '-')}"
                            for e in audit_logs
                        ]
                        
                        selected_idx = st.selectbox(
                            "Select event",
                            range(len(event_summaries)),
                            format_func=lambda x: event_summaries[x],
                            key="selected_event"
                        )
                        
                        if selected_idx is not None:
                            event = audit_logs[selected_idx]
                            
                            # Display event details
                            with st.expander("Event Details", expanded=True):
                                import json
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown(f"**Timestamp:** {event.get('timestamp', '-')}")
                                    st.markdown(f"**Actor:** {event.get('actor', '-')}")
                                    st.markdown(f"**Action:** {event.get('action_type', '-')}")
                                
                                with col2:
                                    st.markdown(f"**Entity Type:** {event.get('target_entity_type', '-')}")
                                    st.markdown(f"**Entity ID:** {event.get('target_entity_id', '-')}")
                                    st.markdown(f"**Status:** {event.get('status', '-')}")
                                
                                if event.get("details"):
                                    st.markdown("**Details:**")
                                    st.json(event.get("details", {}))
    
    with tab2:
        st.markdown("### Compliance Report")
        
        # Report options
        col1, col2 = st.columns(2)
        
        with col1:
            report_type = st.selectbox(
                "Report Type",
                [
                    "User Access",
                    "Data Changes",
                    "Alerts Review",
                    "Rule Modifications",
                    "Model Updates",
                    "Security Events"
                ],
                key="report_type"
            )
        
        with col2:
            report_period = st.selectbox(
                "Period",
                ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom"],
                key="report_period"
            )
        
        if report_period == "Custom":
            col1, col2 = st.columns(2)
            with col1:
                custom_start = st.date_input(
                    "Custom Start Date",
                    datetime.now() - timedelta(days=90),
                    key="custom_start"
                )
            with col2:
                custom_end = st.date_input(
                    "Custom End Date",
                    datetime.now(),
                    key="custom_end"
                )
        else:
            # Calculate date range based on period
            if report_period == "Last 7 Days":
                custom_start = datetime.now() - timedelta(days=7)
                custom_end = datetime.now()
            elif report_period == "Last 30 Days":
                custom_start = datetime.now() - timedelta(days=30)
                custom_end = datetime.now()
            else:  # Last 90 Days
                custom_start = datetime.now() - timedelta(days=90)
                custom_end = datetime.now()
        
        if st.button("📄 Generate Report", use_container_width=True):
            with st.spinner("Generating compliance report..."):
                response = client.get_compliance_report(
                    report_type=report_type.lower().replace(" ", "_"),
                    start_date=custom_start.isoformat(),
                    end_date=custom_end.isoformat()
                )
                
                if "error" in response:
                    show_error_message("Error", response.get("error"))
                else:
                    report = response
                    
                    st.markdown(f"### {report_type} Compliance Report")
                    st.markdown(f"**Period:** {custom_start.date()} to {custom_end.date()}")
                    
                    st.divider()
                    
                    # Report summary
                    st.markdown("#### Summary")
                    
                    summary = report.get("summary", {})
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Events", summary.get("total_events", 0))
                    
                    with col2:
                        st.metric("Unique Users", summary.get("unique_users", 0))
                    
                    with col3:
                        st.metric("Failed Actions", summary.get("failed_actions", 0))
                    
                    with col4:
                        st.metric("Exceptions", summary.get("exceptions", 0))
                    
                    st.divider()
                    
                    # Detailed findings
                    st.markdown("#### Key Findings")
                    
                    findings = report.get("findings", [])
                    if findings:
                        for i, finding in enumerate(findings, 1):
                            with st.expander(f"{i}. {finding.get('title', 'Finding')}"):
                                st.write(finding.get("description", "No description"))
                                
                                if finding.get("recommendation"):
                                    st.info(f"**Recommendation:** {finding.get('recommendation')}")
                    else:
                        st.info("No significant findings in this period")
                    
                    st.divider()
                    
                    # Export report
                    st.markdown("#### Export")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("📥 Download as CSV", use_container_width=True):
                            # Convert report to CSV format
                            import csv
                            import io
                            
                            csv_buffer = io.StringIO()
                            writer = csv.DictWriter(csv_buffer, fieldnames=["Metric", "Value"])
                            writer.writeheader()
                            
                            for key, value in summary.items():
                                writer.writerow({"Metric": key, "Value": value})
                            
                            st.download_button(
                                "Click to Download",
                                csv_buffer.getvalue(),
                                f"compliance_report_{report_type.lower().replace(' ', '_')}.csv",
                                "text/csv"
                            )
                    
                    with col2:
                        if st.button("📤 Download as JSON", use_container_width=True):
                            import json
                            
                            json_str = json.dumps(report, indent=2)
                            st.download_button(
                                "Click to Download",
                                json_str,
                                f"compliance_report_{report_type.lower().replace(' ', '_')}.json",
                                "application/json"
                            )


if __name__ == "__main__":
    main()
