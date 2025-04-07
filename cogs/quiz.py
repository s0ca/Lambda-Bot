import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import asyncio
from pathlib import Path
from collections import defaultdict

QUIZ_DIR = Path("data/quiz")

class MultiQuizButton(discord.ui.Button):
    def __init__(self, label: str, index: int, session):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.index = index
        self.session = session

    async def callback(self, interaction: discord.Interaction):
        await self.session.register_answer(interaction, self.index)


class MultiQuizView(discord.ui.View):
    def __init__(self, session, question_data):
        super().__init__(timeout=None)
        self.session = session
        self.question_data = question_data

        for i, choice in enumerate(question_data["choices"]):
            self.add_item(MultiQuizButton(label=choice, index=i, session=session))

    def disable_all_items(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True


class QuizSession:
    def __init__(self, bot, interaction: discord.Interaction, questions: list, timer: int = 5):
        self.bot = bot
        self.interaction = interaction
        self.channel = interaction.channel
        self.questions = questions
        self.timer = timer
        self.scores = defaultdict(int)
        self.answers = {}  # user_id -> index
        self.current_question = 0
        self.message = None
        self.lock = asyncio.Lock()

    async def start(self):
        await self.interaction.response.send_message(f"🎮 Début du quiz multijoueur avec **{len(self.questions)} questions** (⏱️ {self.timer}s/question)", ephemeral=False)
        await asyncio.sleep(1)
        for i in range(len(self.questions)):
            self.current_question = i
            self.answers.clear()
            question_data = self.questions[i]

            view = MultiQuizView(self, question_data)
            embed = discord.Embed(
                title=f"Question {i+1}/{len(self.questions)}",
                description=question_data["question"],
                color=discord.Color.blurple()
            )
            self.message = await self.channel.send(embed=embed, view=view)

            await asyncio.sleep(self.timer)
            view.disable_all_items()
            await self.message.edit(view=view)
            await self.reveal_answer()
            await asyncio.sleep(2)

        await self.end_quiz()

    async def register_answer(self, interaction: discord.Interaction, answer_index: int):
        async with self.lock:
            if interaction.user.id in self.answers:
                await interaction.response.send_message("❌ Tu as déjà répondu à cette question.", ephemeral=True)
                return
            self.answers[interaction.user.id] = answer_index
            await interaction.response.send_message("✅ Réponse enregistrée !", ephemeral=True)

    async def reveal_answer(self):
        correct_index = self.questions[self.current_question]["answer_index"]
        winners = []
        for user_id, answer in self.answers.items():
            if answer == correct_index:
                self.scores[user_id] += 1
                winners.append(user_id)

        if not winners:
            await self.channel.send("❌ Personne n'a trouvé la bonne réponse.")
        else:
            mentions = [f"<@{uid}>" for uid in winners]
            await self.channel.send(f"✅ Bonne réponse pour : {', '.join(mentions)}")

    async def end_quiz(self):
        if not self.scores:
            await self.channel.send("🛑 Quiz terminé. Aucun participant n'a marqué de points.")
            return

        top_score = max(self.scores.values())
        winners = [uid for uid, score in self.scores.items() if score == top_score]
        mentions = [f"<@{uid}>" for uid in winners]

        await self.channel.send(f"🏁 Quiz terminé ! Gagnant{'s' if len(winners) > 1 else ''} : {', '.join(mentions)} avec {top_score} point(s) !")


class ConfirmDeleteView(discord.ui.View):
    def __init__(self, path: Path, quiz_name: str):
        super().__init__(timeout=15)
        self.path = path
        self.quiz_name = quiz_name
        self.confirmed = asyncio.Event()
        self.result = False

    @discord.ui.button(label="Confirmer la suppression", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            self.path.unlink()
            await interaction.response.edit_message(content=f"🗑️ Quiz **{self.quiz_name}** supprimé avec succès.", view=None)
            self.result = True
        except Exception as e:
            await interaction.response.edit_message(content=f"❌ Erreur lors de la suppression : {e}", view=None)
        self.confirmed.set()

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ Suppression annulée.", view=None)
        self.confirmed.set()


class Quiz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

    @app_commands.command(name="quiz", description="Lance un quiz multijoueur sur un thème")
    @app_commands.describe(
        quiz="Nom du quiz à lancer",
        nombre_questions="Nombre de questions (par défaut: 10)",
        timer_question="Durée en secondes par question (par défaut: 5)"
    )
    async def quiz(self, interaction: discord.Interaction, quiz: str, nombre_questions: int = 10, timer_question: int = 5):
        questions = self.load_quiz(quiz)
        if not questions:
            await interaction.response.send_message("❌ Quiz introuvable ou invalide.", ephemeral=True)
            return

        random.shuffle(questions)
        questions = questions[:nombre_questions]

        session = QuizSession(self.bot, interaction, questions, timer=timer_question)
        await session.start()

    @quiz.autocomplete("quiz")
    async def quiz_autocomplete(self, interaction: discord.Interaction, current: str):
        quizzes = self.get_available_quizzes()
        return [
            app_commands.Choice(name=q.capitalize(), value=q)
            for q in quizzes if current.lower() in q.lower()
        ][:25]

    @app_commands.command(name="quiz_delete", description="Supprime un quiz (admin uniquement)")
    @app_commands.describe(quiz="Nom du quiz à supprimer")
    @app_commands.checks.has_permissions(administrator=True)
    async def quiz_delete(self, interaction: discord.Interaction, quiz: str):
        quizzes = self.get_available_quizzes()
        if quiz not in quizzes:
            await interaction.response.send_message("❌ Quiz introuvable.", ephemeral=True)
            return

        path = QUIZ_DIR / f"{quiz}.json"
        view = ConfirmDeleteView(path, quiz)
        await interaction.response.send_message(f"⚠️ Confirmez-vous la suppression du quiz **{quiz}** ?", view=view, ephemeral=True)
        await view.confirmed.wait()

    @quiz_delete.autocomplete("quiz")
    async def quiz_delete_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=q.capitalize(), value=q)
            for q in self.get_available_quizzes() if current.lower() in q.lower()
        ][:25]


async def setup(bot):
    await bot.add_cog(Quiz(bot))
