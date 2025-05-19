import random
import discord
import json
from discord import app_commands
from discord.ext import commands
from pathlib import Path

SCORES_PATH = Path("rpsls_scores.json")

class RPSLS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.choices = ["pierre", "papier", "ciseaux", "lezard", "spock"]

        self.win_map = {
            "pierre": ["ciseaux", "lezard"],
            "papier": ["pierre", "spock"],
            "ciseaux": ["papier", "lezard"],
            "lezard": ["spock", "papier"],
            "spock": ["ciseaux", "pierre"]
        }

        self.scores = self.load_scores()
        self.active_duels = {}  # (challenger_id, opponent_id) -> DuelSession
        self.loss_streaks = {}

    def load_scores(self):
        if SCORES_PATH.exists():
            with open(SCORES_PATH, 'r') as f:
                return json.load(f)
        return {}

    def save_scores(self):
        with open(SCORES_PATH, 'w') as f:
            json.dump(self.scores, f)

    def get_result(self, p1, p2):
        if p1 == p2:
            return 0
        elif p2 in self.win_map[p1]:
            return 1
        else:
            return -1

    async def update_score(self, user_id, win):
        self.scores[str(user_id)] = self.scores.get(str(user_id), 0) + (1 if win else 0)
        self.save_scores()

        # Déclenche une réinitialisation si un joueur atteint 10 victoires
        if self.scores[str(user_id)] >= 10:
            sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
            winners = []
            for i, (uid, score) in enumerate(sorted_scores[:3]):
                user = self.bot.get_user(int(uid)) or await self.bot.fetch_user(int(uid))
                winners.append(f"**{i+1}.** {user.name} - {score} pts")

            self.scores.clear()
            self.save_scores()

            channel = discord.utils.get(self.bot.get_all_channels(), name="general") or list(self.bot.get_all_channels())[0]
            await channel.send(
            "🎉 **Partie terminée !** Le score a été réinitialisé.\n\n" +
            "🏆 **Top 3 final :**\n" +
            "\n".join(winners) +
            "\n\n🔥 Un nouveau tournoi peut commencer !"
        )
    @app_commands.command(name="rpsls", description="Pierre / Papier / Ciseaux / Lézard / Spock contre un autre joueur ou le bot")
    @app_commands.describe(adversaire="L'utilisateur que tu veux défier (facultatif)")
    async def rpsls(self, interaction: discord.Interaction, adversaire: discord.Member = None):
        if adversaire is None:
            view = RPSLSSoloView(self)
            await interaction.response.send_message("Choisis ton arme contre le bot :", view=view, ephemeral=True)
            return

        if adversaire.bot:
            await interaction.response.send_message("Tu ne peux pas défier un bot !", ephemeral=True)
            return

        if adversaire.id == interaction.user.id:
            await interaction.response.send_message("Tu ne peux pas te défier toi-même !", ephemeral=True)
            return

        key = (interaction.user.id, adversaire.id)
        if key in self.active_duels:
            await interaction.response.send_message("Un duel est déjà en cours entre vous deux !", ephemeral=True)
            return

        self.active_duels[key] = {"challenger": interaction.user, "opponent": adversaire}
        view = RPSLSChallengeView(self, interaction.user, adversaire)
        await interaction.response.send_message(f"{adversaire.mention}, {interaction.user.mention} te défie à un Pierre/Papier/Ciseaux/Lézard/Spock ! Acceptes-tu ?", view=view, ephemeral=False)
        view.message = await interaction.original_response()

class RPSLSSoloView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=30)
        self.cog = cog
        for c in cog.choices:
            self.add_item(RPSLSSoloButton(cog, c))

class RPSLSSoloButton(discord.ui.Button):
    def __init__(self, cog, value):
        super().__init__(label=value.capitalize(), style=discord.ButtonStyle.primary)
        self.cog = cog
        self.value = value

    async def callback(self, interaction: discord.Interaction):
        bot_choice = random.choice(self.cog.choices)
        result = self.cog.get_result(self.value, bot_choice)
        msg = f"Tu as choisi **{self.value}**, le bot a choisi **{bot_choice}**.\n"
        if result == 0:
            msg += "Égalité ! Relance automatique du duel contre le bot...\n"
            await interaction.response.edit_message(content=msg, view=None)
            # relancer immédiatement un autre bouton
            view = RPSLSSoloView(self.cog)
            await interaction.followup.send("Choisis à nouveau ton arme :", view=view, ephemeral=True)
            return
        elif result == 1:
            msg += "Tu as gagné !"
            await self.cog.update_score(interaction.user.id, True)
        else:
            msg += "Tu as perdu..."
        await interaction.response.edit_message(content=msg, view=None)

class RPSLSChallengeView(discord.ui.View):
    def __init__(self, cog: RPSLS, challenger: discord.User, opponent: discord.User):
        super().__init__(timeout=86400)
        self.cog = cog
        self.challenger = challenger
        self.opponent = opponent
        self.message = None
        self.add_item(RPSLSAcceptButton(cog, challenger, opponent))
        self.add_item(RPSLSDeclineButton(cog, challenger, opponent))

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except discord.NotFound:
                pass

class RPSLSAcceptButton(discord.ui.Button):
    def __init__(self, cog: RPSLS, challenger: discord.User, opponent: discord.User):
        super().__init__(label="Accepter", style=discord.ButtonStyle.success)
        self.cog = cog
        self.challenger = challenger
        self.opponent = opponent

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.opponent:
            await interaction.response.send_message("Tu n'es pas concerné par ce duel.", ephemeral=True)
            return

        await interaction.response.send_message("Défi accepté !", ephemeral=True)
        if self.cog.active_duels.get((self.challenger.id, self.opponent.id)):
            for view in interaction.client.persistent_views:
                if isinstance(view, RPSLSChallengeView) and view.message:
                    try:
                        await view.message.delete()
                    except discord.NotFound:
                        pass
        await interaction.channel.send(f"{interaction.user.mention}, choisis ton arme :", view=RPSLSChoiceView(self.cog, self.opponent, self.challenger))
        await interaction.channel.send(f"{self.challenger.mention}, choisis ton arme :", view=RPSLSChoiceView(self.cog, self.challenger, self.opponent))

class RPSLSDeclineButton(discord.ui.Button):
    def __init__(self, cog: RPSLS, challenger: discord.User, opponent: discord.User):
        super().__init__(label="Refuser", style=discord.ButtonStyle.danger)
        self.cog = cog
        self.challenger = challenger
        self.opponent = opponent

    async def callback(self, interaction: discord.Interaction):
        if self.cog.active_duels.get((self.challenger.id, self.opponent.id)):
            for view in interaction.client.persistent_views:
                if isinstance(view, RPSLSChallengeView) and view.message:
                    try:
                        await view.message.delete()
                    except discord.NotFound:
                        pass
        await interaction.response.edit_message(content="Défi refusé.", view=None)
        self.cog.active_duels.pop((self.challenger.id, self.opponent.id), None)

class RPSLSChoiceView(discord.ui.View):
    def __init__(self, cog, user, opponent):
        super().__init__()
        self.cog = cog
        self.user = user
        self.opponent = opponent
        for c in cog.choices:
            self.add_item(RPSLSChoiceButton(cog, c, user, opponent))

class RPSLSChoiceButton(discord.ui.Button):
    def __init__(self, cog, value, user, opponent):
        super().__init__(label=value.capitalize(), style=discord.ButtonStyle.primary)
        self.cog = cog
        self.value = value
        self.user = user
        self.opponent = opponent

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("Ce bouton n'est pas pour toi.", ephemeral=True)
            return

        duel_key = (self.opponent.id, self.user.id) if (self.opponent.id, self.user.id) in self.cog.active_duels else (self.user.id, self.opponent.id)
        duel = self.cog.active_duels.get(duel_key)

        if duel is None:
            await interaction.response.send_message("Ce duel n'existe plus.", ephemeral=True)
            return

        duel[str(self.user.id)] = self.value

        if str(self.opponent.id) in duel and str(self.user.id) in duel:
            c1 = duel[str(self.user.id)]
            c2 = duel[str(self.opponent.id)]
            res = self.cog.get_result(c1, c2)
            msg = f"**{self.user.display_name}** a choisi **{c1}**, **{self.opponent.display_name}** a choisi **{c2}**.\n"
            if res == 0:
                msg += "Égalité !"
                if c1 == "lezard" and c2 == "lezard":
                    msg += "\n🦎 Deux lézards se sont neutralisés en dansant... tragique."
                await interaction.channel.send(msg)
                await interaction.channel.send("Nouvelle égalité ! Rejouez immédiatement :")
                await interaction.channel.send(f"{self.user.mention}, choisis ton arme :", view=RPSLSChoiceView(self.cog, self.user, self.opponent), ephemeral=True)
                await interaction.channel.send(f"{self.opponent.mention}, choisis ton arme :", view=RPSLSChoiceView(self.cog, self.opponent, self.user), ephemeral=True)
                return
            elif res == 1:
                msg += f"{self.user.mention} gagne !"
                await self.cog.update_score(self.user.id, True)
            else:
                msg += f"{self.opponent.mention} gagne !"
                await self.cog.update_score(self.opponent.id, True)
            if res != 0:
                loser_id = self.opponent.id if res == 1 else self.user.id
                self.cog.loss_streaks[loser_id] = self.cog.loss_streaks.get(loser_id, 0) + 1
                winner_id = self.user.id if res == 1 else self.opponent.id
                self.cog.loss_streaks[winner_id] = 0  # reset winner streak

                if self.cog.loss_streaks[loser_id] >= 3:
                    msg += f"\n🤡 {interaction.client.get_user(loser_id).display_name}, ça commence à faire beaucoup de défaites non ?"
                if "spock" in [c1, c2] and random.random() < 0.1:
                    msg += "\n🧠 \"Spock wins. As always.\" – Sheldon Cooper"

            await interaction.channel.send(msg)
            async for m in interaction.channel.history(limit=20):
                if m.author == interaction.client.user and m.components:
                    try:
                        await m.delete()
                    except discord.HTTPException:
                        pass
            self.cog.active_duels.pop(duel_key, None)
        else:
            await interaction.response.send_message("Choix enregistré. En attente de ton adversaire...", ephemeral=True)

@app_commands.command(name="rpsls_scoreboard", description="Affiche le classement des meilleurs joueurs RPSLS")
async def rpsls_scoreboard(interaction: discord.Interaction):
    cog = interaction.client.get_cog("RPSLS")
    if not cog:
        await interaction.response.send_message("Erreur : cog non chargé.", ephemeral=True)
        return

    sorted_scores = sorted(cog.scores.items(), key=lambda x: x[1], reverse=True)[:10]
    if not sorted_scores:
        await interaction.response.send_message("Aucun score enregistré pour le moment.")
    else:
        lines = []
        for i, (user_id, score) in enumerate(sorted_scores, start=1):
            user = await interaction.client.fetch_user(int(user_id))
            lines.append(f"**{i}.** {user.name} - {score} point(s)")

        await interaction.response.send_message("🏆 **Classement RPSLS** :\n" + "\n".join(lines))


async def setup(bot: commands.Bot):
    await bot.add_cog(RPSLS(bot))
    bot.tree.add_command(rpsls_scoreboard)
