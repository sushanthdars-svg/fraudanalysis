"""
User Management Page (Admin Only)
"""
import streamlit as st
from components import (
    AuthHandler,
    create_user_table,
    display_user_detail,
    display_empty_state,
)
from utils import show_error_message, show_success_message


def main():
    """Main user management page."""
    
    # Check authentication
    if not AuthHandler.is_authenticated():
        st.error("Please login to access this page")
        return
    
    # Check admin role
    if not AuthHandler.has_permission("manage_users"):
        st.error("You don't have permission to manage users")
        return
    
    client = AuthHandler.get_api_client()
    
    st.markdown("## 👥 User Management")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["Users List", "Create User", "View Details"])
    
    with tab1:
        st.markdown("### All Users")
        
        # Load users button
        if st.button("🔄 Refresh Users", use_container_width=True):
            with st.spinner("Loading users..."):
                response = client.get_users()
                
                if "error" in response:
                    show_error_message("Error", response.get("error"))
                else:
                    st.session_state.users = response.get("items", [])
        
        if "users" in st.session_state:
            users = st.session_state.users
            
            if not users:
                display_empty_state("No users found")
            else:
                st.markdown(f"### {len(users)} User(s)")
                
                # Create users table
                user_table = create_user_table(users)
                st.dataframe(user_table, use_container_width=True, hide_index=True)
                
                # Quick actions
                st.markdown("### Actions")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    selected_user_id = st.selectbox(
                        "Select user",
                        [u.get("id", "") for u in users],
                        format_func=lambda x: next(
                            (u.get("email", x) for u in users if u.get("id") == x),
                            x
                        ),
                        key="select_user"
                    )
                
                with col2:
                    action = st.selectbox(
                        "Action",
                        ["View", "Edit", "Deactivate", "Delete"],
                        key="user_action"
                    )
                
                if st.button("Execute Action", use_container_width=True):
                    if action == "View":
                        st.session_state.selected_user_id = selected_user_id
                    
                    elif action == "Edit":
                        st.session_state.edit_user_id = selected_user_id
                    
                    elif action == "Deactivate":
                        with st.spinner("Deactivating user..."):
                            result = client.update_user(
                                selected_user_id,
                                {"active": False}
                            )
                            if "error" not in result:
                                show_success_message("Success", "User deactivated")
                                st.session_state.users = None
                                st.rerun()
                            else:
                                show_error_message("Error", result.get("error"))
                    
                    elif action == "Delete":
                        with st.spinner("Deleting user..."):
                            result = client.delete_user(selected_user_id)
                            if "error" not in result:
                                show_success_message("Success", "User deleted")
                                st.session_state.users = None
                                st.rerun()
                            else:
                                show_error_message("Error", result.get("error"))
    
    with tab2:
        st.markdown("### Create New User")
        
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input(
                "Email",
                placeholder="user@example.com",
                key="new_email"
            )
            password = st.text_input(
                "Initial Password",
                type="password",
                placeholder="At least 8 characters",
                key="new_password"
            )
        
        with col2:
            role = st.selectbox(
                "Role",
                ["Viewer", "Analyst", "Admin"],
                key="new_role"
            )
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                key="confirm_password"
            )
        
        full_name = st.text_input(
            "Full Name",
            placeholder="John Doe",
            key="new_name"
        )
        
        department = st.text_input(
            "Department",
            placeholder="Fraud Detection",
            key="new_dept"
        )
        
        send_invite = st.checkbox(
            "Send welcome email",
            value=True,
            key="send_invite"
        )
        
        if st.button("✅ Create User", use_container_width=True):
            # Validation
            if not email or not password:
                st.error("Email and password are required")
            elif password != confirm_password:
                st.error("Passwords don't match")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters")
            else:
                with st.spinner("Creating user..."):
                    result = client.create_user({
                        "email": email,
                        "password": password,
                        "role": role.lower(),
                        "full_name": full_name,
                        "department": department,
                        "active": True
                    })
                    
                    if "error" not in result:
                        show_success_message("Success", f"User {email} created")
                        st.session_state.users = None
                        # Clear form
                        for key in ["new_email", "new_password", "new_name", "new_dept"]:
                            if key in st.session_state:
                                del st.session_state[key]
                    else:
                        show_error_message("Error", result.get("error"))
    
    with tab3:
        st.markdown("### User Details")
        
        if "selected_user_id" in st.session_state:
            user_id = st.session_state.selected_user_id
            
            with st.spinner("Loading user details..."):
                response = client.get_user(user_id)
                
                if "error" in response:
                    show_error_message("Error", response.get("error"))
                else:
                    user = response
                    
                    # Display user details
                    display_user_detail(user)
                    
                    st.divider()
                    
                    # Activity log
                    st.markdown("### Recent Activity")
                    
                    activity = user.get("activity", [])
                    if activity:
                        import pandas as pd
                        
                        activity_data = []
                        for a in activity[-10:]:  # Last 10 activities
                            activity_data.append({
                                "Timestamp": a.get("timestamp", "-"),
                                "Action": a.get("action", "-"),
                                "Resource": a.get("resource", "-"),
                                "Status": a.get("status", "-")
                            })
                        
                        df = pd.DataFrame(activity_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No activity recorded")
                    
                    st.divider()
                    
                    # Edit user
                    if "edit_user_id" in st.session_state and st.session_state.edit_user_id == user_id:
                        st.markdown("### Edit User")
                        
                        new_role = st.selectbox(
                            "Role",
                            ["Viewer", "Analyst", "Admin"],
                            index=["Viewer", "Analyst", "Admin"].index(
                                user.get("role", "Viewer").capitalize()
                            ),
                            key="edit_role"
                        )
                        
                        new_active = st.checkbox(
                            "Active",
                            value=user.get("active", True),
                            key="edit_active"
                        )
                        
                        if st.button("💾 Save Changes", use_container_width=True):
                            with st.spinner("Updating user..."):
                                result = client.update_user(user_id, {
                                    "role": new_role.lower(),
                                    "active": new_active
                                })
                                
                                if "error" not in result:
                                    show_success_message("Success", "User updated")
                                    st.session_state.users = None
                                    st.session_state.edit_user_id = None
                                    st.rerun()
                                else:
                                    show_error_message("Error", result.get("error"))
        else:
            st.info("Select a user from the Users List tab to view details")


if __name__ == "__main__":
    main()
