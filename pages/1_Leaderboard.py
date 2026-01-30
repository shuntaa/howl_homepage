import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import date, datetime
from pages._db import init_connection, load_data, assign_percentile_title

from pages._db import init_connection, load_data, assign_percentile_title

st.header("🏆 Player Rating")


# --- 1. 期間選択のUIを作成 ---
# 横並びのラジオボタンで切り替えやすくします
period_mode = st.radio(
    "集計期間",
    ["今年度 (Current)", "通算 (All Time)"],
    horizontal=True,
    help="「今年度」は4月1日以降の試合のみを集計します。"
)

try:
    supabase = init_connection()
except Exception:
    supabase = None
    st.error(f"接続エラー: {e}")
    st.stop()

if supabase is None:
    st.error("データベースに接続できませんでした。")
else:
    # --- データ表示 ---
    df = load_data(supabase)

    if df.empty:
        st.info("まだ対戦データがありません。")
    else:
        # 日付型への変換（念のため）
        df["game_date"] = pd.to_datetime(df["game_date"])

            # --- 3. フィルタリングロジック（ここが肝です） ---
        if period_mode == "今年度 (Current)":
            today = date.today()
            # 今が1~3月なら、年度開始は去年の4月。4~12月なら今年の4月。
            if today.month < 4:
                start_year = today.year - 1
            else:
                start_year = today.year

            start_date = pd.Timestamp(datetime(start_year, 4, 1))

            # フィルタリング実行
            df_display = df[df["game_date"] >= start_date].copy()

            if df_display.empty:
                st.warning(f"今年度（{start_year}年4月以降）のデータはまだありません。")
        else:
            # 通算ならそのまま
            df_display = df.copy()


# --- 4. 集計ロジック（df_display に対して行う） ---
        if not df_display.empty:

            stats = df_display.groupby(["student_id", "player_name"])["is_win"].agg(w="sum", n="count").reset_index()
            stats["Score"] = ((stats["w"] + 1) / (stats["n"] + 2)) * np.log(stats["n"] + 1) * 100
            # 純粋な勝率（w/n）を計算（パーセント表示用に100を掛ける）
            stats["Win Rate"] = (stats["w"] / stats["n"] * 100).round(1)

            ranking = stats.sort_values("Score", ascending=False)
            ranking["Rank"] = ranking["Score"].rank(ascending=False, method='min').astype(int)
            


            total_players = len(ranking)
            ranking["Title"] = ranking["Rank"].apply(assign_percentile_title, total_players=total_players)
            
            ranking["Score"] = ranking["Score"].round(0)
            ranking = ranking.rename(columns={"w": "Wins", "n": "Games", "player_name": "Player"})
            
            # 表示したいカラムのリストに "Win Rate" を追加
            # 勝率に「%」を付けて見やすく加工します
            ranking["Win Rate %"] = ranking["Win Rate"].astype(str) + "%"

            display_columns = ["Rank", "Title", "Player", "Score", "Wins", "Games","Win Rate %"]

            st.dataframe(ranking[display_columns].set_index("Rank"), use_container_width=True)

            with st.expander("対戦履歴ログ"):
                st.dataframe(df.sort_values("game_date", ascending=False))
