import discord
import random
import asyncio
from discord import app_commands
from discord.ext import commands

class CoinFlip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="pileouface", description="Lance une pièce et affiche Pile ou Face avec une animation.")
    async def pile_ou_face(self, interaction: discord.Interaction):
        """Lance une pièce avec une animation et un résultat interactif."""

        # Liste des étapes d'animation
        etats = ["🪙 En l'air...", "🪙 Tournant...", "🪙 Presque..."]
        resultat = random.choice(["Pile 🪙", "Face 🪙"])

        # Envoie le premier message d'interaction
        await interaction.response.send_message("🪙 Lancer en cours...", ephemeral=False)
        message = await interaction.original_response()

        # Animation
        for etat in etats:
            await asyncio.sleep(1)
            await message.edit(content=etat)

        # Résultat final
        await asyncio.sleep(1)
        await message.edit(content=f"🪙 {interaction.user.mention}, la pièce est tombée sur **{resultat}** !")

async def setup(bot):
    await bot.add_cog(CoinFlip(bot))
