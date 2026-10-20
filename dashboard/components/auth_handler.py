"""
Authentication Handler
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from components.api_client import APIClient
from config import API_BASE_URL, SESSION_TIMEOUT_MINUTES, UserRole, ROLE_PERMISSIONS


class AuthHandler:
    """Handles authentication and authorization."""

    @staticmethod
    def initialize_session_state():
        """Initialize session state variables."""
        if "token" not in st.session_state:
            st.session_state.token = None
        if "user" not in st.session_state:
            st.session_state.user = None
        if "last_activity" not in st.session_state:
            st.session_state.last_activity = datetime.now()
        if "login_attempts" not in st.session_state:
            st.session_state.login_attempts = 0
        if "locked_until" not in st.session_state:
            st.session_state.locked_until = None

    @staticmethod
    def check_session_timeout() -> bool:
        """Check if session has timed out."""
        if st.session_state.token is None:
            return False

        last_activity = st.session_state.get("last_activity")
        if last_activity and isinstance(last_activity, datetime):
            elapsed = datetime.now() - last_activity
            if elapsed > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                AuthHandler.logout()
                st.warning(f"Session expired after {SESSION_TIMEOUT_MINUTES} minutes of inactivity.")
                return False

        st.session_state.last_activity = datetime.now()
        return True

    @staticmethod
    def login(email: str, password: str) -> bool:
        """Authenticate user with email and password."""
        # Check if account is locked
        if st.session_state.locked_until:
            if datetime.now() < st.session_state.locked_until:
                st.error("Account locked due to too many login attempts. Please try again later.")
                return False
            else:
                st.session_state.locked_until = None
                st.session_state.login_attempts = 0

        if not email or not password:
            st.error("Please enter both email and password.")
            return False

        client = APIClient(base_url=API_BASE_URL)
        response = client.login(email, password)

        if "error" in response:
            st.session_state.login_attempts += 1

            from config import MAX_LOGIN_ATTEMPTS, LOCKOUT_DURATION_MINUTES

            if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
                st.session_state.locked_until = datetime.now() + timedelta(
                    minutes=LOCKOUT_DURATION_MINUTES
                )
                st.error(
                    f"Too many failed attempts. Account locked for {LOCKOUT_DURATION_MINUTES} minutes."
                )
            else:
                remaining = MAX_LOGIN_ATTEMPTS - st.session_state.login_attempts
                st.error(f"Login failed: {response.get('error')}. ({remaining} attempts remaining)")
            return False

        if "access_token" in response:
            st.session_state.token = response["access_token"]
            st.session_state.login_attempts = 0
            st.session_state.locked_until = None

            # Fetch user info
            client.set_token(st.session_state.token)
            user_response = client.get_current_user()

            if "error" not in user_response:
                st.session_state.user = user_response
                st.session_state.last_activity = datetime.now()
                return True
            else:
                st.error("Could not fetch user information.")
                st.session_state.token = None
                return False

        st.error("Invalid response from authentication service.")
        return False

    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is currently authenticated."""
        AuthHandler.initialize_session_state()
        return st.session_state.token is not None and AuthHandler.check_session_timeout()

    @staticmethod
    def get_current_user() -> Optional[Dict[str, Any]]:
        """Get current authenticated user."""
        if AuthHandler.is_authenticated():
            return st.session_state.user
        return None

    @staticmethod
    def get_user_role() -> Optional[str]:
        """Get current user's role."""
        user = AuthHandler.get_current_user()
        if user:
            return user.get("role", UserRole.VIEWER)
        return None

    @staticmethod
    def get_user_email() -> Optional[str]:
        """Get current user's email."""
        user = AuthHandler.get_current_user()
        if user:
            return user.get("email")
        return None

    @staticmethod
    def has_permission(permission: str) -> bool:
        """Check if user has specific permission."""
        role = AuthHandler.get_user_role()
        if not role:
            return False

        permissions = ROLE_PERMISSIONS.get(role, [])
        return permission in permissions

    @staticmethod
    def can_access_page(page_roles: list) -> bool:
        """Check if user can access page based on roles."""
        role = AuthHandler.get_user_role()
        if not role:
            return False
        return role in page_roles

    @staticmethod
    def logout():
        """Logout current user."""
        if st.session_state.token:
            client = APIClient(base_url=API_BASE_URL, token=st.session_state.token)
            client.logout()

        st.session_state.token = None
        st.session_state.user = None
        st.session_state.last_activity = None
        st.rerun()

    @staticmethod
    def get_api_client() -> APIClient:
        """Get configured API client with current user's token."""
        token = st.session_state.token if st.session_state.token else None
        return APIClient(base_url=API_BASE_URL, token=token)
