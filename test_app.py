import pandas as pd
import pytest
from app import assign_percentile_title

def test_assign_percentile_title():
    # Test cases
    # total_players = 100

    # S-Class (top 10%)
    row_s = pd.Series({'Rank': 5})
    assert assign_percentile_title(row_s, 100) == "💎 S-Class"

    row_s_boundary = pd.Series({'Rank': 10})
    assert assign_percentile_title(row_s_boundary, 100) == "💎 S-Class"

    # A-Class (10% to 30%)
    row_a_lower_boundary = pd.Series({'Rank': 11})
    assert assign_percentile_title(row_a_lower_boundary, 100) == "✨ A-Class"

    row_a_upper_boundary = pd.Series({'Rank': 30})
    assert assign_percentile_title(row_a_upper_boundary, 100) == "✨ A-Class"

    # B-Class (above 30%)
    row_b = pd.Series({'Rank': 31})
    assert assign_percentile_title(row_b, 100) == "👣 B-Class"

    row_b_max = pd.Series({'Rank': 100})
    assert assign_percentile_title(row_b_max, 100) == "👣 B-Class"

    # Test with different total_players
    # total_players = 20
    row_s_small = pd.Series({'Rank': 1})
    assert assign_percentile_title(row_s_small, 20) == "💎 S-Class" # 1/20 = 0.05

    row_a_small = pd.Series({'Rank': 5})
    assert assign_percentile_title(row_a_small, 20) == "✨ A-Class" # 5/20 = 0.25

    row_b_small = pd.Series({'Rank': 7})
    assert assign_percentile_title(row_b_small, 20) == "👣 B-Class" # 7/20 = 0.35
