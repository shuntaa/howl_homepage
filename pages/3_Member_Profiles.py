import streamlit as st
from modules.env_banner import show_dev_warning

show_dev_warning()

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
        "message": "人狼ゲームをここ慶應で展開したい!そんな思いで2023年にHowlを設立しました。卒業までにどんどん改革していきます！"
    },
    {
        "role": "2期代表",
        "name": "山本 祐大(やまもと ゆうだい)",
        "image": "img/member_yamayu.webp",
        "message": "更新予定✨"
    },
    {
        "role": "3期代表",
        "name": "???",
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
        # ① 役職の描画: st.captionの曖昧な仕様を捨て、明示的な最小ヘッダー(h6)として定義
        if "role" in member and member["role"]:
            st.markdown(f"###### {member['role']}") 
            
        # ② 名前の描画: 役職との階層構造を明確にするため中ヘッダー(h4)を維持
        st.markdown(f"#### {member['name']}")
        
        # ③ 画像とメッセージの描画
        st.image(member["image"], use_container_width=True)
        st.info(member["message"])
        st.write("") # メンバー間の余白
