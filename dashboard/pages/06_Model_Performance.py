"""
Model Performance Page
"""
import streamlit as st
from datetime import datetime, timedelta
from components import (
    AuthHandler,
    create_bar_chart,
    create_line_chart,
    display_chart_with_error_handling,
    display_empty_state,
)
from utils import show_error_message, format_percentage


def main():
    """Main model performance page."""
    
    # Check authentication
    if not AuthHandler.is_authenticated():
        st.error("Please login to access this page")
        return
    
    if not AuthHandler.has_permission("view_models"):
        st.error("You don't have permission to view this page")
        return
    
    client = AuthHandler.get_api_client()
    
    st.markdown("## 🤖 Model Performance")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["Current Model", "Training History", "Model Comparison"])
    
    with tab1:
        st.markdown("### Current Model Metrics")
        
        # Model selector
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Load Model Metrics", use_container_width=True):
                with st.spinner("Loading model metrics..."):
                    response = client.get_model_metrics()
                    
                    if "error" in response:
                        show_error_message("Error", response.get("error"))
                    else:
                        st.session_state.current_model = response
        
        if "current_model" in st.session_state:
            model = st.session_state.current_model
            
            st.markdown(f"**Model Version:** {model.get('version', 'Unknown')}")
            st.markdown(f"**Trained:** {model.get('training_date', 'Unknown')}")
            
            st.divider()
            
            # Metrics cards
            col1, col2, col3, col4 = st.columns(4)
            
            metrics = model.get("metrics", {})
            
            with col1:
                st.metric(
                    "Accuracy",
                    format_percentage(metrics.get("accuracy", 0))
                )
            
            with col2:
                st.metric(
                    "Precision",
                    format_percentage(metrics.get("precision", 0))
                )
            
            with col3:
                st.metric(
                    "Recall",
                    format_percentage(metrics.get("recall", 0))
                )
            
            with col4:
                st.metric(
                    "F1 Score",
                    format_percentage(metrics.get("f1_score", 0))
                )
            
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "ROC-AUC",
                    f"{metrics.get('roc_auc', 0):.3f}"
                )
            
            with col2:
                st.metric(
                    "Dataset Size",
                    f"{model.get('dataset_size', 0):,}"
                )
            
            st.divider()
            
            # Confusion Matrix
            st.markdown("### Confusion Matrix")
            
            confusion = model.get("confusion_matrix", {})
            if confusion:
                cm_data = [
                    {"Predicted": "Positive", "Actual Positive": confusion.get("tp", 0), "Actual Negative": confusion.get("fp", 0)},
                    {"Predicted": "Negative", "Actual Positive": confusion.get("fn", 0), "Actual Negative": confusion.get("tn", 0)},
                ]
                
                import pandas as pd
                cm_df = pd.DataFrame(cm_data).set_index("Predicted")
                st.dataframe(cm_df, use_container_width=True)
            
            st.divider()
            
            # Feature Importance
            st.markdown("### Feature Importance")
            
            features = model.get("feature_importance", [])
            if features:
                # Sort by importance
                features = sorted(features, key=lambda x: x.get("importance", 0), reverse=True)[:10]
                
                display_chart_with_error_handling(
                    create_bar_chart,
                    features,
                    "Top 10 Important Features",
                    "feature_name",
                    "importance",
                    "Feature",
                    "Importance Score",
                    horizontal=True
                )
            else:
                display_empty_state("No feature importance data available")
    
    with tab2:
        st.markdown("### Training History")
        
        # Load options
        col1, col2 = st.columns(2)
        
        with col1:
            limit = st.number_input(
                "Number of Versions",
                min_value=5,
                max_value=50,
                value=10,
                key="history_limit"
            )
        
        with col2:
            if st.button("🔄 Load History", use_container_width=True):
                with st.spinner("Loading training history..."):
                    response = client.get_model_training_history(limit=limit)
                    
                    if "error" in response:
                        show_error_message("Error", response.get("error"))
                    else:
                        st.session_state.model_history = response.get("items", [])
        
        if "model_history" in st.session_state:
            history = st.session_state.model_history
            
            if not history:
                display_empty_state("No training history available")
            else:
                st.markdown(f"### {len(history)} Model Version(s)")
                
                # Create table
                import pandas as pd
                history_data = []
                for h in history:
                    history_data.append({
                        "Version": h.get("version", "-"),
                        "Training Date": h.get("training_date", "-"),
                        "Accuracy": format_percentage(h.get("accuracy", 0)),
                        "Precision": format_percentage(h.get("precision", 0)),
                        "Recall": format_percentage(h.get("recall", 0)),
                        "Dataset Size": f"{h.get('dataset_size', 0):,}"
                    })
                
                df = pd.DataFrame(history_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                st.divider()
                
                # Accuracy trend
                st.markdown("### Accuracy Trend Over Time")
                
                trend_data = [
                    {
                        "version": h.get("version", "-"),
                        "accuracy": h.get("accuracy", 0)
                    }
                    for h in reversed(history)
                ]
                
                display_chart_with_error_handling(
                    create_line_chart,
                    trend_data,
                    "Model Accuracy Trend",
                    "version",
                    "accuracy",
                    "Model Version",
                    "Accuracy"
                )
    
    with tab3:
        st.markdown("### Compare Models")
        
        if "model_history" not in st.session_state:
            st.info("Load training history from the 'Training History' tab first")
        else:
            history = st.session_state.model_history
            
            if len(history) < 2:
                st.warning("At least 2 models needed for comparison")
            else:
                col1, col2 = st.columns(2)
                
                versions = [h.get("version", "") for h in history]
                
                with col1:
                    model1_idx = st.selectbox(
                        "Model 1",
                        range(len(versions)),
                        format_func=lambda x: versions[x],
                        key="compare_model1"
                    )
                
                with col2:
                    model2_idx = st.selectbox(
                        "Model 2",
                        range(len(versions)),
                        format_func=lambda x: versions[x],
                        index=min(1, len(versions)-1) if len(versions) > 1 else 0,
                        key="compare_model2"
                    )
                
                if st.button("Compare Models", use_container_width=True):
                    model1 = history[model1_idx]
                    model2 = history[model2_idx]
                    
                    st.markdown("### Metrics Comparison")
                    
                    import pandas as pd
                    
                    comparison_data = {
                        "Metric": ["Accuracy", "Precision", "Recall", "F1 Score", "ROC-AUC"],
                        model1.get("version", "Model 1"): [
                            format_percentage(model1.get("accuracy", 0)),
                            format_percentage(model1.get("precision", 0)),
                            format_percentage(model1.get("recall", 0)),
                            format_percentage(model1.get("f1_score", 0)),
                            f"{model1.get('roc_auc', 0):.3f}"
                        ],
                        model2.get("version", "Model 2"): [
                            format_percentage(model2.get("accuracy", 0)),
                            format_percentage(model2.get("precision", 0)),
                            format_percentage(model2.get("recall", 0)),
                            format_percentage(model2.get("f1_score", 0)),
                            f"{model2.get('roc_auc', 0):.3f}"
                        ]
                    }
                    
                    comp_df = pd.DataFrame(comparison_data)
                    st.dataframe(comp_df, use_container_width=True, hide_index=True)
                    
                    # Highlight improvement
                    st.markdown("### Performance Change")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    accuracy_diff = model2.get("accuracy", 0) - model1.get("accuracy", 0)
                    precision_diff = model2.get("precision", 0) - model1.get("precision", 0)
                    recall_diff = model2.get("recall", 0) - model1.get("recall", 0)
                    
                    with col1:
                        st.metric(
                            "Accuracy Change",
                            f"{accuracy_diff:+.2%}",
                            "better" if accuracy_diff > 0 else "worse"
                        )
                    
                    with col2:
                        st.metric(
                            "Precision Change",
                            f"{precision_diff:+.2%}",
                            "better" if precision_diff > 0 else "worse"
                        )
                    
                    with col3:
                        st.metric(
                            "Recall Change",
                            f"{recall_diff:+.2%}",
                            "better" if recall_diff > 0 else "worse"
                        )


if __name__ == "__main__":
    main()
