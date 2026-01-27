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
st.title("🐺 人狼サークルHowlへようこそ")

page = st.sidebar.selectbox("Menu", ["About Us (Howlとは)","Leaderboard (ランキング)", "Record Result (勝敗入力)", "Social Media (SNS)"])

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



# --- ページ: About Us (Howlとは) ---
if page == "About Us (Howlとは)":
    st.header("👀 About Howl")
    
    # イントロダクション
    st.subheader("Welcome to Howl - 人狼をもっと身近に、もっと楽しく")
    st.write("""
    慶應義塾大学を拠点に活動する人狼サークル「Howl」は、
    「誰もが熱中できる居場所」を目指して活動しています。
    """)

    # 3つの特徴をカラムで表示
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🔰 初心者大歓迎")
        st.write("""
        現在、メンバーの多くが未経験からのスタートです。
        ルールから丁寧に教えるので、初めての方も安心して参加できます。
        """)
    with col2:
        st.markdown("### 📈 圧倒的な上達")
        st.write("""
        経験豊富な上級者と一緒にプレイすることで、
        議論のコツや心理戦のノウハウが自然と身につきます。
        """)
    with col3:
        st.markdown("### 🏠 アットホーム")
        st.write("""
        学年や経験を問わず、和気あいあいとした雰囲気。
        対戦が終われば、みんなで感想戦や雑談で盛り上がる温かいコミュニティです。
        """)

    st.write("---")

    # 活動の様子（Vlog/画像）
    st.subheader("🎥 Activity Highlights")
    st.write("サークルの日常やイベントの様子をチェック！")
    
    # 実際のYouTube URLがある場合はここにIDを入れてください
    # なければ st.info 等で「SNSで動画公開中」としてもOKで
    video_url = "https://www.youtube.com/watch?v=XEuJA7aBU7o?si=rz_wuIdFizNyf4ww" 
    st.video(video_url)

    # 入会案内
    st.success("✨ Howlでは新しい仲間を随時募集しています！少しでも興味を持ったら、下記のSNSリンクからお気軽にご連絡ください。")

# --- ページ1: ランキング (数理モデル実装) ---
elif page == "Leaderboard (ランキング)":
    st.header("🏆 Player Rating")
    
    df = load_data()
    
    if df.empty:
        st.info("まだ対戦データがありません。")
    else:
        # 1. 集計: プレイヤーごとの勝利数(w)と総対戦数(n)
        stats = df.groupby("player_name")["is_win"].agg(
            w="sum",   # 勝利数 (Wins)
            n="count"  # 総参加数 (Total Games)
        ).reset_index()
        
        # 2. スコア計算: Score = ((w + 1) / (n + 2)) * ln(n + 1) * 100
        stats["Score"] = ((stats["w"] + 1) / (stats["n"] + 2)) * np.log(stats["n"] + 1) * 100
        
        # 3. ソート: スコア降順
        ranking = stats.sort_values("Score", ascending=False)
        
        # ===================================================
        # [追加実装] ランクと称号の付与 (Stratification)
        # ===================================================
        
        # 3.1 順位生成 (同点は最小ランクを採用する 'min' メソッド)
        # 数学的定義: Rank(x_i) = 1 + |{x_j | Score(x_j) > Score(x_i)}|
        ranking["Rank"] = ranking["Score"].rank(ascending=False, method='min').astype(int)

        # 3.2 称号マッピング関数の定義
        # 全体集合における相対位置(Percentile)に基づくクラス分類
        total_players = len(ranking)

        def assign_percentile_title(rank_val):
            # p: 累積分布関数(CDF)における位置の近似
            p = rank_val / total_players
            if p <= 0.1: return "💎 S-Class (Top 10%)"
            if p <= 0.3: return "✨ A-Class (Top 30%)"
            if p <= 0.6: return "👣 B-Class (Top 60%)"
            return "🔰 Rookie"

        # 3.3 関数適用 (写像: Rank -> Title)
        ranking["Title"] = ranking["Rank"].apply(assign_percentile_title)
        
        # ===================================================

        # 4. 表示用整形
        # スコアを見やすく丸める
        ranking["Score"] = ranking["Score"].round(0)
        
        # カラム名の整理と列の並び替え
        # ユーザーが直感的に見やすい順序: Rank -> Title -> Name -> Score ...
        ranking = ranking.rename(columns={"w": "Wins", "n": "Games", "player_name": "Player"})
        
        # 最終的な表示列の選択と順序指定
        display_columns = ["Rank", "Title", "Player", "Score", "Wins", "Games"]
        st.dataframe(ranking[display_columns].set_index("Rank"), use_container_width=True)
        
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
            with col2:
                memo = st.text_input("メモ (任意)")
            
            st.write("---")
            st.write("勝者と敗者を選択してください")
            
            winners = st.multiselect("🏅 勝者 (Winners)", options=player_options)
            losers = st.multiselect("💀 敗者 (Losers)", options=player_options)
            
            submitted = st.form_submit_button("登録する")
            
            if submitted:
                # 集合演算による重複チェック
                if not winners and not losers:
                    st.error("参加者が選択されていません")
                elif set(winners) & set(losers): 
                    st.error("同じプレイヤーが勝者と敗者の両方に含まれています！")
                else:
                    insert_data = []
                    
                    for p in winners:
                        insert_data.append({
                            "game_date": str(game_date),
                            "player_name": p,
                            "is_win": 1, 
                            "memo": memo
                        })
                    
                    for p in losers:
                        insert_data.append({
                            "game_date": str(game_date),
                            "player_name": p,
                            "is_win": 0, 
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
            last_record = supabase.table("match_results").select("created_at").order("created_at", desc=True).limit(1).execute()
            
            if last_record.data:
                last_time = last_record.data[0]["created_at"]
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
