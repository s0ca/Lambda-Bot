import discord
import asyncio
from discord.ext import commands
from datetime import datetime, timedelta
import random

class WarnManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}  # Stockage des warns par utilisateur (id)
        self.warn_expiry = 24  # Durée d'expiration des warns (en heures)

    def is_authorized():
        async def predicate(interaction: discord.Interaction):
            authorized_role = discord.utils.get(interaction.guild.roles, id=XXXX)  # ID du rôle autorisé
            if authorized_role not in interaction.user.roles:
                raise commands.CheckFailure("unauthorized")  # Déclenche une exception si non autorisé
            return True
        return commands.check(predicate)

    @discord.app_commands.command(name="warn", description="Avertir un utilisateur avec une sanction")
    @is_authorized()  # Appliquer le check pour limiter l'accès à certains rôles
    async def warn(self, interaction: discord.Interaction, member: discord.Member, custom_duration: str = None, reason: str = "Pas de raison fournie"):
        """Warn un membre et applique des sanctions progressives avec une raison"""

        await interaction.response.defer()
        print("Réponse déférée...")

        now = datetime.utcnow()

        if member.id not in self.warnings:
            self.warnings[member.id] = []

        # Nettoyage des warns expirés de plus de 24 heures
        self.warnings[member.id] = [warn for warn in self.warnings[member.id] if now - warn < timedelta(hours=self.warn_expiry)]

        # Ajouter un nouveau warn avec un timestamp actuel
        self.warnings[member.id].append(now)
        warn_count = len(self.warnings[member.id])

        await interaction.followup.send(f"{member.mention} a été warn. Application de la sanction...")

        # Sanctions basées sur le nombre de warns dans la fenêtre de 24 heures
        if warn_count == 1:
            duration = custom_duration if custom_duration else "10m"
            await self.apply_punishment_async(member, duration)
            await self.send_warn_embed(interaction, member, interaction.user, duration, reason)
        elif warn_count == 2:
            duration = custom_duration if custom_duration else "1h"
            await self.apply_punishment_async(member, duration)
            await self.send_warn_embed(interaction, member, interaction.user, duration, reason)
        elif warn_count == 3:
            duration = custom_duration if custom_duration else "12h"
            await self.apply_punishment_async(member, duration)
            await self.send_warn_embed(interaction, member, interaction.user, duration, reason)
        else:
            duration = custom_duration if custom_duration else "12h"
            await self.apply_punishment_async(member, duration)
            await interaction.followup.send(f"{member.mention} a déjà {warn_count} warns dans les dernières 24 heures. Sanction réappliquée pour {duration}.")

    async def apply_punishment_async(self, member: discord.Member, duration: str):
        """Lancer la punition asynchrone sans bloquer l'exécution"""
        asyncio.create_task(self.apply_punishment(member, duration))

    async def apply_punishment(self, member: discord.Member, duration: str):
        """Appliquer la sanction en retirant le rôle pour une durée donnée"""
        role = discord.utils.get(member.guild.roles, id=XXXX)  # ID du rôle à supprimer provisoirement
        bot_member = member.guild.me

        if role >= bot_member.top_role:
            print("Je ne peux pas retirer ce rôle car il est supérieur ou égal à mon rôle dans la hiérarchie.")
            return

        if not bot_member.guild_permissions.manage_roles:
            print("Je n'ai pas la permission de gérer les rôles.")
            return

        await member.remove_roles(role)
        print(f"Le rôle {role.name} a été retiré à {member.name} pour {duration}.")

        punishment_duration = self.parse_duration(duration)
        await asyncio.sleep(punishment_duration.total_seconds())

        await member.add_roles(role)
        print(f"Le rôle {role.name} a été réattribué à {member.name} après {duration}.")

    async def send_warn_embed(self, interaction: discord.Interaction, warned_member: discord.Member, warner: discord.User, duration: str, reason: str):
        # Calcul du nombre de warns de l'utilisateur
        warn_count = len(self.warnings[warned_member.id])
        """Créer et envoyer un embed pour annoncer le warn"""
        embed = discord.Embed(title="⚠️ Avertissement ⚠️", color=discord.Color.orange())
        embed.add_field(name="Utilisateur averti", value=warned_member.mention, inline=False)
        embed.add_field(name="Émis par", value=warner.mention, inline=False)
        embed.add_field(name="Nombre de warns", value=f"{warn_count}", inline=False)
        embed.add_field(name="Durée de la sanction", value=duration, inline=False)
        embed.add_field(name="Raison", value=reason, inline=False)
        embed.timestamp = datetime.utcnow()

        await interaction.followup.send(embed=embed)

    def parse_duration(self, duration: str) -> timedelta:
        """Convertir une durée en string (e.g. '10m', '1h') en timedelta"""
        try:
            amount = int(duration[:-1])
            unit = duration[-1]
            if unit == "m":
                return timedelta(minutes=amount)
            elif unit == "h":
                return timedelta(hours=amount)
            elif unit == "d":
                return timedelta(days=amount)
            else:
                raise ValueError("Unité de durée non supportée. Utilisez 'm' pour minutes, 'h' pour heures ou 'd' pour jours.")
        except (ValueError, IndexError):
            print(f"Erreur de conversion de la durée : {duration}. Utilisation de la durée par défaut (10 minutes).")
            return timedelta(minutes=10)

    # Gérer les erreurs globalement avec des réponses aléatoires
    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error):
        if isinstance(error, commands.CheckFailure) and str(error) == "unauthorized":
            # Liste des réponses possibles
            error_responses = [
                "T'as cru avoir suffisamment d'importance pour avoir le droit d'utiliser cette commande?",
                "Essaye encore, mais avec un peu plus d'autorité peut-être.",
                "Non, tu n'as pas les droits pour faire ça, désolé.",
                "Tu penses vraiment pouvoir utiliser cette commande? Pas aujourd'hui.",
                "Accès refusé. Peut-être un jour, mais pas maintenant."
            ]

            # Choisir une réponse au hasard
            random_response = random.choice(error_responses)

            # Envoyer la réponse choisie
            try:
                await interaction.followup.send(random_response, ephemeral=False)
            except discord.errors.InteractionResponded:
                await interaction.followup.send(random_response, ephemeral=False)

        else:
            # Gérer les autres erreurs
            try:
                await interaction.followup.send("Une erreur est survenue lors de l'exécution de la commande.")
            except discord.errors.InteractionResponded:
                await interaction.followup.send("Une erreur est survenue lors de l'exécution de la commande.")

# Ajoute le cog au bot et synchronise les commandes
async def setup(bot: commands.Bot):
    await bot.add_cog(WarnManager(bot))
    await bot.tree.sync()
