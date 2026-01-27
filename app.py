import streamlit as st
from supabase import create_client, Client
import pandas as pd
import numpy as np # 数学関数(log)を使うために追加
from datetime import date

# --- 1. Supabase接続 ---
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

# --- 2. ページ設定 ---
st.set_page_config(page_title="Howl Official", layout="wide")
st.title("🐺 Howl Rating System")

page = st.sidebar.selectbox("Menu", ["Leaderboard (ランキング)", "Record Result (勝敗入力)", "Social Media (SNS)"])

# --- 関数 ---
def load_data():
    """戦績データを取得"""
    response = supabase.table("match_results").select("*").execute()
    if not response.data:
        return pd.DataFrame()
    return pd.DataFrame(response.data)

def get_players():
    """プレイヤー名簿を取得"""
    response = supabase.table("players").select("name").eq("is_active", True).execute()
    return [row["name"] for row in response.data]

# --- ページ1: ランキング (数理モデル実装) ---
if page == "Leaderboard (ランキング)":
    st.header("🏆 Player Rating")
    
    df = load_data()
    
    if df.empty:
        st.info("まだ対戦データがありません。")
    else:
        # 1. プレイヤーごとの勝利数(w)と総対戦数(n)を集計
        # is_winには 1(勝) か 0(負) が入っているので、sumをとれば勝利数になります
        stats = df.groupby("player_name")["is_win"].agg(
            w="sum",   # 勝利数 (Wins)
            n="count"  # 総参加数 (Total Games)
        ).reset_index()
        
        # 2. 指定の関数でスコア計算
        # Score = ((w + 1) / (n + 2)) * log(n + 1)
        # ※np.log は自然対数(ln)です。常用対数にしたい場合は np.log10 に変えてください
        stats["Score"] = ((stats["w"] + 1) / (stats["n"] + 2)) * np.log(stats["n"] + 1) * 100
        
        # 3. 表示用に整える
        # スコアが高い順にソート
        ranking = stats.sort_values("Score", ascending=False)
        ranking.index = range(1, len(ranking) + 1)
        
        # スコアを見やすく丸める
        ranking["Score"] = ranking["Score"].round(0)
        
        # カラム名の整理
        ranking = ranking.rename(columns={"w": "Wins", "n": "Games"})
        
        st.dataframe(ranking, use_container_width=True)
        
        with st.expander("対戦履歴ログ"):
            st.dataframe(df.sort_values("game_date", ascending=False))

# --- ページ2: 勝敗入力 ---
elif page == "Record Result (勝敗入力)":
    st.header("📝 Record Match Result")

    # 認証チェック
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        password = st.text_input("幹部用パスワード", type="password")
        if st.button("Login"):
            if password == st.secrets["admin"]["password"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("パスワードが違います")
    else:
        # --- 勝敗入力フォーム ---
        player_options = get_players()

        with st.form("result_form"):
            col1, col2 = st.columns(2)
            with col1:
                game_date = st.date_input("日付", date.today())
                # game_type は不要になったので削除
            with col2:
                memo = st.text_input("メモ (任意)")
            
            st.write("---")
            st.write("勝者と敗者を選択してください")
            
            # 勝者と敗者をそれぞれ選ばせるUI
            # (同じ人が両方選ばれないように注意が必要ですが、まずはシンプルに実装)
            winners = st.multiselect("🏅 勝者 (Winners)", options=player_options)
            losers = st.multiselect("💀 敗者 (Losers)", options=player_options)
            
            submitted = st.form_submit_button("登録する")
            
            if submitted:
                # バリデーション: 勝者も敗者もいない、または重複している場合
                if not winners and not losers:
                    st.error("参加者が選択されていません")
                elif set(winners) & set(losers): # 積集合で重複チェック
                    st.error("同じプレイヤーが勝者と敗者の両方に含まれています！")
                else:
                    insert_data = []
                    
                    # 勝者データ (is_win = 1)
                    for p in winners:
                        insert_data.append({
                            "game_date": str(game_date),
                            "player_name": p,
                            "is_win": 1, # 勝ちフラグ
                            "memo": memo
                        })
                    
                    # 敗者データ (is_win = 0)
                    for p in losers:
                        insert_data.append({
                            "game_date": str(game_date),
                            "player_name": p,
                            "is_win": 0, # 負けフラグ
                            "memo": memo
                        })
                    
                    try:
                        supabase.table("match_results").insert(insert_data).execute()
                        st.success(f"登録完了！ (勝者: {len(winners)}名, 敗者: {len(losers)}名)")
                    except Exception as e:
                        st.error(f"エラー: {e}")

        st.write("---")
        st.subheader("⚠️ 直近の登録をキャンセル")

        if st.button("最後に登録した1件（全参加者分）を削除する"):
            # 1. 最後に登録された created_at を特定
            last_record = supabase.table("match_results").select("created_at").order("created_at", desc=True).limit(1).execute()
            
            if last_record.data:
                last_time = last_record.data[0]["created_at"]
                # 2. その同じ日時に登録されたデータをすべて削除（一度の登録で複数人分入るため）
                supabase.table("match_results").delete().eq("created_at", last_time).execute()
                st.warning(f"時刻 {last_time} のデータを削除しました。")
                st.rerun()
            else:
                st.info("削除できるデータがありません。")

# --- ページ3: SNSリンク ---
elif page == "Social Media (SNS)":
    st.header("🔗 Our Social Media")
    st.markdown("Here you can find our official social media channels:")
    
    st.markdown("""
    - 公式Line: [Howl Official Instagram](https://line.me/R/ti/p/@290bixgt)
    - Instagram: [Howl Official Instagram](https://www.instagram.com/keio_howl)
    - X (Twitter): [Howl Official X Account](https://x.com/keio_howl?s=21&t=TriTKMLwbruJApWYrQQ3eA)
    - YouTube: [Howl Official YouTube Channel](https://youtube.com/channel/UCpXfFc7T2f0tG6mBApIfnlA?si=QqCmmo-xRIMLsGMq)
    """)


