import streamlit as st
import pandas as pd
import random
import string
from pages._db import init_connection

# メール送信関数をインポート（pages/utils.py がある前提）
try:
    from pages.utils import send_welcome_email
except ImportError:
    st.error("⚠️ 'pages/utils.py' が見つかりません。メール送信機能が動きません。")

st.set_page_config(page_title="管理者画面", page_icon="🛡️")

# --- 関数定義 ---
def generate_code():
    """4桁の数字を含む認証コードを生成 (例: HWL-8392)"""
    digits = ''.join(random.choices(string.digits, k=4))
    return f"HWL-{digits}"

# --- メイン処理 ---
# パスワードロック
ADMIN_PASSWORD = "howl_admin" # 本番は st.secrets["admin_password"] 推奨
password = st.sidebar.text_input("Admin Password", type="password")

if password != ADMIN_PASSWORD:
    st.warning("管理者パスワードを入力してください")
    st.stop()

st.header("🛡️ Howl 管理コンソール")

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"DB接続エラー: {e}")
    st.stop()

# --- 承認待ちリスト ---
st.subheader("⏳ 入部承認待ちリスト")

# PENDING状態の人だけ取ってくる
reqs = supabase.table("membership_requests").select("*").eq("status", "PENDING").order("created_at", desc=True).execute()
df_reqs = pd.DataFrame(reqs.data)

if df_reqs.empty:
    st.info("現在、承認待ちの申請はありません。")
else:
    for index, row in df_reqs.iterrows():
        # カード形式で表示
        with st.container():
            st.markdown(f"### {row['student_name']} (申請者)")
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"**学籍番号:** `{row['student_id_number']}`")
                st.write(f"**振込名義:** `{row['transfer_name']}`")
                st.write(f"**プレイヤー名:** `{row['player_name']}`")
            with col2:
                st.write(f"**振込日:** {row['transfer_date']}")
                st.write(f"**Email:** {row['email']}")
                st.caption(f"申請日時: {row['created_at'][:10]}")
            
            with col3:
                # 承認アクション
                if st.button("承認 ✅", key=f"approve_{row['id']}"):
                    
                    # 1. 認証コード生成
                    v_code = generate_code()

                    # 2. playersに追加（認証コード付き）
                    new_player = {
                        "name": row['player_name'],        # ランキング表示名
                        "real_name": row['student_name'],  # 本名
                        "faculty": row['faculty'],
                        "gender": row['gender'],
                        "email": row['email'],
                        "term_number": row['term_number'], # 自動計算された期数
                        "student_id": row['student_id_number'], 
                        "is_active": True,
                        "verification_code": v_code        # 👈 追加: 合言葉
                    }
                    
                    # DB操作（エラーハンドリング付き）
                    try:
                        supabase.table("players").insert(new_player).execute()
                        
                        # 3. 売上(transactions)に追加
                        income = {
                            "type": "IN",
                            "category": "入サー費",
                            "amount": 5000,
                            "description": f"新入生: {row['student_name']} ({row['player_name']})",
                            "created_by": "Admin Approval"
                        }
                        supabase.table("transactions").insert(income).execute()

                        # 4. メール送信（コードを送る）
                        if row['email']:
                            with st.spinner("📧 招待状を送信中..."):
                                is_sent = send_welcome_email(
                                    to_email=row['email'],
                                    user_name=row['student_name'],
                                    player_name=row['player_name'],
                                    verification_code=v_code # 👈 追加: メールに載せる
                                )
                            if is_sent:
                                st.toast("招待メールを送信しました！", icon="📩")
                            else:
                                st.error("メール送信に失敗しました（ログを確認してください）")
                        else:
                            st.warning("メールアドレスがないため送信できませんでした。")

                        # 5. ステータス更新（完了）
                        supabase.table("membership_requests").update({"status": "APPROVED"}).eq("id", row['id']).execute()
                        
                        st.success(f"「{row['player_name']}」さんを承認しました！")
                        st.rerun()

                    except Exception as e:
                        st.error(f"データベース登録エラー: {e}")

                # 却下アクション
                if st.button("却下 ❌", key=f"reject_{row['id']}"):
                    supabase.table("membership_requests").update({"status": "REJECTED"}).eq("id", row['id']).execute()
                    st.error("申請を却下しました")
                    st.rerun()
            
            st.markdown("---")
