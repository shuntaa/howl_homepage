import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pages._db import init_connection

st.title("🐺 人狼サークルHowlへようこそ")

try:
    supabase = init_connection()
except Exception:
    supabase = None

st.header("About Us")

# イントロダクション
st.subheader("Welcome to Howl ~ 人狼をもっと身近に、もっと楽しく ~")
st.write("""
慶應義塾大学を拠点に活動する人狼サークル「Howl」は、
「誰もが熱中できる居場所」を目指して活動しています。
""")

st.write("")
st.write("")

# 3つの特徴をカラムで表示
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### 🔰 初心者大歓迎")
    st.write("""
    現在、メンバーの多くが未経験からのスタートです。
    ルールから丁寧に教えるので、初めての方も安心して参加できます。
    """)
with col2:
    st.markdown("### 📈 圧倒的な上達")
    st.write("""
    経験豊富な上級者と一緒にプレイすることで、
    議論のコツや心理戦のノウハウが自然と身につきます。
    """)
with col3:
    st.markdown("### 🏠 アットホーム")
    st.write("""
    学年や経験を問わず、和気あいあいとした雰囲気。
    対戦が終われば、みんなで感想戦や雑談で盛り上がる温かいコミュニティです。
    """)

st.write("---")

# 活動の様子（Vlog/画像）
st.subheader("🎥 Activity Highlights")
st.write("サークルの日常やイベントの様子をチェック！")

# 実際のYouTube URLがある場合はここにIDを入れてください
# なければ st.info 等で「SNSで動画公開中」としてもOKで
video_url = "https://www.youtube.com/watch?v=XEuJA7aBU7o?si=rz_wuIdFizNyf4ww" 
st.video(video_url)

# 入会案内
st.success("✨ Howlでは新しい仲間を随時募集しています！少しでも興味を持ったら、下記のSNSリンクからお気軽にご連絡ください。")

st.subheader("🔗 Our Social Media")

st.markdown("🔗 [公式Line](https://line.me/R/ti/p/@290bixgt)")
st.markdown("🔗 [Instagram](https://www.instagram.com/keio_howl)")
st.markdown("🔗 [X (Twitter)](https://x.com/keio_howl?s=21&t=TriTKMLwbruJApWYrQQ3eA)")
st.markdown("🔗 [YouTube](https://youtube.com/channel/UCpXfFc7T2f0tG6mBApIfnlA?si=QqCmmo-xRIMLsGMq)")