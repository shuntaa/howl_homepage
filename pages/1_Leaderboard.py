import streamlit as st
import pandas as pd
import numpy as np
from pages._db import init_connection, load_data, assign_percentile_title

st.header("🏆 Player Rating")

try:
    supabase = init_connection()
except Exception:
    supabase = None

if supabase is None:
    st.error("データベースに接続できませんでした。")
else:
    # --- データ表示 ---
    df = load_data(supabase)

    if df.empty:
        st.info("まだ対戦データがありません。")
    else:
        stats = df.groupby(["student_id", "player_name"])["is_win"].agg(w="sum", n="count").reset_index()
        stats["Score"] = ((stats["w"] + 1) / (stats["n"] + 2)) * np.log(stats["n"] + 1) * 100
        ranking = stats.sort_values("Score", ascending=False)
        ranking["Rank"] = ranking["Score"].rank(ascending=False, method='min').astype(int)
        
        total_players = len(ranking)
        ranking["Title"] = ranking["Rank"].apply(assign_percentile_title, total_players=total_players)
        
        ranking["Score"] = ranking["Score"].round(0)
        ranking = ranking.rename(columns={"w": "Wins", "n": "Games", "player_name": "Player"})
        
        display_columns = ["Rank", "Title", "Player", "Score", "Wins", "Games"]
        st.dataframe(ranking[display_columns].set_index("Rank"), use_container_width=True)

        with st.expander("対戦履歴ログ"):
            st.dataframe(df.sort_values("game_date", ascending=False))
