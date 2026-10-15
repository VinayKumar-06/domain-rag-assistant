"""Simple browser UI; set API_URL to reach the FastAPI service."""

import os
from pathlib import Path

import httpx
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
HERO_IMAGE = Path(__file__).resolve().parents[1] / "assets" / "research-assistant-hero.webp"
st.set_page_config(page_title="Research RAG Assistant", page_icon="📚", layout="wide")
intro, artwork = st.columns([1.15, 1], vertical_alignment="center")
with intro:
    st.title("📚 Research Document Assistant")
    st.caption("Ask questions grounded in your indexed papers, documentation, and notes.")
with artwork:
    st.image(
        str(HERO_IMAGE),
        caption="Documents → retrieved evidence → cited answers",
        use_container_width=True,
    )

with st.container(border=True):
    steps = st.columns(3)
    for column, number, title, detail in zip(
        steps,
        ("01", "02", "03"),
        ("Add documents", "Find evidence", "Review sources"),
        (
            "Upload PDF, TXT, or Markdown files in the sidebar.",
            "Ask a question and retrieve relevant passages.",
            "Open citations to check the supporting text.",
        ),
        strict=True,
    ):
        with column:
            st.markdown(f"### {number} · {title}")
            st.caption(detail)

with st.sidebar:
    st.subheader("Your document library")
    upload = st.file_uploader("Add PDF, TXT, or Markdown", type=["pdf", "txt", "md", "markdown"])
    if upload and st.button("Index document", type="primary"):
        with st.spinner("Reading, chunking, and indexing…"):
            try:
                result = httpx.post(f"{API_URL}/documents", files={"file": (upload.name, upload.getvalue())}, timeout=300)
                result.raise_for_status()
                st.success(f"Indexed {result.json()['chunks_indexed']} passages.")
            except Exception as exc:
                st.error(f"Could not index file: {exc}")
    try:
        docs = httpx.get(f"{API_URL}/documents", timeout=10).json().get("documents", [])
        if docs:
            for doc in docs:
                col, button = st.columns([4, 1])
                col.write(doc["filename"])
                if button.button("×", key=doc["document_id"], help="Remove document"):
                    httpx.delete(f"{API_URL}/documents/{doc['document_id']}", timeout=30).raise_for_status()
                    st.rerun()
        else:
            st.info("No documents indexed yet.")
    except Exception:
        st.warning("API unavailable. Start the backend to manage documents.")

if "messages" not in st.session_state:
    st.session_state.messages = []
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Retrieved passages and citations"):
                for source in message["sources"]:
                    st.markdown(f"**[{source['id']}] {source['filename']} — page {source.get('page') or 'unknown'}**")
                    st.write(source["text"])

question = st.chat_input("Ask a question about your documents")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Searching your indexed documents…"):
            try:
                response = httpx.post(f"{API_URL}/ask", json={"question": question}, timeout=90)
                response.raise_for_status()
                result = response.json()
                st.markdown(result["answer"])
                st.caption(f"{result['latency_ms']} ms")
                if result["sources"]:
                    with st.expander("Retrieved passages and citations"):
                        for source in result["sources"]:
                            st.markdown(f"**[{source['id']}] {source['filename']} — page {source.get('page') or 'unknown'}**")
                            st.write(source["text"])
                st.session_state.messages.append({"role": "assistant", "content": result["answer"], "sources": result["sources"]})
            except Exception as exc:
                st.error(f"The assistant is unavailable: {exc}")
