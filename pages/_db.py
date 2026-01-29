import streamlit as st
from supabase import create_client, Client
import pandas as pd
import numpy as np

def init_connection():
    """Supabaseへの接続を初期化して返す"""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

def load_data(supabase: Client):
    """戦績データを取得"""
    response = supabase.table("match_results").select("*").execute()
    if not response.data:
        return pd.DataFrame()
    return pd.DataFrame(response.data)

def get_players(supabase: Client):
    """プレイヤー名簿を取得（match_resultsから）"""
    response = supabase.table("match_results").select("player_name").execute()
    if not response.data:
        return []
    return pd.DataFrame(response.data)["player_name"].unique().tolist()

def get_active_players(supabase: Client):
    """GM用: アクティブなプレイヤー名簿を取得（playersテーブル）"""
    response = supabase.table("players").select("name").eq("is_active", True).execute()
    if not response.data:
        return []
    return [row["name"] for row in response.data]

def insert_match_results(supabase: Client, insert_data: list):
    """戦績をmatch_resultsに登録"""
    supabase.table("match_results").insert(insert_data).execute()

def assign_percentile_title(rank_val, total_players):
    # p: 累積分布関数(CDF)における位置の近似
    p = rank_val / total_players
    if p <= 0.1: return "💎 S-Class (Top 10%)"
    if p <= 0.3: return "✨ A-Class (Top 30%)"
    if p <= 0.6: return "👣 B-Class (Top 60%)"
    return "🔰 Rookie"
