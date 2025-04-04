import discord
from discord.ext import commands
from discord import app_commands
import json
import sqlite3
import random
from pathlib import Path

QUIZ_DIR = Path("data/quizzes")
DB_PATH = Path("data/quiz_scores.db")


class QuizView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, question_data, correct_index, timeout=15):
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.question_data = question_data
        self.correct_index = correct_index
        self.result = None
        self.responded = False

        for i, choice in enumerate(question_data["choices"]):
            self.add_item(QuizButton(label=choice, index=i, parent=self))

    async def on_timeout(self):
        if not self.responded:
            await self.interaction.followup.send("⏰ Temps écoulé !", ephemeral=True)


class QuizButton(discord.ui.Button):
    def __init__(self, label, index, parent):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.index = index
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.parent.interaction.user:
            await interaction.response.send_message("Ce quiz ne t'est pas destiné !", ephemeral=True)
            return

        self.parent.responded = True
        if self.index == self.parent.correct_index:
            await interaction.response.send_message("✅ Bonne réponse !", ephemeral=True)
            self.parent.result = True
        else:
            correct = self.parent.question_data["choices"][self.parent.correct_index]
            await interaction.response.send_message(f"❌ Mauvaise réponse ! C'était : **{correct}**", ephemeral=True)
            self.parent.result = False
        self.stop()


class Quiz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect(DB_PATH)
        self.init_db()

    def init_db(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    user_id INTEGER,
                    username TEXT,
                    theme TEXT,
                    score INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, theme)
                )
            """)

    def add_point(self, user: discord.User, theme: str):
        with self.conn:
            self.conn.execute("""
                INSERT INTO scores (user_id, username, theme, score)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(user_id, theme) DO UPDATE SET score = score + 1, username = excluded.username
            """, (user.id, str(user), theme))

    def get_scores(self, theme: str, limit=10):
        cur = self.conn.cursor()
        cur.execute("SELECT username, score FROM scores WHERE theme = ? ORDER BY score DESC LIMIT ?", (theme, limit))
        return cur.fetchall()

    def get_available_quizzes(self):
        return [f.stem for f in QUIZ_DIR.glob("*.json")]

    def load_quiz(self, quiz_name: str):
        path = QUIZ_DIR / f"{quiz_name}.json"
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return None
        return None

    @app_commands.command(name="quiz", description="Lance un quiz sur un thème")
    @app_commands.describe(quiz="Nom du quiz à lancer")
    async def quiz(self, interaction: discord.Interaction, quiz: str):
        questions = self.load_quiz(quiz)
        if not questions:
            await interaction.response.send_message("❌ Quiz introuvable ou invalide.", ephemeral=True)
            return

        question = random.choice(questions)
        correct_index = question["answer_index"]

        view = QuizView(interaction, question, correct_index)
        embed = discord.Embed(title=f"🧠 Quiz : {quiz.capitalize()}", description=question["question"], color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await view.wait()

        if view.result:
            self.add_point(interaction.user, quiz)

    @quiz.autocomplete("quiz")
    async def quiz_autocomplete(self, interaction: discord.Interaction, current: str):
        quizzes = self.get_available_quizzes()
        return [
            app_commands.Choice(name=q.capitalize(), value=q)
            for q in quizzes if current.lower() in q.lower()
        ][:25]

    @app_commands.command(name="quiz_score", description="Classement du quiz par thème")
    @app_commands.describe(quiz="Thème du quiz")
    async def quiz_score(self, interaction: discord.Interaction, quiz: str):
        scores = self.get_scores(quiz)
        if not scores:
            await interaction.response.send_message("Aucun score enregistré pour ce thème.", ephemeral=True)
            return

        description = "\n".join([f"**{i+1}.** {name} — {score} pts" for i, (name, score) in enumerate(scores)])
        embed = discord.Embed(title=f"🏆 Classement : {quiz.capitalize()}", description=description, color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)

    @quiz_score.autocomplete("quiz")
    async def quiz_score_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self.quiz_autocomplete(interaction, current)

    @app_commands.command(name="quiz_reset", description="Réinitialise tous les scores (admin)")
    @app_commands.checks.has_permissions(administrator=True)
    async def quiz_reset(self, interaction: discord.Interaction):
        with self.conn:
            self.conn.execute("DELETE FROM scores")
        await interaction.response.send_message("🧹 Tous les scores ont été réinitialisés.", ephemeral=True)

    @quiz_reset.error
    async def quiz_reset_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("🚫 Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Quiz(bot))
