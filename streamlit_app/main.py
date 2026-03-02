import os

import requests
import streamlit as st


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def main() -> None:
    st.set_page_config(
        page_title="Publication Assistant",
        layout="wide",
    )
    st.title("Publication Assistant for AI Projects")
    st.write(
        "Paste your draft or upload a file and let the multi-agent assistant "
        "analyze clarity, structure, technical soundness, visuals, summary, and tags."
    )

    tab_text, tab_file = st.tabs(["Paste text", "Upload file"])

    with tab_text:
        content = st.text_area("Document content", height=400)
        run = st.button("Analyze text")
        if run and content.strip():
            payload = {
                "document": {
                    "content": content,
                    "content_type": "markdown",
                    "source": "text",
                }
            }
            with st.spinner("Running analysis..."):
                resp = requests.post(f"{BACKEND_URL}/api/v1/analyze", json=payload)
            if resp.ok:
                show_result(resp.json())
            else:
                st.error(f"Backend error: {resp.status_code} - {resp.text}")

    with tab_file:
        uploaded = st.file_uploader("Upload a markdown / text file", type=["md", "txt"])
        run_file = st.button("Analyze file")
        if run_file and uploaded is not None:
            files = {"file": uploaded}
            data = {"content_type": "markdown"}
            with st.spinner("Running analysis..."):
                resp = requests.post(
                    f"{BACKEND_URL}/api/v1/analyze/file", data=data, files=files
                )
            if resp.ok:
                show_result(resp.json())
            else:
                st.error(f"Backend error: {resp.status_code} - {resp.text}")


def show_result(payload: dict) -> None:
    result = payload.get("result") or {}

    st.subheader("Guardrails")
    guardrails = result.get("guardrails")
    st.json(guardrails or {})

    cols = st.columns(3)

    with cols[0]:
        clarity = result.get("clarity")
        st.subheader("Clarity")
        if clarity:
            st.markdown("**Improved text**")
            st.write(clarity.get("improved_text", ""))
            st.markdown("**Comments**")
            for c in clarity.get("comments", []):
                st.markdown(f"- {c}")

        structure = result.get("structure")
        st.subheader("Structure")
        if structure:
            st.markdown("**Suggested outline**")
            for s in structure.get("suggested_outline", []):
                st.markdown(f"- {s}")
            st.markdown("**Section suggestions**")
            for s in structure.get("section_suggestions", []):
                st.markdown(f"- {s}")

    with cols[1]:
        technical = result.get("technical")
        st.subheader("Technical review")
        if technical:
            st.markdown("**Issues found**")
            for i in technical.get("issues_found", []):
                st.markdown(f"- {i}")
            st.markdown("**Suggestions**")
            for s in technical.get("suggestions", []):
                st.markdown(f"- {s}")

        visuals = result.get("visuals")
        st.subheader("Visual suggestions")
        if visuals:
            for v in visuals.get("suggestions", []):
                st.markdown(f"**{v.get('title', '')}** ({v.get('type', '')})")
                st.write(v.get("description", ""))
            st.markdown("**Formatting tips**")
            for t in visuals.get("formatting_tips", []):
                st.markdown(f"- {t}")

    with cols[2]:
        summary = result.get("summary")
        st.subheader("Summary")
        if summary:
            st.markdown("**Abstract**")
            st.write(summary.get("summary", ""))
            st.markdown("**Key contributions**")
            for c in summary.get("key_contributions", []):
                st.markdown(f"- {c}")

        tags = result.get("tags")
        st.subheader("Titles & tags")
        if tags:
            st.markdown("**Title suggestions**")
            for t in tags.get("title_suggestions", []):
                st.markdown(f"- {t}")
            st.markdown("**Tags**")
            st.write(", ".join(tags.get("tags", [])))


if __name__ == "__main__":
    main()

