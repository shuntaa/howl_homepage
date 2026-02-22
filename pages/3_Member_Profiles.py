import streamlit as st

st.header("👥 Member Profiles")
st.write("Howlの歴代代表を紹介します。")
st.write("") # スペース

# 1. メンバーデータの定義 (将来的にここを増やすだけでOK)
# 写真は URL または ローカルのパスを指定します
members = [
    {
        "role": "初代代表",
        "name": "土居 隼大(どい しゅんた)",
        "image": "img/member_shunta.JPEG", # サンプル画像URL
        "message": "人狼ゲームをここ慶應で展開したい!そんな思いで2023年にHowlを設立しました。今後のHowl存続を願って、卒業までにどんどん改革していきます！"
    },
    {
        "role": "2期代表",
        "name": "山本 祐大(やまもと ゆうだい)",
        "image": "img/member_yamayu.webp",
        "message": "更新予定✨"
    },
    {
        "role": "3期代表",
        "name": "泉 凛汰朗(いずみ　りんたろう)",
        "image": "https://via.placeholder.com/150",
        "message": "更新予定✨"
    }
]

# 2. 表示（3列構成でループ）
# リストを3つずつの塊（chunk）に分けて表示
cols = st.columns(3)

for i, member in enumerate(members):
    col_idx = i % 3 # 0, 1, 2 のインデックスを繰り返す
    with cols[col_idx]:
        # 名前を強調
        st.subheader(member["name"])
        # 写真を表示 (use_container_widthで枠に合わせる)
        st.image(member["image"], use_container_width=True)
        # メッセージ
        st.info(member["message"])
        st.write("") # メンバー間の余白
