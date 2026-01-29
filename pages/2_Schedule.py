import streamlit as st
from datetime import date

st.header("📅 Schedule / Next Game")

# 次回イベントまでのカウントダウン
event_date = date(2026, 2, 16)  # ユーザーから提供されたイベント日付
today = date.today()
days_until_event = (event_date - today).days

if days_until_event > 0:
    st.subheader(f"次のイベントまであと... {days_until_event} 日！ 🎉")
elif days_until_event == 0:
    st.subheader("本日イベント開催！お見逃しなく！🎉")
else:
    st.subheader("イベントは終了しました。次回のイベントをお楽しみに！")

st.write("---")

# Google Calendar Embed
st.write("### 次回活動予定")
st.components.v1.html('<iframe src="https://calendar.google.com/calendar/embed?src=keiowerewolf.howl%40gmail.com&ctz=Asia%2FTokyo" style="border: 0" width="800" height="600" frameborder="0" scrolling="no"></iframe>', height=600)
