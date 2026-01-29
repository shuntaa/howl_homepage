import streamlit as st

st.set_page_config(
    page_title="Howl Official",
    page_icon="🐺",
)

# 起動時は Home にリダイレクト（空のメイン画面を避ける）
st.switch_page("pages/0_Home.py")