import streamlit as st
import pandas as pd
import random
from supabase import create_client, Client

# --- 1. Supabase接続 ---
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

def get_players():
    """プレイヤー名簿を取得"""
    response = supabase.table("players").select("name").eq("is_active", True).execute()
    return [row["name"] for row in response.data]

# --- Constants ---
PHASE_SETUP = "Setup"
PHASE_DAY = "Day"
PHASE_NIGHT = "Night"
PHASE_RESULT = "Result"

# --- Game Logic Functions ---
def assign_roles(player_names, roles_config):
    roles = sum([[role] * count for role, count in roles_config.items()], [])
    random.shuffle(roles)
    
    return [
        {"name": name, "role": roles[i], "status": "生存", "team": "人狼" if roles[i] in ["人狼", "狂人"] else "市民"}
        for i, name in enumerate(player_names)
    ]

def get_players_by_status(status="生存"):
    return [p for p in st.session_state.players if p["status"] == status]

def check_game_over():
    living_players = get_players_by_status("生存")
    werewolf_count = sum(1 for p in living_players if p["role"] == "人狼")
    human_count = sum(1 for p in living_players if p["team"] == "市民")
    
    if werewolf_count == 0: return "市民チームの勝利"
    if werewolf_count >= human_count: return "人狼チームの勝利"
    return None

# --- UI Rendering Functions ---
def render_sidebar_status():
    st.sidebar.markdown("---")
    st.sidebar.header("ゲーム状況")
    if st.session_state.game_phase in [PHASE_DAY, PHASE_NIGHT, PHASE_RESULT]:
        st.sidebar.metric("経過日数", f"{st.session_state.turn_count} 日目")
        living_players = len(get_players_by_status("生存"))
        total_players = len(st.session_state.players)
        st.sidebar.metric("生存者", f"{living_players} / {total_players} 名")
    else:
        st.sidebar.info("ゲーム開始前です。")

def render_setup_phase():
    st.header("Phase 1: Setup")
    st.info("参加者と役職の数を設定してください。")

    player_options = get_players()

    with st.form("setup_form"):
        player_names = st.multiselect("参加者リスト", options=player_options, help="データベースから参加者を選択してください。")
        st.subheader("役職構成")
        col1, col2 = st.columns(2)
        with col1:
            num_werewolf = st.number_input("人狼", min_value=1, value=1)
            num_seer = st.number_input("占い師", min_value=0, value=1)
        with col2:
            num_madman = st.number_input("狂人", min_value=0, value=1)
            num_knight = st.number_input("騎士", min_value=0, value=1)
            num_psychic = st.number_input("霊能者", min_value=0, value=1)

        total_players = len(player_names)
        num_roles = num_werewolf + num_madman + num_seer + num_knight + num_psychic
        num_villager = total_players - num_roles
        st.metric("市民の数", f"{num_villager} 名")

        if st.form_submit_button("ゲーム開始"):
            if num_villager < 0: st.error("役職の合計が参加者数を超えています！")
            elif total_players == 0: st.error("参加者が入力されていません。")
            else:
                roles_config = {"人狼": num_werewolf, "狂人": num_madman, "占い師": num_seer, "騎士": num_knight, "霊能者": num_psychic, "市民": num_villager}
                st.session_state.players = assign_roles(player_names, roles_config)
                st.session_state.game_phase = PHASE_DAY
                st.session_state.turn_count = 1
                st.session_state.game_logs.append("--- ゲーム開始 ---")
                st.rerun()

def render_day_phase():
    st.header(f"Phase 2: Day (Day {st.session_state.turn_count})")
    st.info("議論の時間です。生存者の中から追放する人物を一人選んでください。")

    # --- Psychic's result ---
    if st.session_state.turn_count > 1:
        psychic = next((p for p in get_players_by_status("生存") if p["role"] == "霊能者"), None)
        if psychic:
            # Find the log of the last execution
            last_execution_log = None
            for log in reversed(st.session_state.game_logs):
                if "が処刑されました。" in log:
                    last_execution_log = log
                    break
            
            if last_execution_log:
                executed_player_name = last_execution_log.split(" ")[2]
                executed_player = next((p for p in st.session_state.players if p["name"] == executed_player_name), None)
                if executed_player:
                    is_werewolf = executed_player["role"] == "人狼"
                    st.markdown("【霊能結果: " + executed_player_name + "】 -> " + ('<span style="color: red;">● 人狼</span>' if is_werewolf else '○ 人狼ではない'), unsafe_allow_html=True)

    with st.form("execution_form"):
        living_player_names = [p["name"] for p in get_players_by_status("生存")]
        executed_player = st.selectbox("処刑対象", living_player_names)
        
        if st.form_submit_button("処刑実行"):
            for p in st.session_state.players:
                if p["name"] == executed_player: p["status"] = "死亡"
            
            st.session_state.game_logs.append(f"Day {st.session_state.turn_count}: {executed_player} が処刑されました。")
            winner = check_game_over()
            if winner:
                st.session_state.game_phase = PHASE_RESULT
                st.session_state.game_logs.append(f"--- {winner} ---")
            else:
                st.session_state.game_phase = PHASE_NIGHT
            st.rerun()

def render_night_phase():
    st.header(f"Phase 3: Night (Day {st.session_state.turn_count})")
    st.info("夜の行動時間です。各役職の行動を選択し、最後にボタンを押してください。")

    living_players = get_players_by_status("生存")
    living_names = [p["name"] for p in living_players]
    
    seer = next((p for p in living_players if p["role"] == "占い師"), None)
    knight = next((p for p in living_players if p["role"] == "騎士"), None)
    werewolf_names = [p["name"] for p in living_players if p["role"] == "人狼"]

    with st.form("night_action_form"):
        st.subheader("🌙 夜のアクション")
        attack_target = st.selectbox("🐺 人狼の襲撃対象", [n for n in living_names if n not in werewolf_names], index=None, placeholder="襲撃しない場合は選択しないでください")
        seer_target = st.selectbox("🔮 占い師の占い対象", [n for n in living_names if n != seer["name"]] if seer else [], index=None, placeholder="生存していません" if not seer else "占わない場合は選択しないでください")
        guard_target = st.selectbox("🛡️ 騎士の護衛対象", [n for n in living_names if n != knight["name"]] if knight else [], index=None, placeholder="生存していません" if not knight else "護衛しない場合は選択しないでください")

        if st.form_submit_button("夜の行動を終了"):
            if seer and seer_target:
                target_player = next(p for p in st.session_state.players if p["name"] == seer_target)
                is_werewolf = target_player["role"] == "人狼"
                st.markdown("【占い結果: " + seer_target + "】 -> " + ('<span style="color: red;">● 人狼</span>' if is_werewolf else '○ 人狼ではない'), unsafe_allow_html=True)

            if attack_target and guard_target != attack_target:
                for p in st.session_state.players:
                    if p["name"] == attack_target: p["status"] = "死亡"
                st.session_state.game_logs.append(f"Night {st.session_state.turn_count}: {attack_target} が襲撃されました。")
            else:
                st.session_state.game_logs.append(f"Night {st.session_state.turn_count}: {'襲撃は護衛された。' if attack_target else '誰も襲撃されませんでした。'}")
            
            winner = check_game_over()
            if winner:
                st.session_state.game_phase = PHASE_RESULT
                st.session_state.game_logs.append(f"--- {winner} ---")
            else:
                st.session_state.game_phase = PHASE_DAY
                st.session_state.turn_count += 1
            st.rerun()

def render_result_phase():
    st.header("Phase 4: Result")
    winner_message = st.session_state.game_logs[-1]
    st.balloons()
    
    if "人狼チーム" in winner_message: st.error(f"## {winner_message}")
    else: st.success(f"## {winner_message}")

    if st.button("✨ 新しいゲームを始める"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- Main App ---
st.set_page_config(page_title="GM Tool", layout="wide")
st.title("🐺 GM Tool (Offline)")

if 'game_phase' not in st.session_state:
    st.session_state.game_phase = PHASE_SETUP
    st.session_state.players = []
    st.session_state.turn_count = 0
    st.session_state.game_logs = []

# --- Page Routing ---
if st.session_state.game_phase == PHASE_SETUP: render_setup_phase()
elif st.session_state.game_phase == PHASE_DAY: render_day_phase()
elif st.session_state.game_phase == PHASE_NIGHT: render_night_phase()
elif st.session_state.game_phase == PHASE_RESULT: render_result_phase()

# --- Common UI Elements ---
render_sidebar_status()

if st.session_state.game_phase != PHASE_SETUP:
    with st.expander("GM用: 役職とステータス確認", expanded=False):
        df = pd.DataFrame(st.session_state.players)

        # Custom sort: 1. Living WW, 2. Living Others, 3. Dead
        df['sort_key'] = df.apply(
            lambda row: 1 if row['status'] == '生存' and row['role'] == '人狼' 
            else (2 if row['status'] == '生存' else 3),
            axis=1
        )
        df_sorted = df.sort_values('sort_key').drop(columns=['sort_key', 'team'])

        def style_rows(row):
            if row['status'] == '死亡':
                return ['text-decoration: line-through'] * len(row)
            return [''] * len(row)

        st.dataframe(df_sorted.set_index("name").style.apply(style_rows, axis=1))
    
    with st.expander("ゲームログ"):
        st.text_area("Log", value="\n".join(st.session_state.game_logs), height=200, disabled=True)
