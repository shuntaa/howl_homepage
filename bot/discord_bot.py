import discord
import os
from keep_alive import keep_alive
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

# --- 1. 設定：ここにIDを貼り付けてください ---
# ※ 数字ですが、クォーテーション " " で囲んで文字列として書いてください
GUILD_ID = "1411193824415449110"  # サーバーID
VERIFY_CHANNEL_ID = "1467609822978379818"  # #verificationチャンネルのID
MEMBER_ROLE_ID = "1467608216425730231"     # MemberロールのID
# -------------------------------------------

# 環境変数の読み込み (Render用)
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabase接続
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Botの準備
intents = discord.Intents.default()
intents.message_content = True # メッセージを読む権限
intents.members = True         # メンバー情報を扱う権限
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    print("Bot is ready to verify members!")

@client.event
async def on_message(message):
    # Bot自身のメッセージは無視
    if message.author == client.user:
        return

    # 指定された認証チャンネル以外は無視
    if message.channel.id != int(VERIFY_CHANNEL_ID):
        return

    # 入力されたコード（空白削除・大文字化）
    input_code = message.content.strip().upper()

    # HWL-から始まるコードかチェック
    if input_code.startswith("HWL-"):
        # 1. Supabaseからコードを検索
        # まだDiscord連携していない(discord_user_id is null) かつ コードが一致する人を探す
        try:
            response = supabase.table("players").select("*").eq("verification_code", input_code).execute()
            
            # データが見つかった場合
            if response.data:
                player_data = response.data[0]
                
                # すでに連携済みかチェック
                if player_data.get("discord_user_id"):
                    await message.reply("⚠️ そのコードは既に使用されています。")
                    return

                # --- 認証成功処理 ---
                user = message.author
                guild = client.get_guild(int(GUILD_ID))
                role = guild.get_role(int(MEMBER_ROLE_ID))

                if role:
                    # 1. ロールを付与
                    await user.add_roles(role)
                    
                    # 2. ニックネームを変更 (例: 824xxxxx 山田太郎)
                    new_nick = f"{player_data['student_id']} {player_data['name']}"
                    try:
                        await user.edit(nick=new_nick)
                    except Exception as e:
                        print(f"名前変更エラー: {e}") # 管理者より偉い人の名前は変えられない仕様などがあるため

                    # 3. DBにDiscord IDを紐付け
                    supabase.table("players").update({"discord_user_id": str(user.id)}).eq("id", player_data['id']).execute()

                    await message.reply(f"✅ 認証成功！ようこそ、{player_data['name']}さん。\nメンバーページへのアクセス権を付与しました。")
                
                else:
                    await message.reply("❌ エラー：ロールが見つかりません。管理者に連絡してください。")

            else:
                await message.reply("❌ 無効なコードです。もう一度確認してください。")

        except Exception as e:
            print(f"Error: {e}")
            await message.reply("⚠️ システムエラーが発生しました。")

# Bot起動
if DISCORD_TOKEN:
    keep_alive()
    client.run(DISCORD_TOKEN)
else:
    print("Error: DISCORD_TOKEN not found.")
