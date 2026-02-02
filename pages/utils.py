import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate
import streamlit as st

def send_welcome_email(to_email, user_name, player_name, verification_code):
    """
    認証コード付きの招待メールを送信する
    """
    
    line_invite_url = "https://line.me/ti/g/xxxxxxx" # あなたのLINEリンク
    discord_invite_url = "https://discord.gg/xxxxxxx" # あなたのDiscordリンク

    subject = "【Howl】入会承認・Discord認証コードのお知らせ"
    
    body = f"""
{user_name} 様
（プレイヤー名: {player_name}）

Howlへの入会申請が承認されました！

▼ Step 1: 以下のコミュニティに参加してください
--------------------------------------------------
✅ LINEグループ (連絡網):
line_invite_url

🎮 Discordサーバー (活動場所):
https://discord.gg/avkhBRHe
--------------------------------------------------

▼ Step 2: Discordの認証を行ってください
セキュリティのため、最初はDiscordの機能が制限されています。
サーバー参加後、「#verification」チャンネルで以下のコマンドを入力してください。

--------------------------------------------------
!verify {verification_code}
--------------------------------------------------

認証が成功すると、自動的にメンバー権限が付与されます。

--------------------------------------------------
Keio Werewolf Circle "Howl" System
--------------------------------------------------
"""

    from_addr = st.secrets["email"]["account"]
    password = st.secrets["email"]["password"]

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_email
    msg['Date'] = formatdate()

    try:
        smtpobj = smtplib.SMTP('smtp.gmail.com', 587)
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
