#!/usr/bin/env python3

import discord
from discord.ext import commands
import os
import asyncio

# Configurar intents
intents = discord.Intents.default()
intents.message_content = True

# Criar bot com commands.Bot
bot = commands.Bot(
    command_prefix='!test ',
    intents=intents,
    help_command=None
)

@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} conectado!')
    print(f'📊 Servidores: {len(bot.guilds)}')

@bot.event  
async def on_message(message):
    if message.author == bot.user:
        return
    
    if bot.user in message.mentions:
        await message.reply("Olá! Sou o Oráculo de Concursos!")

async def main():
    token = os.getenv('DISCORD_TOKEN')
    print(f"🔌 Conectando com token: {token[:20]}...")
    
    try:
        await asyncio.wait_for(bot.start(token), timeout=30.0)
    except asyncio.TimeoutError:
        print("❌ Timeout na conexão")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    asyncio.run(main())