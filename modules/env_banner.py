import streamlit as st
import os

DEV_ENV_NAMES = {"development", "develop", "dev"}


def resolve_current_env():
    candidates = [
        ("secrets.ENVIRONMENT", st.secrets.get("ENVIRONMENT")),
        ("secrets.environment", st.secrets.get("environment")),
        ("env.ENVIRONMENT", os.getenv("ENVIRONMENT")),
        ("env.STREAMLIT_ENV", os.getenv("STREAMLIT_ENV")),
        ("env.APP_ENV", os.getenv("APP_ENV")),
    ]
    for source, value in candidates:
        if value is None:
            continue
        normalized = str(value).strip().lower()
        if normalized:
            return normalized, source, str(value)
    return "production", "default", "production"


def is_development_env(current_env):
    return current_env in DEV_ENV_NAMES


def show_dev_warning():
    current_env, _, _ = resolve_current_env()
    if is_development_env(current_env):
        st.error("⚠️ 【開発環境】現在プレビュー版を表示しています。この画面のURLをメンバーに共有しないでください。")


def render_env_diagnostics():
    current_env, source, raw_value = resolve_current_env()
    with st.expander("環境判定の診断情報（トラブルシュート用）"):
        st.write(f"- 判定環境: `{current_env}`")
        st.write(f"- 取得元: `{source}`")
        st.write(f"- 生値: `{raw_value}`")
        st.write(f"- 開発警告対象: `{is_development_env(current_env)}`")
