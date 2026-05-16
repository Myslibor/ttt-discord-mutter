import discord
from discord.ext import commands
from flask import Flask, request
import threading
import os
from pathlib import Path
import json
from waitress import serve

intents = discord.Intents.default()
intents.message_content = True 
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

def load_config():
    if Path("config.json").exists():
        f = open("config.json", "r", encoding="utf-8")
        f_temp = json.load(f)
        f.close()
        return f_temp
    else:
        default = {"GUILD_ID": 0, "BOT_TOKEN" : "-"}
        f = open("config.json", "w", encoding="utf-8")
        json.dump(default, f)
        f.close()
        print("Created default config")
        os._exit(0)

def load_id_map():
    if Path("id_map.json").exists():
        file = open("id_map.json",'r', encoding="utf-8")
        file_content = file.read().strip()
        file.close()
        file = open("id_map.json",'r', encoding="utf-8")
        if file_content:
            temp_f = json.load(file)
            file.close()
        else:
            temp_f = {}
            file.close()
        return temp_f
    else:
        file = open("id_map.json",'x', encoding="utf-8")
        file.close()
        return {}
    
def save_id_map(steam_dc):
    file = open("id_map.json",'w', encoding="utf-8")
    json.dump(steam_dc, file)

steam_to_discord = load_id_map()
config = load_config()
GUILD_ID = config["GUILD_ID"]
BOT_TOKEN = config["BOT_TOKEN"]

print(f"GUILD_ID set to {GUILD_ID} and BOT_TOKEN set to {BOT_TOKEN}")

app = Flask(__name__)   

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    print(f"Error: {error}")

@bot.command()
async def tttbot_map(ctx, steam_id: str):
    discord_id = ctx.author.id
    steam_to_discord[steam_id] = discord_id
    save_id_map(steam_to_discord)
    await ctx.send(f"Mapped SteamID64 {steam_id} to Discord_ID {discord_id}")

@bot.command()
async def tttbot_map_dc(ctx, steam_id: str, discord_id: str):
    discord_id_int = int(discord_id)
    steam_to_discord[steam_id] = discord_id_int
    save_id_map(steam_to_discord)
    await ctx.send(f"Mapped SteamID64 {steam_id} to Discord_ID {discord_id}")

@bot.command()
async def tttbot_map_delete(ctx, steam_id: str):
    if steam_id in steam_to_discord:
        discord_id = steam_to_discord.pop(steam_id)
        await ctx.send(f"Deleted mapping: SteamID64 {steam_id} -> Discord_ID {discord_id}")
    else:
        await ctx.send(f"No mapping found for SteamID64 {steam_id}")


@bot.command()
async def tttbot_map_reset(ctx):
    steam_to_discord.clear()
    save_id_map(steam_to_discord)
    await ctx.send("id_map has been reset")

@bot.command()
async def tttbot_map_print(ctx):
    if not steam_to_discord:
        await ctx.send("No mappings found")
        return
    
    lines = []
    for steam_id, discord_id in steam_to_discord.items():
        lines.append(f"SteamID64({steam_id}) -> Discord_ID({discord_id})")
    lines = "\n".join(lines)
    
    if len(lines) > 1900:
        for line in lines:
            await ctx.send(line)
    else:
        await ctx.send(lines)


@bot.command()
async def tttbot_end(ctx):
    await ctx.send("Shutting down")
    save_id_map(steam_to_discord)
    await bot.close()
    os._exit(0)

#death of a player
@app.route("/death", methods=["POST"])
def player_death():

    steamid = request.form.get("steamid")
    if not steamid:
        return "Missing steamid", 400

    discord_id = steam_to_discord.get(steamid)
    if not discord_id:
        print(f"No Discord mapping for SteamID64 {steamid}")
        return "No mapping", 404

    async def mute_player():
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            print("Guild not found")
            return
        member = guild.get_member(discord_id)
        if member and member.voice and not member.voice.mute:
            await member.edit(mute=True)
            print(f"Muted {member.display_name}")

    bot.loop.call_soon_threadsafe(bot.loop.create_task, mute_player())
    return "OK"

#player resurrection
@app.route("/res", methods=["POST"])
def player_res():

    steamid = request.form.get("steamid")
    if not steamid:
        return "Missing steamid", 400

    discord_id = steam_to_discord.get(steamid)

    if not discord_id:
        print(f"No Discord mapping for SteamID64 {steamid}")
        return "No mapping", 404

    async def unmute_player():
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            print("Guild not found")
            return
        member = guild.get_member(discord_id)
        if member and member.voice and member.voice.mute:
            await member.edit(mute=False)
            print(f"Unmuted {member.display_name}")

    bot.loop.call_soon_threadsafe(bot.loop.create_task, unmute_player())
    return "OK"

#new round
@app.route("/newround", methods=["POST"])
def handle_new_round():

    async def unmute_all():
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            print("Guild not found")
            return
        for vc in guild.voice_channels:
            for member in vc.members:
                if member.voice and member.voice.mute:
                    await member.edit(mute=False)
                    print(f"Unmuted {member.display_name}")

    bot.loop.call_soon_threadsafe(bot.loop.create_task,unmute_all())
    return "OK"

def run_flask():
    serve(app, host="0.0.0.0", port=5003)

def console():
    while True:
        cmd = input().strip().lower()

        if cmd == "stop":
            print("Shutting down")
            save_id_map(steam_to_discord)
            bot.loop.call_soon_threadsafe(bot.loop.create_task, bot.close())
            os._exit(0)

threading.Thread(target=run_flask).start()
threading.Thread(target=console).start()

bot.run(BOT_TOKEN) #