import collections
import string
from discord.ext import commands
from discord import app_commands
import discord

class Ciphers(commands.GroupCog, name="ciphers"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="rot", description="Effectue une rotation (chiffre de César) sur le message.")
    @app_commands.describe(message="Le message à chiffrer/déchiffrer.", direction="Direction et amplitude de la rotation 0..26 (laissez vide pour bruteforce).")
    async def rot(self, interaction: discord.Interaction, message: str, direction: int = None):
        allrot = ''
        rotation_range = range(0, 26) if direction is None else [direction % 26]

        for i in rotation_range:
            upper = collections.deque(string.ascii_uppercase)
            lower = collections.deque(string.ascii_lowercase)

            upper.rotate(-i)
            lower.rotate(-i)

            upper = ''.join(list(upper))
            lower = ''.join(list(lower))
            translated = message.translate(str.maketrans(string.ascii_uppercase, upper)).translate(
                str.maketrans(string.ascii_lowercase, lower))
            allrot += '{}: {}\n'.format(i, translated)

        await interaction.response.send_message(f"```{allrot}```")

    @app_commands.command(name="atbash", description="Applique le chiffrement Atbash au message.")
    @app_commands.describe(message="Le message à chiffrer/déchiffrer.")
    async def atbash(self, interaction: discord.Interaction, message: str):
        normal = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        changed = 'zyxwvutsrqponmlkjihgfedcbaZYXWVUTSRQPONMLKJIHGFEDCBA'
        trans = str.maketrans(normal, changed)
        atbashed = message.translate(trans)
        await interaction.response.send_message(atbashed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Ciphers(bot))

