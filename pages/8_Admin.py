import streamlit as st
import pandas as pd
import random
import string
from modules._db import init_connection
from modules.env_banner import show_dev_warning, render_env_diagnostics

# --- デバッグ用（確認したらすぐ消すこと！）---
# st.write("▼ secretsの中身確認")
# st.write(st.secrets)
# ------------------------------------------

# メール送信関数をインポート
try:
    from modules.utils import send_welcome_email
except ImportError:
    st.error("⚠️ 'pages/utils.py' が見つかりません。メール送信機能が動きません。")

st.set_page_config(page_title="管理者画面", page_icon="🛡️")
show_dev_warning()

# --- 関数定義 ---
def generate_code():
    """4桁の数字を含む認証コードを生成 (例: HWL-8392)"""
    digits = ''.join(random.choices(string.digits, k=4))
    return f"HWL-{digits}"

# --- メイン処理 ---

# ---------------------------------------------------------
# 🔐 セキュリティ設定 (最高権限ロック)
# ---------------------------------------------------------
try:
    # secrets.toml からパスワードを取得
    # [auth] セクションがある前提
    MASTER_PASSWORD = st.secrets["auth"]["master_password"]
    STAFF_PASSWORD  = st.secrets["auth"].get("staff_password") 

except KeyError:
    st.error("⚠️ secrets.toml の設定が不足しています。[auth]セクションを確認してください。")
    st.stop()
except Exception as e:
    st.error(f"認証設定エラー: {e}")
    st.stop()

# --- 認証フォーム ---
password = st.sidebar.text_input("Master Password", type="password")

# --- 認証ロジック ---
if password == MASTER_PASSWORD:
    # ✅ 認証成功
    st.sidebar.success("Welcome, Administrator.")

elif password == STAFF_PASSWORD:
    # ⛔ 幹部パスワードで入ろうとした場合
    st.sidebar.error("⛔ Access Denied")
    st.error("⚠️ このページは管理者（Master）専用です。\n幹部権限ではアクセスできません。")
    st.stop()

else:
    # ❌ 間違い、または未入力
    if password:
        st.sidebar.error("パスワードが違います")
    
    st.warning("管理者用マスターパスワードを入力してください")
    st.stop()

# ---------------------------------------------------------
# 🛡️ ここから管理者機能 (DB接続など)
# ---------------------------------------------------------
st.header("🛡️ Howl 管理コンソール (Master Only)")
render_env_diagnostics()

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
                
                # 名前重複時に変更できるようにする
                approved_name = st.text_input(
                    "登録プレイヤー名 (変更可)", 
                    value=row['player_name'], 
                    key=f"name_edit_{row['id']}"
                )

            with col2:
                st.write(f"**振込日:** {row['transfer_date']}")
                st.write(f"**Email:** {row['email']}")
                st.caption(f"申請日時: {row['created_at'][:10]}")
                if 'receipt_url' in row and row['receipt_url']:
                    st.markdown("---") # 区切り線
                    st.image(row['receipt_url'], caption="振込明細", width=250)
                else:
                    st.caption("※ 明細画像なし")
            
            with col3:
                # 承認アクション
                if st.button("承認 ✅", key=f"approve_{row['id']}"):
                    
                    # 1. 認証コード生成
                    v_code = generate_code()

                    # 2. playersに追加（編集後の approved_name を使う）
                    new_player = {
                        "name": approved_name,             # 👈 編集後の名前
                        "real_name": row['student_name'],  # 本名
                        "faculty": row['faculty'],
                        "gender": row['gender'],
                        "email": row['email'],
                        "term_number": row['term_number'], 
                        "student_id": row['student_id_number'], 
                        "is_active": True,
                        "verification_code": v_code
                    }
                    
                    try:
                        # DB登録
                        supabase.table("players").insert(new_player).execute()
                        
                        # 3. 売上(transactions)に追加
                        income = {
                            "type": "IN",
                            "category": "入サー費",
                            "amount": 5000,
                            "description": f"新入生: {row['student_name']} ({approved_name})",
                            "created_by": "Admin Approval"
                        }
                        supabase.table("transactions").insert(income).execute()

                        # 4. メール送信（コードを送る）
                        if row['email']:
                            with st.spinner("📧 招待状を送信中..."):
                                send_welcome_email(
                                    to_email=row['email'],
                                    user_name=row['student_name'],
                                    player_name=approved_name, # メールもこの名前で
                                    verification_code=v_code
                                )
                                st.toast("招待メールを送信しました！", icon="📩")

                        # 5. ステータス更新（完了）
                        supabase.table("membership_requests").update({"status": "APPROVED"}).eq("id", row['id']).execute()
                        
                        st.success(f"「{approved_name}」さんを承認しました！")
                        st.rerun()

                    except Exception as e:
                        # エラーハンドリング
                        err_msg = str(e)
                        if "Key (name)" in err_msg:
                             st.error(f"❌ エラー: 名前「{approved_name}」は既に使われています。\n左の入力欄で別の名前に変えてから、もう一度承認ボタンを押してください。")
                        elif "Key (student_id)" in err_msg:
                             st.error("❌ エラー: その「学籍番号」は既に登録されています。")
                        elif "Key (email)" in err_msg:
                             st.error("❌ エラー: その「メールアドレス」は既に登録されています。")
                        else:
                            st.error(f"データベース登録エラー: {e}")

                # 却下アクション
                if st.button("却下 ❌", key=f"reject_{row['id']}"):
                    supabase.table("membership_requests").update({"status": "REJECTED"}).eq("id", row['id']).execute()
                    st.error("申請を却下しました")
                    st.rerun()
            
            st.markdown("---")
