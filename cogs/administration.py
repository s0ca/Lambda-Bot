import discord
from discord.ext import commands
from discord import app_commands
import os

class AdminCog(commands.GroupCog, name="admin"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    async def cog_check(self, interaction: discord.Interaction) -> bool:
        # Vérifie si l'utilisateur a le rôle spécifique pour utiliser les commandes de ce cog
        #BUGGED
        role_name = os.getenv("ADMIN_ROLE_NAME")
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        return role in interaction.user.roles

    @app_commands.command(name="plugins", description="Liste tous les plugins chargés et disponibles.")
    async def plugins(self, interaction: discord.Interaction):
        # Cogs actuellement chargés, retirant le préfixe 'cogs.'
        loaded_cogs = [cog.replace('cogs.', '') for cog in self.bot.extensions.keys()]
        loaded_formatted = "\n".join(loaded_cogs) if loaded_cogs else "Aucun plugin chargé."

        # Cogs disponibles dans le dossier 'cogs'
        cogs_dir = "cogs"
        available_cogs = [f[:-3] for f in os.listdir(cogs_dir) if f.endswith('.py') and not f.startswith('__')]
        # Filtrer les cogs déjà chargés
        available_cogs = [cog for cog in available_cogs if cog not in loaded_cogs]
        available_formatted = "\n".join(available_cogs) if available_cogs else "Aucun plugin disponible."

        # Créer et envoyer les embeds
        embed_loaded = discord.Embed(title="Plugins Chargés", description=loaded_formatted, color=discord.Color.green())
        embed_available = discord.Embed(title="Plugins Disponibles", description=available_formatted, color=discord.Color.orange())

        await interaction.response.send_message(embed=embed_loaded, ephemeral=True)
        await interaction.followup.send(embed=embed_available, ephemeral=True)


    @app_commands.command(name="load", description="Charge un plugin spécifié.")
    async def load(self, interaction: discord.Interaction, plugin: str):
        cog_path = f"cogs.{plugin}"
        try:
            await interaction.response.defer(ephemeral=True)
            await self.bot.load_extension(cog_path)
            await self.bot.tree.sync()
            await interaction.followup.send(f'Le cog {cog_path} a été chargé avec succès.', ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f'Erreur lors du chargement du cog {cog_path}: {e}', ephemeral=True)

    @app_commands.command(name="unload", description="Désactive un plugin spécifié.")
    async def unload(self, interaction: discord.Interaction, plugin: str):
        cog_path = f"cogs.{plugin}"
        try:
            await interaction.response.defer(ephemeral=True)
            await self.bot.unload_extension(cog_path)
            await self.bot.tree.sync()
            await interaction.followup.send(f'Le cog {cog_path} a été déchargé avec succès.')
        except Exception as e:
            await interaction.followup.send(f'Erreur lors du déchargement du cog {cog_path}: {e}')

    @app_commands.command(name="reload", description="Recharge un plugin spécifié.")
    async def reload(self, interaction: discord.Interaction, plugin: str):
        cog_path = f"cogs.{plugin}"
        try:
            await interaction.response.defer(ephemeral=True)
            await self.bot.reload_extension(cog_path)
            await self.bot.tree.sync()
            await interaction.followup.send(f'Le cog {cog_path} a été rechargé avec succès.')
        except Exception as e:
            await interaction.followup.send(f'Erreur lors du rechargement du cog {cog_path}: {e}')

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
