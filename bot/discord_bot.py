import discord
from discord.ext import commands
from supabase import create_client, Client
import os
from threading import Thread
from flask import Flask

# ==========================================
# 1. Webサーバーのふりをする機能 (Keep Alive)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    # Render等のクラウドではポート指定が必要な場合があるため0.0.0.0で待受
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# 2. Discord Bot 本体
# ==========================================
# 環境変数から取得（セキュリティ対策）
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ロール名設定
MEMBER_ROLE_NAME = "Member"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# DB接続失敗を防ぐためのチェック
if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("Warning: Supabase credentials not found.")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def verify(ctx, code: str):
    if ctx.guild is None:
        await ctx.send("このコマンドはサーバー内のチャンネルで実行してください。")
        return

    try:
        response = supabase.table("players").select("*").eq("verification_code", code).execute()
        data = response.data
    except Exception as e:
        await ctx.send(f"DB Error: {e}")
        return

    if not data:
        await ctx.send("❌ 無効なコードです。")
        return

    player = data[0]
    
    try:
        role = discord.utils.get(ctx.guild.roles, name=MEMBER_ROLE_NAME)
        if role:
            await ctx.author.add_roles(role)
            
            # ニックネーム変更
            try:
                await ctx.author.edit(nick=player['name'])
            except:
                pass # 権限不足で変更できない場合はスルー
                
            # コード削除
            supabase.table("players").update({"verification_code": None}).eq("id", player['id']).execute()
            
            await ctx.send(f"✅ 認証成功！ようこそ、{player['name']}さん。")
        else:
            await ctx.send(f"⚠️ Role '{MEMBER_ROLE_NAME}' not found.")

    except Exception as e:
        await ctx.send(f"Error: {e}")

# ==========================================
# 3. 起動処理
# ==========================================
if __name__ == "__main__":
    keep_alive() # Webサーバーを裏で起動
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("Error: DISCORD_TOKEN is missing.")
