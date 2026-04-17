import streamlit as st


def show_dev_warning():
    current_env = str(st.secrets.get("ENVIRONMENT", "production")).strip().lower()
    if current_env in {"development", "develop", "dev"}:
        st.error("⚠️ 【開発環境】現在プレビュー版を表示しています。この画面のURLをメンバーに共有しないでください。")
