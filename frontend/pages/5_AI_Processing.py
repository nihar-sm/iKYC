import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from utils.api_client import api_client

st.header("🤖 AI Processing & Fraud Detection")

# Document processing logic similar to show_ai_processing_page() above
# This allows the page to be used standalone or as part of main app
