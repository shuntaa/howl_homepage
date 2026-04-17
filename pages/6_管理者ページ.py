import streamlit as st
from datetime import date
import pandas as pd

# プロジェクトルートをパスに追加
from modules._db import init_connection, get_active_players_info, get_sanitized_players_df
from modules.env_banner import show_dev_warning

show_dev_warning()

def show_record_score_page(supabase):
    """成績入力フォームを表示する関数"""
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


def show_accounting_page(supabase):
    """会計ページ：資金の補充申請フォームを表示する関数"""
    st.subheader("💸 資金の補充申請 (For Current Rep)")

    with st.form("request_funds"):
        req_amount = st.number_input("補充希望額", min_value=1000, step=1000)
        reason = st.text_input("理由（例：合宿費の先払いのため）")
        
        # 証拠画像（現在の財布の中身や、未精算レシートなど）
        proof_img = st.file_uploader("現在の状況（証憑）", type=['jpg', 'png'])
        
        if st.form_submit_button("CFOへ申請する"):
            # ここでSlackやLINEに通知を飛ばすと完璧
            # send_line_notify(f"¥{req_amount} の補充申請が来ました！理由: {reason}")
            st.success("申請しました！CFO（山本）の承認をお待ちください。")

def show_player_roster_page(supabase):
    """選手名簿を表示する関数"""
    st.header("📖 Player Roster")
    st.write("現在登録されているアクティブなプレイヤーの一覧です。")
    df = get_sanitized_players_df(supabase)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("アクティブなプレイヤーが見つかりません。")

# --- メインの管理者ページロジック ---
st.title("🔒 管理者ページ")

try:
    supabase = init_connection()
except Exception:
    st.error("データベースに接続できませんでした。管理者にご連絡ください。")
    supabase = None

if supabase is None:
    st.info("データベース接続が確立されるまで、このページは使用できません。")
    st.stop()

# パスワード認証
if not st.session_state.get("authenticated", False):
    st.header("Staff Login")
    password = st.text_input("パスワードを入力してください", type="password")
    
    # 新しい secrets.toml の構造に対応
    try:
        staff_pass = st.secrets["auth"]["staff_password"]   # 幹部用
        master_pass = st.secrets["auth"]["master_password"] # あなた用
    except KeyError:
        st.error("⚠️ secrets.toml にパスワード設定が見つかりません。")
        st.stop()

    if st.button("Login"):
        # 幹部パスワード または マスターパスワード でログイン可
        if password == staff_pass or password == master_pass:
            st.session_state.authenticated = True
            st.success("ログイン成功")
            st.rerun()
        else:
            st.error("パスワードが違います")
            st.stop()
else:
    # 認証後の表示
    st.sidebar.success("管理者としてログイン中")
    
    admin_pages = {
        "成績入力": show_record_score_page,
        "選手名簿": show_player_roster_page,
        "会計": show_accounting_page,
    }

    selection = st.sidebar.radio("メニューを選択", list(admin_pages.keys()))
    
    page_function = admin_pages[selection]
    
    page_function(supabase)

    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()
