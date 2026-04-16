import streamlit as st
from modules._db import init_connection
import datetime
import uuid

st.set_page_config(page_title="入部申請", page_icon="📝")

st.header("📝 Howl 入部申請フォーム")

# 案内文
st.info(
    """
**【重要】入部手続きの流れ**
1. 指定口座に入部費（¥3,000）をお振り込みください（4,5月は ¥2,000）。
2. このページ下部のフォームに必要情報を入力して申請してください。
3. 会計担当が入金確認後、正式にメンバー登録されます。
"""
)

st.markdown("### 💳 振込先情報")
col1, col2 = st.columns(2)
with col1:
    st.markdown(
        """
- **金融機関名**: 三井住友銀行
- **支店名**: 810
- **預金種目**: 普通預金
"""
    )
with col2:
    st.markdown(
        """
- **口座番号**: 3854580
- **口座名義**: ドイ シユンタ
"""
    )
st.caption("振込後は、フォーム内の振込情報（名義・日付）と送金明細を必ず提出してください。")


# DB接続
try:
    supabase = init_connection()
except Exception as e:
    st.error(f"データベース接続エラー: {e}")
    st.stop()

# --- 申請フォーム ---
with st.form("join_request_form"):
    st.subheader("基本情報")
    
    # 入力項目（ユーザー指定）
    name = st.text_input("氏名（フルネーム）", placeholder="例：慶應 太郎")
    s_id = st.text_input("学籍番号", placeholder="例：824xxxxx")
    player_name = st.text_input("プレイヤーネーム（ランキングにはこの名前が表示されます）", placeholder="例：けいおう")
    email = st.text_input("慶應メールアドレス", placeholder="example@keio.jp")

    faculty_options = [
        "文学部", "経済学部", "法学部", "商学部", "医学部", "理工学部",
        "総合政策学部", "環境情報学部", "看護医療学部", "薬学部", "その他"
    ]
    faculty = st.selectbox("学部", faculty_options)

    gender = st.radio("性別", ("男性", "女性"))

    st.markdown("---")
    st.subheader("💰 振込情報確認")
    st.caption("照合のため、振込時の名義と日付を正確に入力してください。")

    col1, col2 = st.columns(2)
    transfer_name = col1.text_input("振込名義人（カナ）", placeholder="例：ケイオウ タロウ")
    transfer_date = col2.date_input("振込日", datetime.date.today())
    uploaded_file = st.file_uploader("送金明細のスクリーンショット", type=['jpg', 'png', 'jpeg'])

    submitted = st.form_submit_button("申請する", type="primary")

    if submitted:
        if not all([name, s_id, player_name, email, transfer_name, uploaded_file]):
            st.error("⚠️ すべての項目を入力・アップロードしてください。")
        elif "@" not in email:
            st.error("⚠️ 正しいメールアドレスを入力してください。")
        else:
            # ---------------------------------------------------------
            # 🛡️ 重複事前チェック (Pre-check)
            # ---------------------------------------------------------
            try:
                # 名前が被っていないか確認
                check_name = supabase.table("players").select("name").eq("name", player_name).execute()

                # メアドが被っていないか確認
                check_email = supabase.table("players").select("email").eq("email", email).execute()

                # 学籍番号が被っていないか確認（念のため）
                # ※ DBのstudent_idが数値型の場合、エラーになることがあるのでキャストする
                check_sid = supabase.table("players").select("student_id").eq("student_id", int(s_id) if s_id.isdigit() else s_id).execute()

                # 重複があればエラーを出して止める
                if check_name.data:
                    st.error(f"❌ プレイヤー名「{player_name}」は既に使用されています。別の名前にしてください。")
                    st.stop() # ここで処理を中断

                if check_email.data:
                    st.error("❌ そのメールアドレスは既に登録されています。")
                    st.stop()

                if check_sid.data:
                    st.error("❌ その学籍番号は既に登録されています。")
                    st.stop()

            except Exception as e:
                # DB接続エラーなどはここでキャッチ
                st.warning(f"重複チェック中にエラーが発生しましたが、処理を続行します: {e}")

            # ---------------------------------------------------------
            # ✅ ここまで来たら重複なし -> 申請データを送信

            image_url = None
            if uploaded_file:
                try:
                    # ファイル名をユニークにする (学籍番号_ランダム.拡張子)
                    file_ext = uploaded_file.name.split('.')[-1]
                    file_name = f"{s_id}_{uuid.uuid4()}.{file_ext}"
                    bucket_name = "receipts"

                    # アップロード実行
                    file_bytes = uploaded_file.read()
                    supabase.storage.from_(bucket_name).upload(
                        path=file_name,
                        file=file_bytes,
                        file_options={"content-type": uploaded_file.type}
                    )
                    
                    # 公開URLを取得
                    image_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
                    
                except Exception as e:
                    st.error(f"画像のアップロードに失敗しました: {e}")
                    st.stop()


            # --- ここで自動計算 (Logic) ---
            # term_number = 振込年 - 2022
            term_num = transfer_date.year - 2022

            # データ送信処理
            try:
                data = {
                    "student_name": name,
                    "student_id_number": s_id,
                    "player_name": player_name,
                    "faculty": faculty,
                    "gender": gender,
                    "email": email,
                    "transfer_name": transfer_name,
                    "transfer_date": transfer_date.isoformat(),
                    "term_number": term_num,
                    "status": "PENDING",
                    "receipt_url": image_url
                }
                supabase.table("membership_requests").insert(data).execute()

                st.success(f"✅ 申請を受け付けました！\nあなたは【{term_num}期生】として登録申請されました。\n入金確認をお待ちください。")
                st.balloons()

            except Exception as e:
                st.error(f"送信エラーが発生しました: {e}")
