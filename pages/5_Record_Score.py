import streamlit as st
from datetime import date
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pages._db import init_connection, get_active_players_info

try:
    supabase = init_connection()
except Exception as e:
    st.error("データベースに接続できませんでした。管理者にご連絡ください。")
    st.error(e)
    supabase = None

if supabase is None:
    st.info("データベース接続が確立されるまで、このページは使用できません。")
else:
    # 認証ロジック
    if not st.session_state.get("authenticated", False):
        st.header("🔒 Admin Login")
        password = st.text_input("幹部用パスワード", type="password", key="password_input")
        
        # パスワードを安全にチェック
        admin_password = st.secrets.get("admin", {}).get("password")

        if st.button("Login"):
            if admin_password and password == admin_password:
                st.session_state.authenticated = True
                st.rerun() # ログイン成功後、再実行してフォームを表示
            else:
                st.error("パスワードが違うか、設定されていません。")
        
    # 認証済みの場合にフォームを表示
    else:
        st.header("📝 Record Match Result")
        with st.form("result_form"):
            players_info = get_active_players_info(supabase)
            player_options = {player['student_id']: player['name'] for player in players_info}

            col1, col2 = st.columns(2)
            with col1:
                game_date = st.date_input("日付", date.today())
            with col2:
                memo = st.text_input("メモ (任意)")
            
            st.write("勝者と敗者を選択してください")
            winners = st.multiselect("🏅 勝者 (Winners)", options=list(player_options.keys()), format_func=lambda x: player_options[x])
            losers = st.multiselect("💀 敗者 (Losers)", options=list(player_options.keys()), format_func=lambda x: player_options[x])
            
            submitted = st.form_submit_button("登録する")
            
            if submitted:
                if not winners and not losers:
                    st.error("参加者が選択されていません")
                elif set(winners) & set(losers):
                    st.error("同じプレイヤーが勝者と敗者の両方に含まれています！")
                else:
                    insert_data = []
                    for p in winners:
                        insert_data.append({"game_date": str(game_date), "student_id": p, "is_win": 1, "memo": memo})
                    for p in losers:
                        insert_data.append({"game_date": str(game_date), "student_id": p, "is_win": 0, "memo": memo})
                    
                    try:
                        supabase.table("match_results").insert(insert_data).execute()
                        st.success(f"登録完了！ (勝者: {len(winners)}名, 敗者: {len(losers)}名)")
                    except Exception as e:
                        st.error(f"エラー: {e}")

        st.subheader("⚠️ 直近の登録をキャンセル")
        if st.button("最後に登録した1件（全参加者分）を削除する"):
            try:
                last_record = supabase.table("match_results").select("created_at").order("created_at", desc=True).limit(1).execute()
                if last_record.data:
                    last_time = last_record.data[0]["created_at"]
                    supabase.table("match_results").delete().eq("created_at", last_time).execute()
                    st.warning(f"時刻 {last_time} のデータを削除しました。")
                    st.rerun()
                else:
                    st.info("削除できるデータがありません。")
            except Exception as e:
                st.error(f"削除中にエラーが発生しました: {e}")

        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()
