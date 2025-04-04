import discord
from discord.ext import commands
import json
import os
import random

# Définir combien de commandes par page
COMMANDS_PER_PAGE = 10
ADMIN_ROLE_ID = 123456  # Remplace par l'ID du rôle autorisé à créer/éditer/supprimer

class CustomTextCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.custom_commands = {}
        # Charger les commandes sauvegardées au démarrage
        self.load_commands()

    # Vérification si l'utilisateur a le bon rôle
    def has_admin_role():
        async def predicate(interaction: discord.Interaction):
            role = discord.utils.get(interaction.user.roles, id=ADMIN_ROLE_ID)
            if not role:
                print(f"Utilisateur {interaction.user} n'a pas le rôle requis.")  # Debug pour vérifier
                # Envoyer un message personnalisé à l'utilisateur
                error_responses = [
                    "T'as cru avoir suffisamment d'importance pour avoir le droit d'utiliser cette commande?",
                    "Essaye encore, mais avec un peu plus d'autorité peut-être.",
                    "Non, tu n'as pas les droits pour faire ça, désolé.",
                    "Tu penses vraiment pouvoir utiliser cette commande? Pas aujourd'hui.",
                    "Accès refusé. Peut-être un jour, mais pas maintenant.",
                    "Les recrutements sont clos pour ce job. Désolé",
                    "Voir avec Soupole"
                ]
                random_response = random.choice(error_responses)
                try:
                    await interaction.response.send_message(random_response, ephemeral=False)
                except discord.errors.InteractionResponded:
                    await interaction.followup.send(random_response, ephemeral=False)

                # Lever l'exception après avoir envoyé le message
                raise discord.app_commands.CheckFailure("unauthorized")
            return True
        return discord.app_commands.check(predicate)

    # Commande pour créer une nouvelle commande dynamique avec un texte ou un gif
    @discord.app_commands.command(name="create_text", description="Créer une commande personnalisée avec texte ou GIF.")
    @has_admin_role()  # Vérifie si l'utilisateur a le rôle admin
    async def create_text(self, interaction: discord.Interaction, command_name: str, response_text: str = None, image_url: str = None):
        """Créer une commande personnalisée qui répond avec un texte ou un GIF"""
        
        # S'assurer que la commande commence par '!'
        if not command_name.startswith("!"):
            await interaction.response.send_message("La commande doit commencer par un '!' (ex: !ma_commande).", ephemeral=True)
            return

        # S'assurer qu'il y a soit un texte soit un GIF
        if not response_text and not image_url:
            await interaction.response.send_message("Vous devez fournir au moins un texte ou une image/GIF pour créer cette commande.", ephemeral=True)
            return

        # Enregistrer la commande dans le dictionnaire
        self.custom_commands[command_name] = {"text": response_text, "image": image_url}

        # Sauvegarder les commandes dans un fichier JSON
        self.save_commands()

        await interaction.response.send_message(f"Commande `{command_name}` créée avec succès.", ephemeral=True)

    # Commande pour lister toutes les commandes personnalisées avec pagination
    @discord.app_commands.command(name="list_commands", description="Liste toutes les commandes personnalisées.")
    async def list_commands(self, interaction: discord.Interaction):
        """Lister toutes les commandes personnalisées avec pagination"""
        if not self.custom_commands:
            await interaction.response.send_message("Aucune commande personnalisée n'a été créée.", ephemeral=True)
            return

        # Diviser les commandes en pages
        commands_list = list(self.custom_commands.items())
        total_pages = (len(commands_list) - 1) // COMMANDS_PER_PAGE + 1

        # Afficher la première page
        embed = self.get_commands_embed(commands_list, 0, total_pages)
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Créer la vue avec la pagination
        view = PaginationView(commands_list, 0, total_pages, self.update_commands_embed)
        await interaction.edit_original_response(view=view)

    # Commande pour éditer une commande personnalisée existante
    @discord.app_commands.command(name="edit_command", description="Modifier une commande personnalisée.")
    @has_admin_role()  # Vérifie si l'utilisateur a le rôle admin
    async def edit_command(self, interaction: discord.Interaction, command_name: str, new_text: str = None, new_image_url: str = None):
        """Modifier le texte ou l'image d'une commande existante"""
        if command_name not in self.custom_commands:
            await interaction.response.send_message(f"La commande `{command_name}` n'existe pas.", ephemeral=True)
            return

        # Mettre à jour le texte et/ou le GIF si fourni
        if new_text:
            self.custom_commands[command_name]["text"] = new_text
        if new_image_url:
            self.custom_commands[command_name]["image"] = new_image_url

        # Sauvegarder les modifications
        self.save_commands()

        await interaction.response.send_message(f"Commande `{command_name}` modifiée avec succès.", ephemeral=True)

    # Commande pour supprimer plusieurs commandes personnalisées
    @discord.app_commands.command(name="delete_commands", description="Supprimer plusieurs commandes personnalisées.")
    @has_admin_role()  # Vérifie si l'utilisateur a le rôle admin
    async def delete_commands(self, interaction: discord.Interaction, command_names: str):
        """Supprimer plusieurs commandes personnalisées"""
        
        # Diviser les noms de commande si plusieurs sont donnés
        command_list = command_names.split(" ")

        deleted_commands = []
        not_found_commands = []

        # Parcourir chaque commande et tenter de les supprimer
        for command_name in command_list:
            if command_name in self.custom_commands:
                del self.custom_commands[command_name]
                deleted_commands.append(command_name)
            else:
                not_found_commands.append(command_name)

        # Sauvegarder les modifications
        self.save_commands()

        # Créer un message de retour indiquant les commandes supprimées et celles non trouvées
        if deleted_commands:
            success_message = f"Commandes supprimées avec succès : {', '.join(deleted_commands)}"
        else:
            success_message = "Aucune commande supprimée."

        if not_found_commands:
            error_message = f"Commandes non trouvées : {', '.join(not_found_commands)}"
        else:
            error_message = ""

        # Envoyer le résultat final à l'utilisateur
        final_message = f"{success_message}\n{error_message}"
        await interaction.response.send_message(final_message, ephemeral=True)

    # Fonction pour générer l'embed d'une page de commandes
    def get_commands_embed(self, commands_list, current_page, total_pages):
        start = current_page * COMMANDS_PER_PAGE
        end = start + COMMANDS_PER_PAGE
        commands_page = commands_list[start:end]

        embed = discord.Embed(title="Commandes personnalisées", color=discord.Color.blue())
        for command, _ in commands_page:
            # Ajouter seulement le nom de la commande sans son contenu
            embed.add_field(name=command, value="Commande personnalisée", inline=False)

        embed.set_footer(text=f"Page {current_page + 1}/{total_pages}")
        return embed

    # Fonction pour mettre à jour l'embed avec les nouvelles commandes
    async def update_commands_embed(self, interaction: discord.Interaction, commands_list, current_page, total_pages):
        # Mettre à jour l'embed
        embed = self.get_commands_embed(commands_list, current_page, total_pages)
        view = PaginationView(commands_list, current_page, total_pages, self.update_commands_embed)

        # Utiliser response.edit_message au lieu de edit_original_response pour éditer le message courant
        await interaction.response.edit_message(embed=embed, view=view)

    # Fonction pour gérer les commandes préfixées par "!"
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:  # Ignorer les messages du bot lui-même
            return

        if message.content.startswith("!"):  # Vérifier si le message commence par "!"
            command_name = message.content.split()[0]  # Récupérer la commande (ex: !bot)
            
            if command_name in self.custom_commands:
                # Extraire les arguments (par exemple, les utilisateurs mentionnés après la commande)
                args = message.content.split()[1:]

                # Récupérer le texte et le gif (si disponible) pour cette commande
                response = self.custom_commands[command_name].get("text")
                image_url = self.custom_commands[command_name].get("image")

                # Remplacer {user} par la mention d'utilisateur si elle est présente dans le texte
                if args and response and '{user}' in response:
                    # Supposons que le premier argument soit un utilisateur mentionné
                    mentioned_user = args[0]
                    
                    # Remplacer {user} par la mention de l'utilisateur
                    response = response.replace("{user}", mentioned_user)

                # Envoyer le texte avec les sauts de ligne et l'image (si fourni)
                if response and image_url:
                    await message.channel.send(f"{response}\n{image_url}")
                elif response:
                    await message.channel.send(response)
                elif image_url:
                    await message.channel.send(image_url)

        # Laisser les autres événements on_message se propager
        await self.bot.process_commands(message)

    # Fonction pour sauvegarder les commandes dans un fichier JSON
    def save_commands(self):
        with open("custom_commands.json", "w") as file:
            json.dump(self.custom_commands, file)

    # Fonction pour charger les commandes depuis un fichier JSON
    def load_commands(self):
        if os.path.exists("custom_commands.json"):
            with open("custom_commands.json", "r") as file:
                self.custom_commands = json.load(file)
        else:
            self.custom_commands = {}

    # Gérer les erreurs avec des messages personnalisés
    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error):
        if isinstance(error, discord.app_commands.CheckFailure):
            # Liste des réponses possibles
            error_responses = [
                "T'as cru avoir suffisamment d'importance pour avoir le droit d'utiliser cette commande?",
                "Essaye encore, mais avec un peu plus d'autorité peut-être.",
                "Non, tu n'as pas les droits pour faire ça, désolé.",
                "Tu penses vraiment pouvoir utiliser cette commande? Pas aujourd'hui.",
                "Accès refusé. Peut-être un jour, mais pas maintenant.",
                "Les recrutements sont clos pour ce job. Désolé",
                "Voir avec Soupole"
            ]

            # Choisir une réponse au hasard
            random_response = random.choice(error_responses)

            # Envoyer la réponse choisie
            try:
                await interaction.response.send_message(random_response, ephemeral=False)
            except discord.errors.InteractionResponded:
                await interaction.followup.send(random_response, ephemeral=False)

        else:
            # Gérer les autres erreurs
            try:
                await interaction.response.send_message("Une erreur est survenue lors de l'exécution de la commande.")
            except discord.errors.InteractionResponded:
                await interaction.followup.send("Une erreur est survenue lors de l'exécution de la commande.")

# Classe pour gérer les boutons de pagination
class PaginationView(discord.ui.View):
    def __init__(self, commands_list, current_page, total_pages, callback):
        super().__init__()
        self.commands_list = commands_list
        self.current_page = current_page
        self.total_pages = total_pages
        self.callback = callback

        # Désactiver le bouton "Précédent" si on est sur la première page
        self.previous.disabled = current_page == 0
        # Désactiver le bouton "Suivant" si on est sur la dernière page
        self.next.disabled = current_page == total_pages - 1

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.primary, custom_id="previous")
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Aller à la page précédente"""
        await self.callback(interaction, self.commands_list, self.current_page - 1, self.total_pages)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.primary, custom_id="next")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Aller à la page suivante"""
        await self.callback(interaction, self.commands_list, self.current_page + 1, self.total_pages)

async def setup(bot):
    await bot.add_cog(CustomTextCommands(bot))
