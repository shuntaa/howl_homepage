import streamlit as st
from pages._db import init_connection
import datetime

st.set_page_config(page_title="入部申請", page_icon="📝")

st.header("📝 Howl 入部申請フォーム")

# 案内文
st.info("""
**【重要】入部手続きの流れ**
1. 指定の口座に入部費（¥5,000）を振り込んでください。
2. 以下のフォームに情報を入力して申請してください。
3. 会計担当が入金を確認後、正式にメンバーリストに追加されます。
""")

# DB接続
try:
    supabase = init_connection()
except Exception as e:
    st.error(f"データベース接続エラー: {e}")
    st.stop()

# --- 申請フォーム ---
with st.form("join_request_form"):
    st.subheader("基本情報")
    
    # 入力項目（ユーザー指定）
    name = st.text_input("氏名（フルネーム）", placeholder="例：慶應 太郎")
    s_id = st.text_input("学籍番号", placeholder="例：824xxxxx")
    player_name = st.text_input("プレイヤーネーム（ランキングにはこの名前が表示されます）", placeholder="例：けいおう")
    email = st.text_input("慶應メールアドレス", placeholder="example@keio.jp")

    faculty_options = [
        "文学部", "経済学部", "法学部", "商学部", "医学部", "理工学部",
        "総合政策学部", "環境情報学部", "看護医療学部", "薬学部", "その他"
    ]
    faculty = st.selectbox("学部", faculty_options)

    gender = st.radio("性別", ("男性", "女性"))

    st.markdown("---")
    st.subheader("💰 振込情報確認")
    st.caption("照合のため、振込時の名義と日付を正確に入力してください。")

    col1, col2 = st.columns(2)
    transfer_name = col1.text_input("振込名義人（カナ）", placeholder="例：ケイオウ タロウ")
    transfer_date = col2.date_input("振込日", datetime.date.today())

    submitted = st.form_submit_button("申請する", type="primary")

    if submitted:
        if not all([name, s_id, player_name, email, transfer_name]):
            st.error("⚠️ すべての項目を入力してください。")
        elif "@keio.jp" not in email:
            st.error("⚠️ 慶應のメールアドレス（@keio.jp）を入力してください。")
        else:
            # --- ここで自動計算 (Logic) ---
            # term_number = 振込年 - 2022
            term_num = transfer_date.year - 2022

            # データ送信処理
            try:
                data = {
                    "student_name": name,
                    "student_id_number": s_id,
                    "player_name": player_name,
                    "faculty": faculty,
                    "gender": gender,
                    "email": email,
                    "transfer_name": transfer_name,
                    "transfer_date": transfer_date.isoformat(),
                    
                    # 計算した期数を送信
                    "term_number": term_num,
                    
                    "status": "PENDING"
                }
                supabase.table("membership_requests").insert(data).execute()

                st.success(f"✅ 申請を受け付けました！\nあなたは【{term_num}期生】として登録申請されました。\n入金確認をお待ちください。")
                st.balloons()

            except Exception as e:
                st.error(f"送信エラーが発生しました: {e}")
