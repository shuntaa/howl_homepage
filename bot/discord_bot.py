cat <<EOF > bot/discord_bot.py
import discord
import os
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv
from keep_alive import keep_alive  # Webサーバー機能を読み込み

# --- 設定 ---
GUILD_ID = "1411193824415449110"
VERIFY_CHANNEL_ID = "1467609822978379818"
MEMBER_ROLE_ID = "1467608216425730231"

# 環境変数
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabase接続
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Bot準備
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.channel.id == int(VERIFY_CHANNEL_ID):
        code = message.content.strip()
        try:
            response = supabase.table("players").select("*").eq("passcode", code).execute()
            if response.data:
                player_data = response.data[0]
                if player_data.get("discord_user_id"):
                    await message.reply("⚠️ そのコードは既に使用されています。")
                    return

                user = message.author
                guild = client.get_guild(int(GUILD_ID))
                role = guild.get_role(int(MEMBER_ROLE_ID))

                if role:
                    await user.add_roles(role)
                    try:
                        await user.edit(nick=player_data['name'])
                    except:
                        pass
                    
                    supabase.table("players").update({"discord_user_id": str(user.id)}).eq("id", player_data['id']).execute()
                    await message.reply(f"✅ 認証成功！ようこそ、{player_data['name']}さん。")
                else:
                    await message.reply("❌ ロール設定エラー")
            else:
                await message.reply("❌ 無効なコードです。")
        except Exception as e:
            print(f"Error: {e}")
            await message.reply("⚠️ エラーが発生しました。")

# --- 🚀 ここが最重要！ ---
if DISCORD_TOKEN:
    keep_alive()  # Webサーバーを起動！
    client.run(DISCORD_TOKEN)
EOF
