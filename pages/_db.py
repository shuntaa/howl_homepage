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
    response = supabase.table("match_results").select("student_id, is_win, game_date, created_at, memo").execute()
    if not response.data:
        return pd.DataFrame()
    
    df = pd.DataFrame(response.data)
    
    player_map = get_player_name_map(supabase)
    df['player_name'] = df['student_id'].map(player_map).fillna("Unknown")
        
    return df

def get_players(supabase: Client):
    """プレイヤー名簿を取得（playersテーブルから）"""
    response = supabase.table("players").select("student_id, name").eq("is_active", True).execute()
    if not response.data:
        return []
    return response.data

def get_player_name_map(supabase: Client):
    """student_idとプレイヤー名のマッピングを取得"""
    players = get_players(supabase)
    return {player["student_id"]: player["name"] for player in players}

def get_active_players(supabase: Client):
    """【GM用】アクティブな全プレイヤー情報を取得（playersテーブル）"""
    response = supabase.table("players").select("*").eq("is_active", True).execute()
    if not response.data:
        return []
    return response.data

def get_sanitized_players_df(supabase: Client):
    """【一般画面用】個人情報を除外したプレイヤー一覧をDataFrameで取得"""
    players_data = get_active_players(supabase)
    if not players_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(players_data)
    
    # センシティブな情報をここでドロップ
    sensitive_columns = ["real_name", "term_number", "faculty", "email", "gender"]
    # 存在しない列をドロップしようとするとエラーになるため、存在する列のみを対象とする
    columns_to_drop = [col for col in sensitive_columns if col in df.columns]
    
    return df.drop(columns=columns_to_drop)

def get_active_players_info(supabase: Client):
    """アクティブなプレイヤーの情報（student_id, name）を取得"""
    players = get_active_players(supabase)
    return [{"student_id": player["student_id"], "name": player["name"]} for player in players]

def get_active_player_names(supabase: Client):
    """アクティブなプレイヤーの名前のみを取得"""
    players_info = get_active_players_info(supabase)
    return [player["name"] for player in players_info]


def insert_match_results(supabase: Client, insert_data: list):
    """戦績をmatch_resultsに登録"""
    supabase.table("match_results").insert(insert_data).execute()

def upsert_players(supabase: Client, players_df: pd.DataFrame):
    """【GM用】プレイヤー情報を一括でUpsert（Insert or Update）"""
    # DataFrameをJSON形式（辞書型のリスト）に変換
    records = players_df.to_dict('records')
    # on_conflictに指定したカラムで重複を判定し、存在すればUpdate、しなければInsert
    return supabase.table("players").upsert(records, on_conflict="student_id").execute()


def assign_percentile_title(rank_val, total_players):
    # p: 累積分布関数(CDF)における位置の近似
    p = rank_val / total_players
    if p <= 0.1: return "💎 S-Class (Top 10%)"
    if p <= 0.3: return "✨ A-Class (Top 30%)"
    if p <= 0.6: return "👣 B-Class (Top 60%)"
    return "🔰 Rookie"
