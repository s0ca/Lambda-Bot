import discord
import asyncio
import json
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import random
import os

WARN_FILE = "warn_data.json"
LOG_CHANNEL_ID = 12345678987654321012  # Remplace par l'ID de ton canal de logs

class WarnManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}  # {user_id: [{"timestamp": str, "duration": str}]}
        self.active_tasks = {}  # {user_id: asyncio.Task}
        self.warn_expiry = 24  # Heures pour purge

    async def load_warns(self):
        if os.path.exists(WARN_FILE):
            with open(WARN_FILE, "r") as f:
                self.warnings = json.load(f)
                await self.restore_tasks()

    async def save_warns(self):
        with open(WARN_FILE, "w") as f:
            json.dump(self.warnings, f, indent=4)

    async def restore_tasks(self):
        now = datetime.utcnow()
        for user_id, warn_list in self.warnings.items():
            if not warn_list:
                continue
            last_warn = warn_list[-1]
            start = datetime.fromisoformat(last_warn["timestamp"])
            duration = self.parse_duration(last_warn["duration"])
            end = start + duration
            if end > now:
                remaining = (end - now).total_seconds()
                member = self.bot.get_user(int(user_id))
                if member:
                    self.active_tasks[user_id] = asyncio.create_task(self.schedule_unwarn(member, last_warn["duration"], start))

    async def log_action(self, guild: discord.Guild, message: str):
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(message)
        else:
            print(f"[WARN LOG] Channel introuvable pour LOG_CHANNEL_ID={LOG_CHANNEL_ID}")
            print(f"[LOG] {message}")

    def is_authorized():
        async def predicate(interaction: discord.Interaction):
            print("Vérification des permissions (slash commands)...")
            authorized_role = discord.utils.get(interaction.guild.roles, id=123456)
            override_user_id = 123456 

            if interaction.user.id == override_user_id:
                print(f"Accès autorisé via ID explicite : {interaction.user}")
                return True

            if not authorized_role:
                print("Erreur : rôle non trouvé. Vérifie l'ID du rôle.")
                raise app_commands.CheckFailure("unauthorized")

            if authorized_role not in interaction.user.roles:
                print(f"L'utilisateur {interaction.user} n'a pas le rôle requis.")
                error_responses = [
                    "T'as cru avoir suffisamment d'importance pour avoir le droit d'utiliser cette commande?",
                    "Essaye encore, mais avec un peu plus d'autorité peut-être.",
                    "Tu penses vraiment pouvoir utiliser cette commande? Pas aujourd'hui.",
                    "Les recrutements sont clos pour ce job. Désolé.",
                    "Voir avec Soupole."
                ]
                random_response = random.choice(error_responses)

                try:
                    await interaction.response.send_message(random_response, ephemeral=True)
                except discord.errors.InteractionResponded:
                    await interaction.followup.send(random_response, ephemeral=True)

                raise app_commands.CheckFailure("unauthorized")
            return True

        return app_commands.check(predicate)

    def parse_duration(self, duration: str) -> timedelta:
        try:
            duration = duration.strip().lower()
            amount = int(duration[:-1])
            unit = duration[-1]
            if unit == "s":
                return timedelta(seconds=amount)
            elif unit == "m":
                return timedelta(minutes=amount)
            elif unit == "h":
                return timedelta(hours=amount)
            elif unit == "d":
                return timedelta(days=amount)
        except:
            pass
        return timedelta(minutes=10)

    async def send_warn_embed(self, interaction, member, warner, duration, reason):
        warn_count = len(self.warnings.get(str(member.id), []))
        embed = discord.Embed(title="\u26a0\ufe0f Avertissement \u26a0\ufe0f", color=discord.Color.orange())
        embed.add_field(name="Utilisateur averti", value=member.mention, inline=False)
        embed.add_field(name="\u00c9mis par", value=warner.mention, inline=False)
        embed.add_field(name="Nombre de warns", value=f"{warn_count}", inline=False)
        embed.add_field(name="Dur\u00e9e de la sanction", value=duration, inline=False)
        embed.add_field(name="Raison", value=reason, inline=False)
        embed.timestamp = datetime.utcnow()
        await interaction.followup.send(embed=embed)

    @discord.app_commands.command(name="warn", description="Avertir un utilisateur avec une sanction.")
    @is_authorized()
    async def warn(self, interaction, member: discord.Member, custom_duration: str = None, reason: str = "Pas de raison fournie"):
        await interaction.response.defer()
        now = datetime.utcnow()
        user_id = str(member.id)

        if user_id not in self.warnings:
            self.warnings[user_id] = []

        self.warnings[user_id] = [warn for warn in self.warnings[user_id] if now - datetime.fromisoformat(warn["timestamp"]) < timedelta(hours=self.warn_expiry)]

        duration = custom_duration or ["10m", "30m", "1h", "12h"][min(len(self.warnings[user_id]), 3)]
        self.warnings[user_id].append({"timestamp": now.isoformat(), "duration": duration})
        await self.save_warns()

        role = discord.utils.get(member.guild.roles, id=123456)
        await member.remove_roles(role)
        await self.send_warn_embed(interaction, member, interaction.user, duration, reason)
        await self.log_action(interaction.guild, f"{member} warned by {interaction.user} for {duration} — {reason}")

        self.active_tasks[user_id] = asyncio.create_task(self.schedule_unwarn(member, duration, now))

    async def schedule_unwarn(self, member: discord.Member, duration: str, start_time: datetime):
        delta = self.parse_duration(duration)
        await asyncio.sleep((start_time + delta - datetime.utcnow()).total_seconds())
        role = discord.utils.get(member.guild.roles, id=123456)
        await member.add_roles(role)
        await self.log_action(member.guild, f"{member} warn finished after {duration}")

    @discord.app_commands.command(name="unwarn", description="Annuler un avertissement actif pour un utilisateur.")
    @is_authorized()
    async def unwarn(self, interaction, member: discord.Member, reason: str = "Pas de raison fournie"):
        user_id = str(member.id)
        role = discord.utils.get(member.guild.roles, id=123456)
        if user_id in self.warnings and self.warnings[user_id]:
            self.warnings[user_id].pop()
            await self.save_warns()

            if role and role not in member.roles:
                await member.add_roles(role)

            if user_id in self.active_tasks:
                self.active_tasks[user_id].cancel()

            embed = discord.Embed(title="\u2705 Warn annul\u00e9 \u2705", color=discord.Color.green())
            embed.add_field(name="Utilisateur", value=member.mention, inline=False)
            embed.add_field(name="\u00c9mis par", value=interaction.user.mention, inline=False)
            embed.add_field(name="Raison", value=reason, inline=False)
            embed.timestamp = datetime.utcnow()
            await interaction.response.send_message(embed=embed)
            await self.log_action(interaction.guild, f"{member} unwarned by {interaction.user} — {reason}")
            return

        await interaction.response.send_message(f"{member.mention} n'a aucun warn actif à annuler.", ephemeral=True)

    @discord.app_commands.command(name="warnlist", description="Afficher la liste des warns actifs et leur temps restant.")
    @is_authorized()
    async def warnlist(self, interaction: discord.Interaction):
        now = datetime.utcnow()
        embed = discord.Embed(title="\ud83d\udccb Liste des warns en cours", color=discord.Color.blue())

        for user_id, warns in self.warnings.items():
            if not warns:
                continue
            last_warn = warns[-1]
            start = datetime.fromisoformat(last_warn["timestamp"])
            duration = self.parse_duration(last_warn["duration"])
            end = start + duration
            if end < now:
                continue

            remaining = end - now
            member = interaction.guild.get_member(int(user_id))
            if not member:
                try:
                    member = await interaction.guild.fetch_member(int(user_id))
                except:
                    continue

            count_24h = sum(1 for w in warns if now - datetime.fromisoformat(w["timestamp"]) < timedelta(hours=24))
            embed.add_field(
                name=f"{member.display_name}",
                value=f"{last_warn['duration']} (reste {str(remaining).split('.')[0]}) ({count_24h} warns dernières 24h)",
                inline=False
            )

        if not embed.fields:
            embed.description = "Aucun warn actif."

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    cog = WarnManager(bot)
    await cog.load_warns()
    await bot.add_cog(cog)
    await bot.tree.sync()
