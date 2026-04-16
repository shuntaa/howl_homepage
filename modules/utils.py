import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate
import streamlit as st

def _send_email(subject, body, to_email):
    from_addr = st.secrets["email"]["account"]
    password = st.secrets["email"]["password"]

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg["Date"] = formatdate()

    try:
        smtpobj = smtplib.SMTP("smtp.gmail.com", 587)
        smtpobj.ehlo()
        smtpobj.starttls()
        smtpobj.ehlo()
        smtpobj.login(from_addr, password)
        smtpobj.sendmail(from_addr, to_email, msg.as_string())
        smtpobj.close()
        return True
    except Exception as e:
        print(f"Mail Error: {e}")
        return False

def send_welcome_email(to_email, user_name, player_name, verification_code):
    """
    認証コード付きの招待メールを送信する
    """
    
    line_invite_url = "https://line.me/ti/g/agxLzN8vCj" # あなたのLINEリンク
    discord_invite_url = "https://discord.gg/avkhBRHe" # あなたのDiscordリンク

    subject = "【Howl】入会承認・Discord認証コードのお知らせ"
    
    body = f"""
{user_name} 様
（プレイヤー名: {player_name}）

Howlへの入会申請が承認されました！

▼ Step 1: LINEグループに参加してください
--------------------------------------------------
{line_invite_url}
*年齢確認で参加できない場合、新歓LineのShuntaに本メールのスクショを送ってください！
--------------------------------------------------

▼ Step 2: Discordの認証を行ってください
セキュリティのため、最初はDiscordの機能が制限されています。
まず以下のDiscordサーバーに参加してください。
{discord_invite_url}
その後、
サーバー参加後、「#入サー手続き」チャンネルで以下のコマンドを入力してください。

--------------------------------------------------
{verification_code}
--------------------------------------------------

認証が成功すると、自動的にメンバー権限が付与されます。

ご不明点があれば、@shuntadoi27@keio.jp までご連絡ください。

--------------------------------------------------
Keio Werewolf Circle "Howl" System
--------------------------------------------------
"""

    return _send_email(subject, body, to_email)

def send_membership_request_notification(request_data, admin_email="shuntadoi27@keio.jp"):
    """
    入部申請が行われた際に、管理者へ通知メールを送信する
    """
    subject = "【Howl】新しい入部申請が届きました"

    receipt_url = request_data.get("receipt_url") or "なし"
    body = f"""
新しい入部申請が届きました。内容を確認してください。

----------------------------------------
氏名: {request_data.get("student_name", "")}
学籍番号: {request_data.get("student_id_number", "")}
プレイヤー名: {request_data.get("player_name", "")}
学部: {request_data.get("faculty", "")}
性別: {request_data.get("gender", "")}
慶應メール: {request_data.get("email", "")}
振込名義: {request_data.get("transfer_name", "")}
振込日: {request_data.get("transfer_date", "")}
明細URL: {receipt_url}
----------------------------------------
"""

    return _send_email(subject, body, admin_email)
