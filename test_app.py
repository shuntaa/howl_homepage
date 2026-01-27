import pandas as pd
import pytest
from app import assign_percentile_title

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
