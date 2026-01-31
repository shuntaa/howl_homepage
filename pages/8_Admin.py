import streamlit as st
import pandas as pd
from pages._db import init_connection

st.set_page_config(page_title="管理者画面", page_icon="🛡️")

# パスワードロック（簡易版）
ADMIN_PASSWORD = "howl_admin" # 本番は st.secrets を推奨
password = st.sidebar.text_input("Admin Password", type="password")

if password != ADMIN_PASSWORD:
    st.warning("管理者パスワードを入力してください")
    st.stop()

st.header("🛡️ Howl 管理コンソール")

try:
    supabase = init_connection()
except:
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
            st.markdown(f"### {row['student_name']}")
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"**学籍番号:** `{row['student_id_number']}`")
                st.write(f"**振込名義:** `{row['transfer_name']}`")
            with col2:
                st.write(f"**振込日:** {row['transfer_date']}")
                st.caption(f"申請日時: {row['created_at'][:10]}")
            
            with col3:
                # 承認アクション
                if st.button("承認 ✅", key=f"approve_{row['id']}"):
                    # 1. playersに追加
                    new_player = {
                        "name": row['student_name'],
                        "student_id": row['student_id_number'],
                        "is_active": True
                    }
                    supabase.table("players").insert(new_player).execute()
                    
                    # 2. 売上(transactions)に追加
                    income = {
                        "type": "IN",
                        "category": "入サー費",
                        "amount": 5000,
                        "description": f"新入生: {row['student_name']}",
                        "created_by": "Admin Approval"
                    }
                    supabase.table("transactions").insert(income).execute()

                    # 3. リクエスト済み(APPROVED)にする
                    supabase.table("membership_requests").update({"status": "APPROVED"}).eq("id", row['id']).execute()
                    
                    st.success(f"{row['student_name']}さんを承認・登録しました！")
                    st.rerun()

                # 却下アクション
                if st.button("却下 ❌", key=f"reject_{row['id']}"):
                    supabase.table("membership_requests").update({"status": "REJECTED"}).eq("id", row['id']).execute()
                    st.error("却下しました")
                    st.rerun()
            
            st.markdown("---")
