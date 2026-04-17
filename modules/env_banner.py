import streamlit as st
import os


def show_dev_warning():
    # secrets.toml と環境変数の両方に対応
    raw_env = (
        st.secrets.get("ENVIRONMENT")
        or st.secrets.get("environment")
        or os.getenv("ENVIRONMENT")
        or os.getenv("STREAMLIT_ENV")
        or "production"
    )
    current_env = str(raw_env).strip().lower()
    if current_env in {"development", "develop", "dev"}:
        st.error("⚠️ 【開発環境】現在プレビュー版を表示しています。この画面のURLをメンバーに共有しないでください。")
