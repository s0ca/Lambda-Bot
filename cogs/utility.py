import json
import discord
from discord.ext import commands
from discord import app_commands

class Utility(commands.GroupCog, name="utility"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="length", description="Compte les caractères dans une chaîne donnée.")
    async def length(self, interaction: discord.Interaction, string: str):
        await interaction.response.send_message(len(string))

    @app_commands.command(name="wordcount", description="Compte les mots dans une chaîne donnée.")
    async def wordcount(self, interaction: discord.Interaction, string: str):
        words = string.split()
        await interaction.response.send_message(len(words))

    @app_commands.command(name="reverse", description="Inverse les caractères dans une chaîne donnée.")
    async def reverse(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(message[::-1])

    @app_commands.command(name="count", description="Compte chaque occurrence de caractère dans la chaîne donnée.")
    async def count(self, interaction: discord.Interaction, message: str):
        count = {}
        for char in message:
            if char in count:
                count[char] += 1
            else:
                count[char] = 1
        await interaction.response.send_message(str(count))

    @app_commands.command(name="magicb", description="Affiche les signatures de fichiers connues pour un format donné.")
    async def magicb(self, interaction: discord.Interaction, filetype: str):
        try:
            with open('magic.json', 'r') as file:
                alldata = json.load(file)
            if filetype in alldata:
                messy_signs = str(alldata[filetype]['signs'])
                signs = messy_signs.split('[')[1].split(',')[0].split(']')[0].replace("'", '')
                mime_type = alldata[filetype]['mime']
                response = f"{mime_type}: {signs}"
            else:
                response = f"{filetype} not found :( If you think this filetype should be included please request it."

            await interaction.response.send_message(response)
        except Exception as e:
            await interaction.response.send_message("An error occurred while processing the request.")

    @app_commands.command(name="purge", description="la grande purge messagère")
    async def purge(self, interaction: discord.Interaction, nbr: int = 1 ):
        await interaction.response.send_message(f"Suppression de {nbr} messages...", ephemeral=True)
        deleted_messages = await interaction.channel.purge(limit=nbr)
        await interaction.followup.send(f"{len(deleted_messages)} messages supprimés.", ephemeral=True)

    @app_commands.command(name="whois", description="Affiche les informations sur un membre.")
    @app_commands.describe(member="Le membre dont vous voulez obtenir des informations.")
    async def whois(self, interaction: discord.Interaction, member: discord.Member = None):
        # Si aucun membre n'est spécifié, utiliser celui qui a lancé la commande
        if member is None:
            member = interaction.user

        roles = [role for role in member.roles[1:]] # Ignorer le rôle @everyone
        embed = discord.Embed(colour=discord.Colour.orange(), timestamp=discord.utils.utcnow(), title=f"Infos sur {member}")
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID:", value=member.id, inline=True)
        embed.add_field(name="Pseudo:", value=member.display_name, inline=True)
        embed.add_field(name="Créé le:", value=member.created_at.strftime("%d/%m/%Y à %H:%M:%S"), inline=True)
        embed.add_field(name="Rejoint le:", value=member.joined_at.strftime("%d/%m/%Y à %H:%M:%S"), inline=True)
        embed.add_field(name="Rôles:", value=" ".join(role.mention for role in roles) if roles else "Aucun", inline=False)
        embed.add_field(name="Rôle le plus haut:", value=member.top_role.mention, inline=True)
        embed.set_footer(text=f"Requête de {interaction.user}", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
