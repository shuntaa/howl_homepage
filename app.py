import streamlit as st
from supabase import create_client, Client
import pandas as pd
import numpy as np # 数学関数(log)を使うために追加
from datetime import date, timedelta

# --- 1. Supabase接続 ---
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

# --- 2. ページ設定 ---
st.set_page_config(page_title="Howl Official", layout="wide")
st.title("🐺 人狼サークルHowlへようこそ")

page = st.sidebar.selectbox("Menu", ["About Us (Howlとは)","Schedule / Next Game（次回活動予定）", "Member Profiles (メンバー紹介)","Leaderboard (ランキング)", "Rule (ルール説明)"])

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

def assign_percentile_title(rank_val, total_players):
    # p: 累積分布関数(CDF)における位置の近似
    p = rank_val / total_players
    if p <= 0.1: return "💎 S-Class (Top 10%)"
    if p <= 0.3: return "✨ A-Class (Top 30%)"
    if p <= 0.6: return "👣 B-Class (Top 60%)"
    return "🔰 Rookie"



# --- ページ: About Us (Howlとは) ---
if page == "About Us (Howlとは)":
    st.header("About Us")
    
    # イントロダクション
    st.subheader("Welcome to Howl ~ 人狼をもっと身近に、もっと楽しく ~")
    st.write("""
    慶應義塾大学を拠点に活動する人狼サークル「Howl」は、
    「誰もが熱中できる居場所」を目指して活動しています。
    """)
    
    st.write("")
    st.write("")
    
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

    st.subheader("🔗 Our Social Media")
    
    st.markdown("🔗 [公式Line](https://line.me/R/ti/p/@290bixgt)")
    st.markdown("🔗 [Instagram](https://www.instagram.com/keio_howl)")
    st.markdown("🔗 [X (Twitter)](https://x.com/keio_howl?s=21&t=TriTKMLwbruJApWYrQQ3eA)")
    st.markdown("🔗 [YouTube](https://youtube.com/channel/UCpXfFc7T2f0tG6mBApIfnlA?si=QqCmmo-xRIMLsGMq)")


# --- ページ: Schedule / Next Game（次回活動予定） ---
elif page == "Schedule / Next Game（次回活動予定）":
    st.header("📅 Schedule / Next Game")

    # 次回イベントまでのカウントダウン
    event_date = date(2026, 2, 16)  # ユーザーから提供されたイベント日付
    today = date.today()
    days_until_event = (event_date - today).days

    if days_until_event > 0:
        st.subheader(f"次のイベントまであと... {days_until_event} 日！ 🎉")
    elif days_until_event == 0:
        st.subheader("本日イベント開催！お見逃しなく！🎉")
    else:
        st.subheader("イベントは終了しました。次回のイベントをお楽しみに！")
    
    st.write("---")
    
    # Google Calendar Embed
    st.write("### 次回活動予定")
    st.components.v1.html('<iframe src="https://calendar.google.com/calendar/embed?src=keiowerewolf.howl%40gmail.com&ctz=Asia%2FTokyo" style="border: 0" width="800" height="600" frameborder="0" scrolling="no"></iframe>', height=600)


# --- ページ: Member Profiles (メンバー紹介) ---
elif page == "Member Profiles (メンバー紹介)":
    st.header("👥 Member Profiles")
    st.write("Howlを彩る個性豊かなメンバーを紹介します。")
    st.write("") # スペース

    # 1. メンバーデータの定義 (将来的にここを増やすだけでOK)
    # 写真は URL または ローカルのパスを指定します
    members = [
        {
            "name": "土居 隼大(どい しゅんた)",
            "image": "img/member_shunta.JPEG", # サンプル画像URL
            "message": "人狼ゲームをここ慶應で展開したい!そんな思いで2023年にHowlを設立しました。数十年後のHowl存続を願って、卒業までにどんどん改革していきます！"
        },
        {
            "name": "山本 祐大(やまもと ゆうだい)",
            "image": "img/member_yamayu.webp",
            "message": "アットホームな雰囲気が大好きです。対戦後の感想戦も楽しみましょう！"
        },
        {
            "name": "Member C",
            "image": "https://via.placeholder.com/150",
            "message": "Vlogも作っています。サークルの楽しさを広めていきたいです！"
        }
    ]

    # 2. 表示（3列構成でループ）
    # リストを3つずつの塊（chunk）に分けて表示
    cols = st.columns(3)
    
    for i, member in enumerate(members):
        col_idx = i % 3 # 0, 1, 2 のインデックスを繰り返す
        with cols[col_idx]:
            # 名前を強調
            st.subheader(member["name"])
            # 写真を表示 (use_container_widthで枠に合わせる)
            st.image(member["image"], use_container_width=True)
            # メッセージ
            st.info(member["message"])
            st.write("") # メンバー間の余白


# --- ページ1: ランキング (数理モデル実装) ---
elif page == "Leaderboard (ランキング)":
    st.header("🏆 Player Rating")

    # --- データ表示 ---
    df = load_data()

    if df.empty:
        st.info("まだ対戦データがありません。")
    else:
        stats = df.groupby("player_name")["is_win"].agg(w="sum", n="count").reset_index()
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

    st.write("---")

    # --- 結果入力セクション ---
    if st.button("勝敗を入力する"):
        # ボタンが押されたら編集モードをトグルする代わりに、常にTrueに設定
        st.session_state.editing = True

    # 編集モードがアクティブな場合のみ表示
    if st.session_state.get("editing", False):
        
        # 認証ロジック
        if not st.session_state.get("authenticated", False):
            st.header("🔒 Admin Login")
            password = st.text_input("幹部用パスワード", type="password", key="password_input")
            if st.button("Login"):
                if password == st.secrets["admin"]["password"]:
                    st.session_state.authenticated = True
                    st.rerun() # ログイン成功後、再実行してフォームを表示
                else:
                    st.error("パスワードが違います")
            
            # 閉じるボタンは認証前にも表示
            if st.button("閉じる"):
                st.session_state.editing = False
                st.rerun()
        
        # 認証済みの場合にフォームを表示
        else:
            st.header("📝 Record Match Result")
            with st.form("result_form"):
                player_options = get_players()
                col1, col2 = st.columns(2)
                with col1:
                    game_date = st.date_input("日付", date.today())
                with col2:
                    memo = st.text_input("メモ (任意)")
                
                st.write("勝者と敗者を選択してください")
                winners = st.multiselect("🏅 勝者 (Winners)", options=player_options)
                losers = st.multiselect("💀 敗者 (Losers)", options=player_options)
                
                submitted = st.form_submit_button("登録する")
                
                if submitted:
                    if not winners and not losers:
                        st.error("参加者が選択されていません")
                    elif set(winners) & set(losers):
                        st.error("同じプレイヤーが勝者と敗者の両方に含まれています！")
                    else:
                        insert_data = []
                        for p in winners:
                            insert_data.append({"game_date": str(game_date), "player_name": p, "is_win": 1, "memo": memo})
                        for p in losers:
                            insert_data.append({"game_date": str(game_date), "player_name": p, "is_win": 0, "memo": memo})
                        
                        try:
                            supabase.table("match_results").insert(insert_data).execute()
                            st.success(f"登録完了！ (勝者: {len(winners)}名, 敗者: {len(losers)}名)")
                            st.session_state.editing = False # 成功したら編集モードを終了
                            st.rerun()
                        except Exception as e:
                            st.error(f"エラー: {e}")

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

            if st.button("閉じる"):
                st.session_state.editing = False
                st.rerun()

elif page == "Rule (ルール説明)":
    st.header("ルール説明")
    
    # イントロダクション
    st.subheader("ゲームの流れ")
    st.write("""
    人狼ゲームは、プレイヤーが「市民陣営」と「人狼陣営」に分かれて互いの正体を隠しながら議論し、相手を欺き、自陣営の勝利を目指すゲームです。
    1. 日付の変更：昼から夜になります。また、夜から昼になります。
    2. 夜の活動：人狼は襲い、占い師や霊媒師は能力を使用します。
    3. 朝：人狼が襲ったプレイヤーが明らかになります。また、占い師や霊媒師が得た情報が共有されます。
    4. 議論：生存しているプレイヤーは、朝の情報を元に最も怪しいプレイヤーが誰であるかを話し合います。
    5. 処刑：生存しているプレイヤーは投票を行い、一人の人物を処刑します。
    人間チームが人狼を全て倒すか、人狼チームが人間の人数が人狼の人数以下になるまで残っているとゲームが終了します。
    """)
    
    st.write("")
    st.write("")
    
    st.subheader("各役職の説明")

    # 3つの特徴をカラムで表示
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🐺 人狼")
        st.write("""
        市民を欺き、毎晩一人ずつ襲撃します。正体を知られないように、市民のふりをします。
        """)
        st.markdown("### 🔮 占い師")
        st.write("""
        毎晩、生存者の中から一人を選び、その人が「人狼」か「人狼でない」かを知ることができます。
        """)
        st.markdown("### 🔍 霊媒師")
        st.write("""
        毎晩、その日に処刑された人が「人狼」か「人狼でない」かを知ることができます。
        """)
    with col2:
        st.markdown("### 🤪 狂人")
        st.write("""
        人狼の勝利が自身の勝利です。人狼が誰かは知りませんが、占い師や霊媒師を騙って議論を混乱させ、人狼を助けます。
        """)
        st.markdown("### 🛡️ 騎士")
        st.write("""
        毎晩、生存者の中から一人を選び、人狼の襲撃から守ることができます。ただし、自分自身を守ることはできません。
        """)
        st.markdown("### 🧑‍🌾 市民")
        st.write("""
        特別な能力はありません。議論を通じて人狼を見つけ出し、投票で処刑することが目標です。
        """)
    with col3:
        st.markdown("### 🐈‍⬛ 黒猫")
        st.write("""
        人狼の味方です。処刑されると、市民陣営からランダムで1名を道連れにします。
        人狼に襲撃された場合は、能力は発動せずそのまま死亡します。
        """)
        st.markdown("### 🐈 猫又")
        st.write("""
        襲撃されると、人狼を1名道連れにします。処刑されると、全生存者からランダムで1名を道連れにするため、味方を殺す危険もあります。
        """)
        st.markdown("### 🦊 妖狐")
        st.write("""
        市民陣営でも人狼陣営でもありません。ゲーム終了時に生き残っていれば一人勝ちです。人狼に襲撃されても死にませんが、占い師に占われると死んでしまいます。
        """)
    st.write("---")

    # 活動の様子（Vlog/画像）
    st.subheader("Advanced: 専門用語の解説")
    st.write("議論で出てくる用語をチェック！")

    st.markdown("### グレー")
    st.write("占い師から「人狼」とも「人狼でない」とも言われていない、正体が不明なプレイヤーのこと。")
    st.markdown("### ローラー")
    st.write("特定の役職を騙るプレイヤーが複数人現れた場合、その全員を処刑すること。")
    st.markdown("### 騙り")
    st.write("人狼や狂人が、占い師や霊媒師などの役職を偽って名乗り出ること。")
    st.markdown("### 連ガ")
    st.write("騎士が同じ人物を連続して守ること。")


