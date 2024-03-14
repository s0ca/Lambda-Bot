from discord.ext import commands
from discord import app_commands
import discord
import sqlite3

class NoteTaking(commands.GroupCog, name="notes"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_path = 'notes.db'  # Chemin vers votre fichier de base de données SQLite

    def add_note_to_db(self, user_id: str, note: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notes (user_id, note) VALUES (?, ?)", (user_id, note))
        conn.commit()
        conn.close()

    def get_notes_from_db(self, user_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, note FROM notes WHERE user_id=?", (user_id,))
        notes = cursor.fetchall()  # Récupère toutes les notes correspondantes
        conn.close()
        return notes
    
    def delete_note_from_db(self, note_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id=?", (note_id,))
        conn.commit()
        conn.close()


    @app_commands.command(name="create_note", description="Crée une nouvelle note.")
    @app_commands.describe(note="Le contenu de la note à ajouter.")
    async def create_note(self, interaction: discord.Interaction, note: str):
        user_id = str(interaction.user.id)
        self.add_note_to_db(user_id, note)
        await interaction.response.send_message("Note ajoutée avec succès!", ephemeral=True)

    @app_commands.command(name="show_notes", description="Affiche toutes vos notes.")
    async def show_notes(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        notes = self.get_notes_from_db(user_id)
        if notes:
            # Ajustez ici pour inclure à la fois l'ID et le contenu de la note dans l'affichage
            notes_content = "\n".join(f"{index+1}: {note_content}" for index, (note_id, note_content) in enumerate(notes))
            await interaction.response.send_message(f"Vos notes:\n{notes_content}", ephemeral=True)
        else:
            await interaction.response.send_message("Vous n'avez pas encore de notes.", ephemeral=True)


    @app_commands.command(name="rm_note", description="Supprime une note spécifique.")
    @app_commands.describe(index="Index de la note à supprimer.")
    async def delete_note(self, interaction: discord.Interaction, index: int):
        user_id = str(interaction.user.id)
        notes = self.get_notes_from_db(user_id)
        if index < 1 or index > len(notes):
            await interaction.response.send_message("Index invalide.", ephemeral=True)
            return
        note_id = notes[index - 1][0]  # Assumer que [0] est l'ID de la note
        self.delete_note_from_db(note_id)
        await interaction.response.send_message(f"Note #{index} supprimée.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(NoteTaking(bot))
