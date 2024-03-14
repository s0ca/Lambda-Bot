import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp as youtube_dl
from datetime import timedelta
from typing import Optional
import logging
import asyncio
import math
import os

logger = logging.getLogger('yt_dlp')
logger.setLevel(logging.ERROR)


FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

class Music(commands.GroupCog, name="music"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.disconnect_timer = None
        super().__init__()
        self.current_volume = 0.3  # Valeur initiale du volume
        self.queue = []  # Initialiser la file d'attente des morceaux

    async def start_disconnect_timer(self, voice_client):
        await asyncio.sleep(300)  # Attendre 5 minutes
        if voice_client.is_connected():
            if len(voice_client.channel.members) == 1:  # Si le bot est seul dans le canal
                await voice_client.disconnect()
                print("Bot déconnecté du canal vocal pour inactivité.")
                self.disconnect_timer = None

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        voice_client = self.bot.voice_clients[0] if self.bot.voice_clients else None
        if voice_client:
            # Si le bot rejoint un canal vocal ou si quelqu'un quitte le canal et le bot est seul
            if after.channel == voice_client.channel or (before.channel == voice_client.channel and len(before.channel.members) == 1):
                if self.disconnect_timer:
                    self.disconnect_timer.cancel()  # Annuler le timer précédent s'il existe
                self.disconnect_timer = self.bot.loop.create_task(self.start_disconnect_timer(voice_client))

    # Méthode d'ajout d'une chanson à la file d'attente
    async def add_song_to_queue(self, interaction: discord.Interaction, url: str, member: discord.Member):
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio',
            'default_search': 'auto',
            'quiet': True,
            'noplaylist': True,
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video = info_dict['entries'][0] if 'entries' in info_dict else info_dict
            song = {
                'url': video['url'],
                'title': video['title'],
                'duration': video.get('duration', 0),
                'thumbnail': video.get('thumbnail', ''),
                'requester': member,
                'voice_client': interaction.guild.voice_client,
                'channel': interaction.channel
            }

        self.queue.append(song)
        if len(self.queue) == 1 and not interaction.guild.voice_client.is_playing():
            await self.play_next()

    async def play_next(self):
        if len(self.queue) > 0:
            next_song = self.queue.pop(0)
            voice_client = next_song['voice_client']
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(next_song['url'], **FFMPEG_OPTIONS), volume=self.current_volume)
            def after_playing(e):
                self.bot.loop.create_task(self.play_next())
            voice_client.play(source, after=after_playing)
            embed = await self.create_embed(next_song['title'], next_song['url'], next_song['duration'], next_song['thumbnail'], next_song['requester'])
            await next_song['channel'].send(embed=embed)

    async def create_embed(self, video_title: str, video_url: str, video_duration: int, video_thumbnail: str, requester: discord.Member):
        duration = str(timedelta(seconds=video_duration))
        embed = discord.Embed(title="Now Playing", description=f"```css\n{video_title}\n```", color=discord.Color.blurple())
        embed.add_field(name="Duration", value=duration, inline=False)
        embed.add_field(name="Queried by", value=requester.mention, inline=False)
        embed.add_field(name="Direct link", value=f"[Here]({video_url})", inline=False)
        embed.set_thumbnail(url=video_thumbnail)
        embed.set_footer(text="Lambda Bot v3.03")
        return embed

    # Méthode pour vérifier et gérer la connexion au canal vocal
    async def ensure_voice_connection(self, interaction: discord.Interaction):
        member = interaction.user
        if member.voice is None:
            await interaction.response.send_message("Vous devez être dans un canal vocal pour utiliser cette commande.", ephemeral=True)
            return False
        voice_channel = member.voice.channel
        voice_client = interaction.guild.voice_client
        if voice_client is None:
            await voice_channel.connect()
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)
        return True

    # Play
    @app_commands.command(name="play", description="Joue de la musique dans votre canal vocal.")
    @app_commands.describe(prompt="Entrez votre recherche ici URL ou STRING.")
    async def play(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        if not await self.ensure_voice_connection(interaction):
            return
        await self.add_song_to_queue(interaction, prompt, interaction.user)
        await interaction.followup.send(f"**{prompt}** ajouté à la file d'attente.", ephemeral=False)

    # Pause
    @app_commands.command(name="pause", description="Met en pause la lecture actuelle ou la reprend si elle est déjà en pause.")
    async def pause(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        
        if voice_client is None:
            await interaction.response.send_message("Le bot n'est pas connecté à un canal vocal.", ephemeral=True)
            return

        if voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("Lecture mise en pause.", ephemeral=False)
        elif voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("Lecture reprise.", ephemeral=False)
        else:
            await interaction.response.send_message("Aucune musique en cours de lecture ou déjà en pause.", ephemeral=True)

    # List d'attente
    @app_commands.command(name="list", description="Affiche les chansons dans la file d'attente.")
    @app_commands.describe(page="Page de la liste d'attente à afficher.")
    async def list(self, interaction: discord.Interaction, page: int = 1):
        items_per_page = 10
        pages = math.ceil(len(self.queue) / items_per_page)

        if page < 1 or page > pages:
            await interaction.response.send_message(f"Numéro de page invalide. Veuillez choisir un numéro entre 1 et {pages}.", ephemeral=True)
            return

        start = (page - 1) * items_per_page
        end = start + items_per_page
        queue_page = self.queue[start:end]

        embed = discord.Embed(title=f"File d'attente - Page {page}/{pages}", color=discord.Color.blue())
        for i, song in enumerate(queue_page, start=start):
            song_title = song['title']
            requester = song['requester'].mention
            embed.add_field(name=f"{i+1}. {song_title}", value=f"Requête par {requester}", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=False)
    
    # Supprime une entrée de la File d'attente
    @app_commands.command(name="remove", description="Supprime une chanson de la file d'attente par son index.")
    @app_commands.describe(index="L'index de la chanson à supprimer.")
    async def remove(self, interaction: discord.Interaction, index: int):
        if index < 1 or index > len(self.queue):
            await interaction.response.send_message("Index invalide. Assurez-vous de choisir un index valide de la liste d'attente.", ephemeral=True)
            return

        song_to_remove = self.queue.pop(index - 1)
        await interaction.response.send_message(f"**{song_to_remove['title']}** a été retiré de la file d'attente.", ephemeral=False)

    # Next
    @app_commands.command(name="next", description="Passe à la chanson suivante dans la file d'attente.")
    async def next(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client is None or not voice_client.is_connected():
            await interaction.response.send_message("Le bot n'est pas connecté à un canal vocal.", ephemeral=True)
            return

        if not voice_client.is_playing() and not voice_client.is_paused():
            await interaction.response.send_message("Il n'y a pas de musique en cours de lecture.", ephemeral=True)
            return

        if len(self.queue) == 0:
            await interaction.response.send_message("Il n'y a pas d'autres chansons dans la file d'attente.", ephemeral=True)
            return

        # Arrête la chanson actuelle, ce qui déclenchera l'événement 'after' du voice_client.play() pour jouer la chanson suivante
        voice_client.stop()
        await interaction.response.send_message("Passage à la chanson suivante...", ephemeral=False)

    # Stop
    @app_commands.command(name="stop", description="Arrête la musique actuellement jouée et se déconnecte du canal vocal.")
    async def stop(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client is None:
            await interaction.response.send_message("Le bot n'est pas connecté à un canal vocal.", ephemeral=True)
            return
        
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
            message = "Musique arrêtée."
        else:
            message = "Aucune musique n'est actuellement jouée."

        # Se déconnecter indépendamment de si la musique était jouée ou non
        await voice_client.disconnect()
        await interaction.response.send_message(f"{message} Bot déconnecté du canal vocal.", ephemeral=True)

    # Gestion du Volume
    @app_commands.command(name="volume", description="Ajuste le volume de la musique ou affiche le volume actuel.")
    @app_commands.describe(volume="Volume entre 0 et 100. Laissez vide pour voir le volume actuel.")
    async def volume(self, interaction: discord.Interaction, volume: Optional[int] = None):
        voice_client = interaction.guild.voice_client
        if voice_client is None or not voice_client.is_connected():
            await interaction.response.send_message("Le bot n'est pas connecté à un canal vocal.", ephemeral=True)
            return

        # Si aucun volume n'est fourni, affichez le volume actuel
        if volume is None:
            current_volume = int(self.current_volume * 100)  # Convertissez le volume en pourcentage
            await interaction.response.send_message(f"Le volume actuel est de {current_volume}%.", ephemeral=True)
            return

        # Vérifiez si le volume fourni est dans la plage autorisée
        if volume < 0 or volume > 100:
            await interaction.response.send_message("Le volume doit être entre 0 et 100.", ephemeral=True)
            return

        # Ajustez le volume
        self.current_volume = volume / 100.0
        if voice_client.source and isinstance(voice_client.source, discord.PCMVolumeTransformer):
            voice_client.source.volume = self.current_volume
        await interaction.response.send_message(f"Volume réglé sur {volume}%.", ephemeral=False)

    # Liste les playlists disponibles
    @app_commands.command(name="playlists", description="Liste les playlists disponibles.")
    @app_commands.describe(page="Page de la liste des playlists à afficher.")
    async def playlists(self, interaction: discord.Interaction, page: int = 1):
        playlists_dir = "playlists"
        playlists_files = [f for f in os.listdir(playlists_dir) if os.path.isfile(os.path.join(playlists_dir, f))]
        playlists_files.sort()  # Assurez-vous que la liste est triée pour une pagination cohérente

        items_per_page = 10
        pages = math.ceil(len(playlists_files) / items_per_page)

        if page < 1 or page > pages:
            await interaction.response.send_message(f"Numéro de page invalide. Veuillez choisir un numéro entre 1 et {pages}.", ephemeral=True)
            return

        start = (page - 1) * items_per_page
        end = start + items_per_page
        playlists_page = playlists_files[start:end]

        description = '\n'.join(f'{i+1+start}. {playlist}' for i, playlist in enumerate(playlists_page))
        embed = discord.Embed(title=f"Playlists disponibles - Page {page}/{pages}", description=description, color=discord.Color.blue())

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Crée une nouvelle playlist
    @app_commands.command(name="new_playlist", description="Crée une nouvelle playlist.")
    @app_commands.describe(name="Nom de la playlist", urls="Liste des URLs séparées par une virgule")
    async def new_playlist(self, interaction: discord.Interaction, name: str, urls: str):
        playlists_dir = "playlists"
        file_path = os.path.join(playlists_dir, name)
        with open(file_path, 'w') as playlist_file:
            for url in urls.split(','):
                playlist_file.write(url.strip() + '\n')
        await interaction.response.send_message(f"Playlist `{name}` créée avec succès.", ephemeral=True)

    # Joue une playlist
    @app_commands.command(name="play_playlist", description="Joue la playlist à l'index spécifié.")
    @app_commands.describe(index="Index de la playlist à jouer.")
    async def play_playlist(self, interaction: discord.Interaction, index: int):
        playlists_dir = "playlists"
        playlists_files = [f for f in os.listdir(playlists_dir) if os.path.isfile(os.path.join(playlists_dir, f))]
        playlists_files.sort()

        # Vérifiez si l'index est valide
        if index < 1 or index > len(playlists_files):
            await interaction.response.send_message(f"L'index spécifié est invalide. Choisissez un numéro entre 1 et {len(playlists_files)}.", ephemeral=True)
            return

        # Utilisez l'index pour obtenir le nom de la playlist
        playlist_name = playlists_files[index - 1]

        file_path = os.path.join(playlists_dir, playlist_name)
        if not await self.ensure_voice_connection(interaction):
            return
        if not os.path.exists(file_path):
            await interaction.response.send_message(f"La playlist `{playlist_name}` n'existe pas.", ephemeral=True)
            return

        with open(file_path, 'r') as playlist_file:
            urls = [url.strip() for url in playlist_file if url.strip()]
            await interaction.response.defer(ephemeral=False)
            for url in urls:
                await self.add_song_to_queue(interaction, url, interaction.user)
                await asyncio.sleep(1)

        await interaction.followup.send(f"Playlist `{playlist_name}` chargée et ajoutée à la file d'attente.")



async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))

