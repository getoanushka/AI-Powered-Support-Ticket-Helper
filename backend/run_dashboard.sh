#!/bin/bash
cd /app/backend
export REACT_APP_BACKEND_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
streamlit run streamlit_dashboard.py --server.port 8501 --server.address 0.0.0.0