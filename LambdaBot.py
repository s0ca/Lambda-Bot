import discord
from discord.ext import commands
from discord import app_commands
import settings

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix='', intents=intents)

    async def setup_hook(self):
        # Charger les cogs
        await self.load_extension("cogs.music")
        await self.load_extension("cogs.administration")
        # Synchronisation des commandes slash avec Discord.
        self.tree.copy_global_to(guild=discord.Object(id=settings.GUILD))
        await self.tree.sync(guild=discord.Object(id=settings.GUILD))

bot = MyBot()

@bot.event
async def on_ready():
    print(f"{bot.user} est connecté à Discord!")

@bot.tree.command(name="source", description="Affiche le lien source du bot.")
async def source(interaction: discord.Interaction):
    await interaction.response.send_message('https://github.com/s0ca/Lambda-bot')

@bot.tree.command(name="request", description="Demande une nouvelle fonctionnalité.")
async def request(interaction: discord.Interaction, feature: str):
    creator = await bot.fetch_user(settings.OWNER)
    await creator.send(f''':pencil: {interaction.user}: {feature}''')
    await interaction.response.send_message(f''':pencil: Merci, "{feature}" a été demandé!''')

@bot.tree.command(name="report", description="Signale un bug ou une erreur.")
async def report(interaction: discord.Interaction, error_report: str):
    creator = await bot.fetch_user(settings.OWNER)
    await creator.send(f''':triangular_flag_on_post: {interaction.user}: {error_report}''')
    await interaction.response.send_message(f''':triangular_flag_on_post: Merci pour votre aide, "{error_report}" a été signalé!''')

@bot.event
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CommandInvokeError):
        await interaction.response.send_message("Une erreur est survenue lors de l'exécution de la commande.")

if __name__ == '__main__':
    bot.run(settings.TOKEN)
