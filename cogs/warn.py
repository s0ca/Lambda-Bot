import discord
from discord.ext import commands
from datetime import datetime, timedelta

class WarnManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}  # Stockage des warns par utilisateur (id)
        self.warn_expiry = 24  # Durée d'expiration des warns (en heures)

    def is_authorized():
        async def predicate(interaction: discord.Interaction):
            # Récupérer le rôle par son ID
            authorized_role = discord.utils.get(interaction.guild.roles, id=123456) #Mettre l'id du role autorisé à utiliser cette commande
            # Vérifier si l'utilisateur a le rôle
            if authorized_role not in interaction.user.roles:
                raise commands.CheckFailure("unauthorized")  # Déclenche une exception si non autorisé
            return True
        return commands.check(predicate)

    @discord.app_commands.command(name="warn", description="Avertir un utilisateur avec une sanction")
    @is_authorized()  # Appliquer le check pour limiter l'accès à certains rôles
    async def warn(self, interaction: discord.Interaction, member: discord.Member, custom_duration: str = None, reason: str = "Pas de raison fournie"):
        """Warn un membre et applique des sanctions progressives avec une raison"""
        now = datetime.utcnow()

        if member.id not in self.warnings:
            self.warnings[member.id] = []
        
        # Nettoyage des warns expirés de plus de 24 heures
        self.warnings[member.id] = [warn for warn in self.warnings[member.id] if now - warn < timedelta(hours=self.warn_expiry)]

        # Ajouter un nouveau warn avec un timestamp actuel
        self.warnings[member.id].append(now)
        warn_count = len(self.warnings[member.id])

        # Sanctions basées sur le nombre de warns dans la fenêtre de 24 heures
        if warn_count == 1:
            duration = custom_duration if custom_duration else "10m"
            await self.apply_punishment(interaction, member, duration)
            await self.send_warn_embed(interaction, member, interaction.user, duration, reason)
        elif warn_count == 2:
            duration = custom_duration if custom_duration else "1h"
            await self.apply_punishment(interaction, member, duration)
            await self.send_warn_embed(interaction, member, interaction.user, duration, reason)
        elif warn_count == 3:
            duration = custom_duration if custom_duration else "12h"
            await self.apply_punishment(interaction, member, duration)
            await self.send_warn_embed(interaction, member, interaction.user, duration, reason)
        else:
            await interaction.response.send_message(f"{member.mention} a déjà {warn_count} warns dans les dernières 24 heures.")

    async def apply_punishment(self, interaction: discord.Interaction, member: discord.Member, duration: str):
        """Appliquer la sanction en retirant le rôle pour une durée donnée"""
        role = discord.utils.get(interaction.guild.roles, id=321654) # Definir l'id du role a supprimer provisoirement
        await member.remove_roles(role)
        
        # Convertir la durée en timedelta
        punishment_duration = self.parse_duration(duration)

        # Tâche pour réattribuer le rôle après la période définie
        await discord.utils.sleep_until(datetime.utcnow() + punishment_duration)
        await member.add_roles(role)

    async def send_warn_embed(self, interaction: discord.Interaction, warned_member: discord.Member, warner: discord.User, duration: str, reason: str):
        """Créer et envoyer un embed pour annoncer le warn"""
        embed = discord.Embed(title="⚠️ Avertissement ⚠️", color=discord.Color.orange())
        embed.add_field(name="Utilisateur averti", value=warned_member.mention, inline=False)
        embed.add_field(name="Émis par", value=warner.mention, inline=False)
        embed.add_field(name="Durée de la sanction", value=duration, inline=False)
        embed.add_field(name="Raison", value=reason, inline=False)
        embed.timestamp = datetime.utcnow()

        await interaction.response.send_message(embed=embed)

    def parse_duration(self, duration: str) -> timedelta:
        """Convertir une durée en string (e.g. '10m', '1h') en timedelta"""
        amount = int(duration[:-1])
        unit = duration[-1]
        if unit == "m":
            return timedelta(minutes=amount)
        elif unit == "h":
            return timedelta(hours=amount)
        elif unit == "d":
            return timedelta(days=amount)
        return timedelta()  # Valeur par défaut en cas d'erreur

# Ajoute le cog au bot
async def setup(bot):
    await bot.add_cog(WarnManager(bot))

# Gérer les erreurs globalement
@commands.Cog.listener()
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, commands.CheckFailure) and str(error) == "unauthorized":
        # Message personnalisé affiché publiquement dans le canal où la commande a été invoquée
        await interaction.response.send_message("T'as cru avoir suffisamment d'importance pour avoir le droit d'utiliser cette commande?", ephemeral=False)
    else:
        # Gérer les autres erreurs
        await interaction.response.send_message("Une erreur est survenue lors de l'exécution de la commande.")
