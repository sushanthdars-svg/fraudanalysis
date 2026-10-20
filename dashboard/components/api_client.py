"""
API Client for backend communication
"""
import requests
import streamlit as st
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from config import API_BASE_URL, API_TIMEOUT


class APIClient:
    """Centralized API client for backend communication."""

    def __init__(self, base_url: str = API_BASE_URL, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.session = requests.Session()
        self.timeout = API_TIMEOUT

    def set_token(self, token: str):
        """Set authentication token."""
        self.token = token

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth token."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and errors."""
        try:
            if response.status_code == 401:
                st.error("Authentication failed. Please login again.")
                if "token" in st.session_state:
                    del st.session_state.token
                if "user" in st.session_state:
                    del st.session_state.user
                st.rerun()
            elif response.status_code == 403:
                return {"error": "Access denied. You don't have permission for this action."}
            elif response.status_code == 404:
                return {"error": "Resource not found."}
            elif response.status_code >= 500:
                return {"error": "Server error. Please try again later."}
            elif response.status_code >= 400:
                try:
                    return response.json()
                except:
                    return {"error": f"Request failed: {response.text}"}

            if response.status_code == 204:
                return {"success": True}

            return response.json()
        except Exception as e:
            return {"error": f"Error processing response: {str(e)}"}

    # Authentication Endpoints
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login with email and password."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={"email": email, "password": password},
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Login failed: {str(e)}"}

    def get_current_user(self) -> Dict[str, Any]:
        """Get current authenticated user info."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/auth/me",
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to fetch user: {str(e)}"}

    def logout(self) -> Dict[str, Any]:
        """Logout current user."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/logout",
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Logout failed: {str(e)}"}

    # Transaction Endpoints
    def get_transactions(
        self,
        skip: int = 0,
        limit: int = 20,
        customer_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        merchant_id: Optional[str] = None,
        risk_level: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get transactions with filters."""
        try:
            params = {"skip": skip, "limit": limit}
            if customer_id:
                params["customer_id"] = customer_id
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date
            if min_amount is not None:
                params["min_amount"] = min_amount
            if max_amount is not None:
                params["max_amount"] = max_amount
            if merchant_id:
                params["merchant_id"] = merchant_id
            if risk_level:
                params["risk_level"] = risk_level

            response = self.session.get(
                f"{self.base_url}/api/transactions",
                params=params,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to fetch transactions: {str(e)}"}

    def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Get single transaction with assessment details."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/transactions/{transaction_id}",
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to fetch transaction: {str(e)}"}

    def get_transaction_stats(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get transaction statistics."""
        try:
            params = {}
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date

            response = self.session.get(
                f"{self.base_url}/api/transactions/stats/summary",
                params=params,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to fetch stats: {str(e)}"}

    # Alert Endpoints
    def get_alerts(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        risk_level: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get fraud alerts with filters."""
        try:
            params = {"skip": skip, "limit": limit}
            if status:
                params["status"] = status
            if risk_level:
                params["risk_level"] = risk_level
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date

            response = self.session.get(
                f"{self.base_url}/api/alerts",
                params=params,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to fetch alerts: {str(e)}"}

    def get_alert(self, alert_id: str) -> Dict[str, Any]:
        """Get single alert details."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/alerts/{alert_id}",
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to fetch alert: {str(e)}"}

    def review_alert(
        self,
        alert_id: str,
        decision: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Review and make decision on alert."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/alerts/{alert_id}/review",
                json={"decision": decision, "notes": notes},
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to review alert: {str(e)}"}

    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/alerts/stats/summary",
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to fetch alert stats: {str(e)}"}

    # Rule Endpoints
    def get_fraud_rules(self) -> Dict[str, Any]:
        """Get all fraud detection rules."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/rules",
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to fetch rules: {str(e)}"}

    def get_rule(self, rule_id: str) -> Dict[str, Any]:
        """Get single rule details."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/rules/{rule_id}",
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to fetch rule: {str(e)}"}

    def create_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new fraud rule."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/rules",
                json=rule_data,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to create rule: {str(e)}"}

    def update_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing fraud rule."""
        try:
            response = self.session.put(
                f"{self.base_url}/api/rules/{rule_id}",
                json=rule_data,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to update rule: {str(e)}"}

    def delete_rule(self, rule_id: str) -> Dict[str, Any]:
        """Delete (soft) fraud rule."""
        try:
            response = self.session.delete(
                f"{self.base_url}/api/rules/{rule_id}",
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to delete rule: {str(e)}"}

    # Model Endpoints
    def get_models(self) -> Dict[str, Any]:
        """Get all models."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/models",
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to fetch models: {str(e)}"}

    def get_model_metrics(self, model_id: str) -> Dict[str, Any]:
        """Get model performance metrics."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/models/{model_id}/metrics",
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to fetch model metrics: {str(e)}"}

    # User Endpoints
    def get_users(self, skip: int = 0, limit: int = 20) -> Dict[str, Any]:
        """Get all users."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/users",
                params={"skip": skip, "limit": limit},
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to fetch users: {str(e)}"}

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/users",
                json=user_data,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to create user: {str(e)}"}

    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information."""
        try:
            response = self.session.put(
                f"{self.base_url}/api/users/{user_id}",
                json=user_data,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to update user: {str(e)}"}

    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete user."""
        try:
            response = self.session.delete(
                f"{self.base_url}/api/users/{user_id}",
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to delete user: {str(e)}"}

    # Audit Log Endpoints
    def get_audit_logs(
        self,
        skip: int = 0,
        limit: int = 50,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get audit logs with filters."""
        try:
            params = {"skip": skip, "limit": limit}
            if actor:
                params["actor"] = actor
            if action:
                params["action"] = action
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date

            response = self.session.get(
                f"{self.base_url}/api/audit-logs",
                params=params,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to fetch audit logs: {str(e)}"}

    # Customer Risk Endpoints
    def get_customer_risk_profile(self, customer_id: str) -> Dict[str, Any]:
        """Get customer risk profile."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/customers/{customer_id}/risk-profile",
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to fetch customer profile: {str(e)}"}

    def get_transaction_patterns(self) -> Dict[str, Any]:
        """Get transaction patterns and analytics."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/analytics/patterns",
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            return {"error": f"Failed to fetch patterns: {str(e)}"}
