import discord
import asyncio
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import random

class WarnManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}  # Stockage des warns par utilisateur (id)
        self.warn_expiry = 24  # Durée d'expiration des warns (en heures)
    
    def is_authorized():
        async def predicate(interaction: discord.Interaction):
            print("Vérification des permissions (slash commands)...")  # Log pour savoir si la fonction est appelée

            # Récupérer le rôle par son ID
            authorized_role = discord.utils.get(interaction.guild.roles, id=xxxx)  # Mettre ici l'ID du rôle autorisé

            # Vérifier si le rôle a été trouvé dans le serveur
            if not authorized_role:
                print("Erreur : rôle non trouvé. Vérifie l'ID du rôle.")
                raise app_commands.CheckFailure("unauthorized")

            # Vérifier si l'utilisateur a le rôle
            if authorized_role not in interaction.user.roles:
                print(f"L'utilisateur {interaction.user} n'a pas le rôle requis.")

                # Choisir une réponse aléatoire parmi les phrases personnalisées
                error_responses = [
                    "T'as cru avoir suffisamment d'importance pour avoir le droit d'utiliser cette commande?",
                    "Essaye encore, mais avec un peu plus d'autorité peut-être.",
                    "Tu penses vraiment pouvoir utiliser cette commande? Pas aujourd'hui.",
                    "Les recrutements sont clos pour ce job. Désolé",
                    "Voir avec Soupole"
                ]

                random_response = random.choice(error_responses)

                # Envoyer le message personnalisé à l'utilisateur
                try:
                    await interaction.response.send_message(random_response, ephemeral=False)
                except discord.errors.InteractionResponded:
                    await interaction.followup.send(random_response, ephemeral=False)

                raise app_commands.CheckFailure("unauthorized")  # Déclenche une exception si non autorisé
            else:
                print(f"L'utilisateur {interaction.user} a bien le rôle requis.")

            return True

        return app_commands.check(predicate)

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
        role = discord.utils.get(member.guild.roles, id=xxxx)  # ID du rôle à supprimer provisoirement
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

    @discord.app_commands.command(name="reset_warn", description="Réinitialiser les warnings d'un utilisateur.")
    @is_authorized()  # Vérification que l'utilisateur qui exécute la commande est autorisé
    async def reset_warn(self, interaction: discord.Interaction, member: discord.Member):
        """Réinitialiser les warnings d'un utilisateur"""

        # Vérifier si l'utilisateur a des warnings
        if member.id in self.warnings and self.warnings[member.id]:
            # Réinitialiser les warnings de l'utilisateur
            self.warnings[member.id] = []
            await interaction.response.send_message(f"Les warnings de {member.mention} ont été réinitialisés.", ephemeral=True)
            print(f"Warnings réinitialisés pour {member.name}")
        else:
            # Si l'utilisateur n'a pas de warnings
            await interaction.response.send_message(f"{member.mention} n'a pas de warnings à réinitialiser.", ephemeral=True)
            print(f"Aucun warning à réinitialiser pour {member.name}")
   
    @discord.app_commands.command(name="list_warns", description="Afficher tous les utilisateurs avec des warnings en cours.")
    @is_authorized()  # Vérification que l'utilisateur qui exécute la commande est autorisé
    async def list_warns(self, interaction: discord.Interaction):
        """Lister tous les utilisateurs avec des warnings en cours"""

        # Créer un embed pour afficher la liste des utilisateurs avec warnings
        embed = discord.Embed(title="📋 Liste des utilisateurs avec warnings", color=discord.Color.blue())

        # Vérifier s'il y a des utilisateurs avec des warnings
        if self.warnings:
            has_warns = False  # Un flag pour vérifier si au moins un utilisateur a des warns
            for user_id, warns in self.warnings.items():
                if warns:  # Si l'utilisateur a au moins un warning en cours
                    user = await interaction.guild.fetch_member(user_id)
                    embed.add_field(name=user.display_name, value=f"{len(warns)} warnings en cours", inline=False)
                    has_warns = True
        
            if not has_warns:
                embed.description = "Aucun utilisateur n'a de warnings en cours."
        else:
            embed.description = "Aucun utilisateur n'a de warnings en cours."

        # Envoyer l'embed
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Ajoute le cog au bot et synchronise les commandes
async def setup(bot: commands.Bot):
    await bot.add_cog(WarnManager(bot))
    await bot.tree.sync()
