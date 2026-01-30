import pandas as pd
import pytest
from unittest.mock import MagicMock
from pages._db import assign_percentile_title


def test_assign_percentile_title():
    # Test cases
    # total_players = 100

    # S-Class (top 10%)
    assert assign_percentile_title(5, 100) == "💎 S-Class (Top 10%)"
    assert assign_percentile_title(10, 100) == "💎 S-Class (Top 10%)"

    # A-Class (10% to 30%)
    assert assign_percentile_title(11, 100) == "✨ A-Class (Top 30%)"
    assert assign_percentile_title(30, 100) == "✨ A-Class (Top 30%)"

    # B-Class (30% to 60%)
    assert assign_percentile_title(31, 100) == "👣 B-Class (Top 60%)"
    assert assign_percentile_title(60, 100) == "👣 B-Class (Top 60%)"

    # Rookie (above 60%)
    assert assign_percentile_title(61, 100) == "🔰 Rookie"
    assert assign_percentile_title(100, 100) == "🔰 Rookie"

    # Test with different total_players
    # total_players = 20
    assert assign_percentile_title(1, 20) == "💎 S-Class (Top 10%)" # 1/20 = 0.05
    assert assign_percentile_title(2, 20) == "💎 S-Class (Top 10%)" # 2/20 = 0.1

    assert assign_percentile_title(3, 20) == "✨ A-Class (Top 30%)" # 3/20 = 0.15
    assert assign_percentile_title(6, 20) == "✨ A-Class (Top 30%)" # 6/20 = 0.3

    assert assign_percentile_title(7, 20) == "👣 B-Class (Top 60%)" # 7/20 = 0.35
    assert assign_percentile_title(12, 20) == "👣 B-Class (Top 60%)" # 12/20 = 0.6

    assert assign_percentile_title(13, 20) == "🔰 Rookie" # 13/20 = 0.65

def test_init_connection_success(monkeypatch):
    """init_connection が st.secrets から正しく接続情報を取得してクライアントを返すことを検証"""
    mock_client = MagicMock()
    mock_create_client = MagicMock(return_value=mock_client)
    mock_st = MagicMock()
    mock_st.secrets = {"supabase": {"url": "https://test.supabase.co", "key": "test-key"}}

    monkeypatch.setattr("pages._db.create_client", mock_create_client)
    monkeypatch.setattr("pages._db.st", mock_st)

    from pages._db import init_connection

    result = init_connection()
    assert result is mock_client
    mock_create_client.assert_called_once_with("https://test.supabase.co", "test-key")


def test_load_data_with_mock(monkeypatch):
    """load_data が Supabase から取得したデータを DataFrame に変換することを検証"""
    mock_data = [
        {"game_date": "2024-01-01", "student_id": 1, "is_win": 1, "memo": "Test", "players": {"name": "Player 1"}},
        {"game_date": "2024-01-01", "student_id": 2, "is_win": 0, "memo": "Test", "players": {"name": "Player 2"}},
    ]
    mock_response = MagicMock()
    mock_response.data = mock_data

    mock_supabase = MagicMock()
    mock_supabase.table().select().execute.return_value = mock_response

    from pages._db import load_data

    df = load_data(mock_supabase)
    assert len(df) == 2
    assert "student_id" in df.columns
    assert "player_name" in df.columns
    assert df["player_name"].tolist() == ["Player 1", "Player 2"]


def test_get_player_name_map(monkeypatch):
    """get_player_name_map が正しくマッピングを返すことを検証"""
    mock_data = [
        {"student_id": 1, "name": "Player 1"},
        {"student_id": 2, "name": "Player 2"},
    ]
    mock_response = MagicMock()
    mock_response.data = mock_data

    mock_supabase = MagicMock()
    mock_supabase.table().select().execute.return_value = mock_response

    monkeypatch.setattr("pages._db.get_players", lambda supabase: mock_data)

    from pages._db import get_player_name_map

    name_map = get_player_name_map(mock_supabase)
    assert name_map == {1: "Player 1", 2: "Player 2"}



def test_load_data_empty(monkeypatch):
    """load_data が空のレスポンスで空の DataFrame を返すことを検証"""
    mock_response = MagicMock()
    mock_response.data = None

    mock_supabase = MagicMock()
    mock_supabase.table().select().execute.return_value = mock_response

    from pages._db import load_data

    df = load_data(mock_supabase)
    assert df.empty