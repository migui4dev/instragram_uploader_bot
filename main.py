import asyncio
import os
import threading
from typing import Optional, Union

import instagrapi
from flask import Flask
from instagrapi import Client
import discord
from discord import Interaction, User, Member, Attachment
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

user_using_bot: Union[User, Member, None] = None
bot = commands.Bot(intents=intents, command_prefix="!")
cl = Client()
app = Flask(__name__)


@app.route('/')
def home():
    return "Up and running :D"


async def subir_imagen(
        caption: str,
        image: discord.Attachment,
) -> None:
    cl.photo_upload(image.filename, caption=caption)
    return await asyncio.sleep(0.1)


@bot.event
async def on_ready() -> None:
    try:
        synced = await bot.tree.sync()
        print(f"Synced: {len(synced)}")
    except Exception as e:
        print(e)


@bot.tree.command(name="login")
async def login(
        interaction: Interaction,
        username: str,
        password: str,
        verification_code: Optional[str]) -> None:
    global user_using_bot

    if user_using_bot is None:
        try:
            user_using_bot = interaction.user
            await interaction.response.defer()
            cl.login(username=username, password=password, verification_code=verification_code)
            await  interaction.followup.send(f'{username} logged-in correctly!')
        except instagrapi.exceptions.BadPassword as e:
            print(e)
            await  interaction.followup.send(f'User or password are not correct.')


@bot.tree.command(name="logout")
async def logout(
        interaction: Interaction):
    global user_using_bot

    if user_using_bot is None:
        await interaction.followup.send('Not user logged-in!')
    else:
        await interaction.response.defer()
        cl.logout()
        user_using_bot = None
        await  interaction.followup.send('Logged-out correctly!')


@bot.tree.command(name="upload_post", description="It uploads a post to the currently logged-in account.")
async def upload_post_command(
        interaction: Interaction,
        caption: str,
        image: Attachment
) -> None:
    if user_using_bot is None or interaction.user.id != user_using_bot.id:
        return

    await image.save(f'./{image.filename}')

    try:
        await interaction.response.defer()
        await subir_imagen(caption=caption,
                           image=image)
        await interaction.followup.send(f'Post uploaded successfully with caption: "{caption}".')

    except instagrapi.exceptions.FeedbackRequired as e:
        print(e)
        await interaction.followup.send(
            f'Post uploaded successfully with caption: "{caption}". *You are uploading too many posts.*')
    except Exception as e:
        await interaction.followup.send(f'Oops! This is uncomfortable, but: {e}')
    finally:
        if os.path.exists(f'./{image.filename}'):
            os.remove(f'./{image.filename}')

def run_server():
    port = int(os.environ.get("PORT", 4000))
    app.run(host="0.0.0.0", port=port)

# Iniciar Flask en un hilo separado
thread = threading.Thread(target=run_server)
thread.start()

bot.run(TOKEN)
