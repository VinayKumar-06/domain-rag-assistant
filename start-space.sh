#!/usr/bin/env sh
set -eu
uvicorn app.api.main:app --host 127.0.0.1 --port 8000 &
exec streamlit run ui/streamlit_app.py --server.address 0.0.0.0 --server.port 7860 --server.headless true
