"""
GM Tool - 人狼ゲーム進行支援ツール
UIとロジックを分離した構成。pages/_db.py でDB接続・操作を行う。
"""
import streamlit as st
import pandas as pd
import random
from datetime import date
from pages._db import init_connection, get_active_players_info, insert_match_results

# --- Constants ---
PHASE_SETUP = "Setup"
PHASE_DAY = "Day"
PHASE_NIGHT = "Night"
PHASE_RESULT = "Result"

# --- DB接続 ---
try:
    supabase = init_connection()
except Exception:
    supabase = None


# ========== Game Logic Functions ==========

def assign_roles(players_info, roles_config):
    """参加者に役職をランダム割り当て"""
    roles = sum([[role] * count for role, count in roles_config.items()], [])
    random.shuffle(roles)

    return [
        {
            "student_id": info["student_id"],
            "name": info["name"],
            "role": roles[i],
            "status": "生存",
            "team": "人狼" if roles[i] in ["人狼", "狂人"] else "市民",
        }
        for i, info in enumerate(players_info)
    ]


def get_players_by_status(players, status="生存"):
    """指定ステータスのプレイヤー一覧を取得"""
    return [p for p in players if p["status"] == status]


def check_game_over(players):
    """勝敗判定"""
    living_players = get_players_by_status(players, "生存")
    werewolf_count = sum(1 for p in living_players if p["role"] == "人狼")
    human_count = sum(1 for p in living_players if p["team"] == "市民")

    if werewolf_count == 0:
        return "市民チームの勝利"
    if werewolf_count >= human_count:
        return "人狼チームの勝利"
    return None


def get_last_executed_player_id(game_logs):
    """直近の処刑ログから処刑されたプレイヤーのIDを取得"""
    for log in reversed(game_logs):
        if "が処刑されました。" in log:
            # "Day 1: PlayerName (12345) が処刑されました。" -> "12345"
            try:
                return int(log.split("(")[1].split(")")[0])
            except (IndexError, ValueError):
                return None
    return None


# ========== UI Rendering Functions ==========

def render_sidebar_status(players, game_phase, turn_count):
    """サイドバーにゲーム状況を表示"""
    st.sidebar.markdown("---")
    st.sidebar.header("ゲーム状況")
    if game_phase in [PHASE_DAY, PHASE_NIGHT, PHASE_RESULT]:
        st.sidebar.metric("経過日数", f"{turn_count} 日目")
        living_players = len(get_players_by_status(players, "生存"))
        total_players = len(players)
        st.sidebar.metric("生存者", f"{living_players} / {total_players} 名")

        st.sidebar.subheader("生存状況")
        for player in sorted(players, key=lambda p: p["name"]):
            if player["status"] == "死亡":
                st.sidebar.markdown(f"<s>{player['name']}</s>", unsafe_allow_html=True)
            else:
                st.sidebar.write(f"・{player['name']}")
    else:
        st.sidebar.info("ゲーム開始前です。")


def render_setup_phase(supabase_client):
    """Phase 1: Setup - 参加者と役職設定"""
    st.header("Phase 1: Setup")
    st.info("参加者と役職の数を設定してください。")

    players_info = get_active_players_info(supabase_client)
    player_options = {player['student_id']: player['name'] for player in players_info}

    with st.form("setup_form"):
        selected_student_ids = st.multiselect(
            "参加者リスト",
            options=list(player_options.keys()),
            format_func=lambda x: player_options[x],
            help="データベースから参加者を選択してください。",
        )
        total_players = len(selected_student_ids)

        st.subheader("役職構成")
        col1, col2 = st.columns(2)

        with col1:
            num_werewolf = st.number_input("人狼", min_value=1, value=1)
            num_seer = st.number_input("占い師", min_value=0, value=1)
            num_knight = st.number_input("騎士", min_value=0, value=1)

        with col2:
            num_madman = st.number_input("狂人", min_value=0, value=1)
            num_psychic = st.number_input("霊能者", min_value=0, value=1)

            num_roles_except_villagers = (
                num_werewolf + num_madman + num_seer + num_knight + num_psychic
            )
            default_villagers = total_players - num_roles_except_villagers
            num_villager = st.number_input(
                "市民", min_value=0, value=max(0, default_villagers)
            )

        total_roles = (
            num_werewolf + num_madman + num_seer + num_knight + num_psychic + num_villager
        )
        if st.form_submit_button("ゲーム開始"):
            if total_roles != total_players:
                st.error(
                    f"役職の合計({total_roles}名)が参加者数({total_players}名)と一致しません！"
                )
            elif total_players == 0:
                st.error("参加者が入力されていません。")
            else:
                roles_config = {
                    "人狼": num_werewolf,
                    "狂人": num_madman,
                    "占い師": num_seer,
                    "騎士": num_knight,
                    "霊能者": num_psychic,
                    "市民": num_villager,
                }
                selected_players_info = [p for p in players_info if p['student_id'] in selected_student_ids]
                st.session_state.players = assign_roles(selected_players_info, roles_config)
                st.session_state.game_phase = PHASE_DAY
                st.session_state.turn_count = 1
                st.session_state.game_logs.append("--- ゲーム開始 ---")
                st.rerun()


def render_day_phase():
    """Phase 2: Day - 議論・処刑"""
    st.header(f"Phase 2: Day (Day {st.session_state.turn_count})")
    st.info("議論の時間です。生存者の中から追放する人物を一人選んでください。")

    players = st.session_state.players
    living_players = get_players_by_status(players, "生存")

    # --- Seer's result ---
    if "seer_result" in st.session_state and st.session_state.seer_result:
        st.markdown(st.session_state.seer_result, unsafe_allow_html=True)
        st.session_state.seer_result = None

    # --- Psychic's result ---
    if st.session_state.turn_count > 1:
        psychic = next(
            (p for p in living_players if p["role"] == "霊能者"), None
        )
        if psychic:
            executed_id = get_last_executed_player_id(st.session_state.game_logs)
            if executed_id:
                executed_player = next(
                    (p for p in players if p["student_id"] == executed_id), None
                )
                if executed_player:
                    is_werewolf = executed_player["role"] == "人狼"
                    st.markdown(
                        "【霊能結果: "
                        + executed_player['name']
                        + "】 -> "
                        + (
                            '<span style="color: red;">● 人狼</span>'
                            if is_werewolf
                            else "○ 人狼ではない"
                        ),
                        unsafe_allow_html=True,
                    )

    with st.form("execution_form"):
        living_player_options = {p['student_id']: p['name'] for p in living_players}
        executed_player_id = st.selectbox("処刑対象", list(living_player_options.keys()), format_func=lambda x: living_player_options[x])

        if st.form_submit_button("処刑実行"):
            executed_player_name = ""
            for p in players:
                if p["student_id"] == executed_player_id:
                    p["status"] = "死亡"
                    executed_player_name = p['name']

            st.session_state.game_logs.append(
                f"Day {st.session_state.turn_count}: {executed_player_name} ({executed_player_id}) が処刑されました。"
            )
            winner = check_game_over(players)
            if winner:
                st.session_state.game_phase = PHASE_RESULT
                st.session_state.game_logs.append(f"--- {winner} ---")
            else:
                st.session_state.game_phase = PHASE_NIGHT
            st.rerun()


def render_night_phase():
    """Phase 3: Night - 夜のアクション"""
    st.header(f"Phase 3: Night (Day {st.session_state.turn_count})")
    st.info("夜の行動時間です。各役職の行動を選択し、最後にボタンを押してください。")

    players = st.session_state.players
    living_players = get_players_by_status(players, "生存")
    living_player_options = {p['student_id']: p['name'] for p in living_players}

    seer = next((p for p in living_players if p["role"] == "占い師"), None)
    knight = next((p for p in living_players if p["role"] == "騎士"), None)
    werewolf_ids = [p["student_id"] for p in living_players if p["role"] == "人狼"]

    with st.form("night_action_form"):
        st.subheader("🌙 夜のアクション")
        attack_target_id = st.selectbox(
            "🐺 人狼の襲撃対象",
            [id for id in living_player_options.keys() if id not in werewolf_ids],
            index=None,
            placeholder="襲撃しない場合は選択しないでください",
            format_func=lambda x: living_player_options[x]
        )
        seer_target_id = st.selectbox(
            "🔮 占い師の占い対象",
            [id for id in living_player_options.keys() if id != seer["student_id"]] if seer else [],
            index=None,
            placeholder="生存していません" if not seer else "占わない場合は選択しないでください",
            format_func=lambda x: living_player_options[x]
        )
        guard_target_id = st.selectbox(
            "🛡️ 騎士の護衛対象",
            [id for id in living_player_options.keys() if id != knight["student_id"]] if knight else [],
            index=None,
            placeholder="生存していません" if not knight else "護衛しない場合は選択しないでください",
            format_func=lambda x: living_player_options[x]
        )

        if st.form_submit_button("夜の行動を終了"):
            if seer and seer_target_id:
                target_player = next(
                    p for p in players if p["student_id"] == seer_target_id
                )
                is_werewolf = target_player["role"] == "人狼"
                st.session_state.seer_result = (
                    "【占い結果: "
                    + target_player['name']
                    + "】 -> "
                    + (
                        '<span style="color: red;">● 人狼</span>'
                        if is_werewolf
                        else "○ 人狼ではない"
                    )
                )
            else:
                st.session_state.seer_result = None

            if attack_target_id and guard_target_id != attack_target_id:
                attacked_player_name = ""
                for p in players:
                    if p["student_id"] == attack_target_id:
                        p["status"] = "死亡"
                        attacked_player_name = p['name']
                st.session_state.game_logs.append(
                    f"Night {st.session_state.turn_count}: {attacked_player_name} ({attack_target_id}) が襲撃されました。"
                )
            else:
                st.session_state.game_logs.append(
                    f"Night {st.session_state.turn_count}: "
                    + (
                        "襲撃は護衛された。"
                        if attack_target_id
                        else "誰も襲撃されませんでした。"
                    )
                )

            winner = check_game_over(players)
            if winner:
                st.session_state.game_phase = PHASE_RESULT
                st.session_state.game_logs.append(f"--- {winner} ---")
            else:
                st.session_state.game_phase = PHASE_DAY
                st.session_state.turn_count += 1
            st.rerun()


def render_result_phase(supabase_client):
    """Phase 4: Result - 結果表示・ランキング登録"""
    st.header("Phase 4: Result")
    winner_message = st.session_state.game_logs[-1]
    st.balloons()

    if "人狼チーム" in winner_message:
        st.error(f"## {winner_message}")
        winning_team = "人狼"
    else:
        st.success(f"## {winner_message}")
        winning_team = "市民"

    st.write("---")
    st.subheader("📝 Record Match Result")

    players = st.session_state.players
    player_options = {p["student_id"]: p["name"] for p in players}
    winners_default = [p["student_id"] for p in players if p["team"] == winning_team]
    losers_default = [p["student_id"] for p in players if p["team"] != winning_team]

    with st.form("result_form"):
        game_date = st.date_input("日付", date.today())
        memo = st.text_input("メモ (任意)", f"{st.session_state.turn_count}日で決着")

        st.write("---")
        st.write("勝者と敗者を確認・修正してください")

        winners = st.multiselect(
            "🏅 勝者 (Winners)", options=list(player_options.keys()), default=winners_default, format_func=lambda x: player_options[x]
        )
        losers = st.multiselect(
            "💀 敗者 (Losers)", options=list(player_options.keys()), default=losers_default, format_func=lambda x: player_options[x]
        )

        st.write("---")
        password = st.text_input("幹部用パスワード", type="password")

        submitted = st.form_submit_button("ランキングに登録")

        if submitted:
            admin_password = st.secrets.get("admin", {}).get("password")
            if not admin_password:
                st.error("管理者パスワードが設定されていません。.streamlit/secrets.tomlを確認してください。")
            elif password == admin_password:
                if not winners and not losers:
                    st.error("参加者が選択されていません")
                elif set(winners) & set(losers):
                    st.error("同じプレイヤーが勝者と敗者の両方に含まれています！")
                else:
                    insert_data = []
                    for p_id in winners:
                        insert_data.append(
                            {
                                "game_date": str(game_date),
                                "student_id": p_id,
                                "is_win": 1,
                                "memo": memo,
                            }
                        )
                    for p_id in losers:
                        insert_data.append(
                            {
                                "game_date": str(game_date),
                                "student_id": p_id,
                                "is_win": 0,
                                "memo": memo,
                            }
                        )

                    try:
                        insert_match_results(supabase_client, insert_data)
                        st.success(
                            f"登録完了！ (勝者: {len(winners)}名, 敗者: {len(losers)}名)"
                        )
                    except Exception as e:
                        st.error(f"エラー: {e}")
            else:
                st.error("パスワードが違います")

    st.write("---")
    if st.button("✨ 新しいゲームを始める"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def render_gm_panel(players):
    """GM用: 役職・ステータス確認パネル"""
    df = pd.DataFrame(players)
    df["sort_key"] = df.apply(
        lambda row: (
            1
            if row["status"] == "生存" and row["role"] == "人狼"
            else (2 if row["status"] == "生存" else 3)
        ),
        axis=1,
    )
    df_sorted = df.sort_values("sort_key").drop(columns=["sort_key", "team"])

    def style_rows(row):
        if row["status"] == "死亡":
            return ["text-decoration: line-through"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df_sorted.set_index("name").style.apply(style_rows, axis=1)
    )


# ========== Main App ==========

st.title("🐺 Game")

if supabase is None:
    st.error("データベースに接続できませんでした。.streamlit/secrets.toml を確認してください。")
    st.stop()

# --- Session State 初期化 ---
if "game_phase" not in st.session_state:
    st.session_state.game_phase = PHASE_SETUP
    st.session_state.players = []
    st.session_state.turn_count = 0
    st.session_state.game_logs = []

players = st.session_state.players
game_phase = st.session_state.game_phase
turn_count = st.session_state.turn_count

# --- Page Routing ---
if game_phase == PHASE_SETUP:
    render_setup_phase(supabase)
elif game_phase == PHASE_DAY:
    render_day_phase()
elif game_phase == PHASE_NIGHT:
    render_night_phase()
elif game_phase == PHASE_RESULT:
    render_result_phase(supabase)

# --- Common UI Elements ---
render_sidebar_status(players, game_phase, turn_count)

if game_phase != PHASE_SETUP:
    with st.expander("GM用: 役職とステータス確認", expanded=False):
        render_gm_panel(players)

    with st.expander("ゲームログ"):
        st.text_area(
            "Log",
            value="\n".join(st.session_state.game_logs),
            height=200,
            disabled=True,
        )
