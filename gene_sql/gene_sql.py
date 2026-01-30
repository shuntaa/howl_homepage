import pandas as pd

def generate_sql_from_csv(input_csv, output_sql):
    # 1. データの読み込み
    df = pd.read_csv(input_csv)

    # 2. カラム名のクレンジング (改行コードや空白を削除)
    # 実データでは 'player_name\n' のようになっていたため、strip()で補正します
    df.columns = [c.strip() for c in df.columns]

    sql_statements = []
    default_date = '2024-10-01' # 過去データ用の暫定日付
    memo = "2024年データ一括移行"

    # 3. データの復元（De-aggregation）
    for _, row in df.iterrows():
        name = str(row['name']).strip()
        try:
            w = int(row['win'])
            l = int(row['lose'])
        except (ValueError, TypeError):
            continue # 数値でない行（合計行など）があればスキップ

        # 勝利数(w)と同じ数だけ、is_win=1 のレコードを生成
        for _ in range(w):
            sql_statements.append(f"('{default_date}', '{name}', 1, '{memo}')")
        
        # 敗北数(l)と同じ数だけ、is_win=0 のレコードを生成
        for _ in range(l):
            sql_statements.append(f"('{default_date}', '{name}', 0, '{memo}')")

    # 4. SQLファイルの出力
    # PostgreSQLの制限を考慮し、100行ずつのバルクインサート形式で書き出し
    if sql_statements:
        chunk_size = 100
        with open(output_sql, 'w', encoding='utf-8') as f:
            for i in range(0, len(sql_statements), chunk_size):
                chunk = sql_statements[i:i + chunk_size]
                values_str = ",\n".join(chunk)
                f.write(f"INSERT INTO match_results (game_date,name, is_win, memo) VALUES\n{values_str};\n\n")
        print(f"成功: {len(sql_statements)}件の試合データを復元し、{output_sql} に保存しました。")
    else:
        print("有効なデータが見つかりませんでした。")

# 実行
generate_sql_from_csv('input_csv.csv', 'import_howl_results24.sql')
