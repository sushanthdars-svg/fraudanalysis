"""
Main Streamlit Dashboard Application
"""
import streamlit as st
from components.auth_handler import AuthHandler
from config import DASHBOARD_TITLE, PAGES, UserRole

# Page configuration
st.set_page_config(
    page_title=DASHBOARD_TITLE,
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
AuthHandler.initialize_session_state()

# Custom styling
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    .stDataFrame {
        padding: 1rem 0;
    }
    h1 {
        color: #0066CC;
        border-bottom: 2px solid #0066CC;
        padding-bottom: 1rem;
    }
    h2 {
        color: #0066CC;
        margin-top: 1.5rem;
    }
    .error-box {
        background-color: #fee;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #c00;
    }
    .success-box {
        background-color: #efe;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #0c0;
    }
    .info-box {
        background-color: #eef;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #00c;
    }
</style>
""", unsafe_allow_html=True)


def show_login_page():
    """Display login page."""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("# 🔐 Fraud Detection System")
        st.markdown("---")
        
        st.subheader("Login to Dashboard")
        
        email = st.text_input(
            "Email",
            placeholder="admin@example.com",
            key="login_email"
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="••••••••",
            key="login_password"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔓 Login", use_container_width=True):
                with st.spinner("Authenticating..."):
                    if AuthHandler.login(email, password):
                        st.success("Login successful! Redirecting...")
                        st.rerun()
        
        with col2:
            if st.button("ℹ️ Demo Login", use_container_width=True):
                st.info("Demo credentials: admin@example.com / password")


def show_dashboard():
    """Display main dashboard with navigation."""
    # Sidebar
    with st.sidebar:
        st.markdown("# 📊 Navigation")
        
        # User info
        user = AuthHandler.get_current_user()
        if user:
            st.markdown(f"**{user.get('email', 'User')}**")
            st.caption(f"Role: {user.get('role', 'Viewer').title()}")
            st.divider()
        
        # Navigation pages
        page_options = []
        page_files = {}
        
        for page_name, page_info in PAGES.items():
            # Skip login page
            if page_name == "Login":
                continue
            
            # Check role access
            allowed_roles = page_info.get("roles", [])
            if AuthHandler.can_access_page(allowed_roles):
                page_options.append(page_name)
                page_files[page_name] = page_info["file"]
        
        if page_options:
            selected_page = st.selectbox(
                "Select Page",
                page_options,
                key="page_selector"
            )
        else:
            st.warning("No pages available for your role")
            selected_page = None
        
        st.divider()
        
        # Session info
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("🚪 Logout", use_container_width=True):
                AuthHandler.logout()
        
        st.divider()
        
        # Footer
        st.caption("Financial Fraud Detection System v1.0")
        st.caption(f"Session Active: {AuthHandler.check_session_timeout()}")
    
    # Main content
    if not AuthHandler.is_authenticated():
        st.warning("Session expired. Please login again.")
        show_login_page()
        return
    
    if selected_page:
        # Import and run the selected page
        try:
            page_file = page_files[selected_page]
            # Remove the leading "0X_" from filename for module import
            page_module_name = page_file.replace("pages/", "").replace(".py", "")
            
            # Dynamically import page
            import importlib.util
            import os
            
            page_path = os.path.join("dashboard", "pages", page_file)
            
            # For Streamlit, we'll manually call the page's main function
            # Pages are structured as multi-page apps
            st.markdown(f"# {selected_page}")
            
            # Import page content based on file
            if "01_Dashboard" in page_file:
                from pages.dashboard import main as page_main
            elif "02_Transaction" in page_file:
                from pages.transactions import main as page_main
            elif "03_Fraud" in page_file:
                from pages.alerts import main as page_main
            elif "04_Financial" in page_file:
                from pages.risk_analytics import main as page_main
            elif "05_Rule" in page_file:
                from pages.rules import main as page_main
            elif "06_Model" in page_file:
                from pages.models import main as page_main
            elif "07_User" in page_file:
                from pages.users import main as page_main
            elif "08_Audit" in page_file:
                from pages.audit_logs import main as page_main
            else:
                st.error(f"Page {selected_page} not found")
                return
            
            page_main()
        
        except ImportError as e:
            st.error(f"Error loading page: {str(e)}")
        except Exception as e:
            st.error(f"Error: {str(e)}")


# Main app entry point
if __name__ == "__main__":
    if AuthHandler.is_authenticated():
        show_dashboard()
    else:
        show_login_page()
