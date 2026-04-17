import streamlit as st


def show_dev_warning():
    if st.secrets.get("ENVIRONMENT", "production") == "development":
        st.error("⚠️ 【開発環境】現在プレビュー版を表示しています。この画面のURLをメンバーに共有しないでください。")
