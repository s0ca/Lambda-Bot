import base64
import binascii
import urllib.parse
from discord.ext import commands
from discord import app_commands
import discord

class Encoding(commands.GroupCog, name="encoding"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="b64", description="Encode ou décode en Base64.")
    @app_commands.describe(encode_or_decode="Choisissez 'encode' ou 'decode'.", string="La chaîne à encoder ou décoder.")
    async def b64(self, interaction: discord.Interaction, encode_or_decode: str, string: str):
        byted_str = str.encode(string)
        if encode_or_decode.lower() == 'decode':
            decoded = base64.b64decode(byted_str).decode('utf-8')
            await interaction.response.send_message(decoded)
        elif encode_or_decode.lower() == 'encode':
            encoded = base64.b64encode(byted_str).decode('utf-8').replace('\n', '')
            await interaction.response.send_message(encoded)

    @app_commands.command(name="b32", description="Encode ou décode en Base32.")
    @app_commands.describe(encode_or_decode="Choisissez 'encode' ou 'decode'.", string="La chaîne à encoder ou décoder.")
    async def b32(self, interaction: discord.Interaction, encode_or_decode: str, string: str):
        byted_str = str.encode(string)
        if encode_or_decode.lower() == 'decode':
            decoded = base64.b32decode(byted_str).decode('utf-8')
            await interaction.response.send_message(decoded)
        elif encode_or_decode.lower() == 'encode':
            encoded = base64.b32encode(byted_str).decode('utf-8').replace('\n', '')
            await interaction.response.send_message(encoded)

    @app_commands.command(name="binary", description="Encode ou décode en binaire.")
    @app_commands.describe(encode_or_decode="Choisissez 'encode' ou 'decode'.", string="La chaîne à encoder ou décoder.")
    async def binary(self, interaction: discord.Interaction, encode_or_decode: str, string: str):
        if encode_or_decode.lower() == 'decode':
            string = string.replace(" ", "")
            data = int(string, 2)
            decoded = data.to_bytes((data.bit_length() + 7) // 8, 'big').decode()
            await interaction.response.send_message(decoded)
        elif encode_or_decode.lower() == 'encode':
            encoded = bin(int.from_bytes(string.encode(), 'big')).replace('b', '')
            await interaction.response.send_message(encoded)

    @app_commands.command(name="hex", description="Encode ou décode en hexadécimal.")
    @app_commands.describe(encode_or_decode="Choisissez 'encode' ou 'decode'.", string="La chaîne à encoder ou décoder.")
    async def hex(self, interaction: discord.Interaction, encode_or_decode: str, string: str):
        if encode_or_decode.lower() == 'decode':
            string = string.replace(" ", "")
            decoded = binascii.unhexlify(string).decode('ascii')
            await interaction.response.send_message(decoded)
        elif encode_or_decode.lower() == 'encode':
            byted = string.encode()
            encoded = binascii.hexlify(byted).decode('ascii')
            await interaction.response.send_message(encoded)

    @app_commands.command(name="url", description="Encode ou décode une URL.")
    @app_commands.describe(encode_or_decode="Choisissez 'encode' ou 'decode'.", message="L'URL à encoder ou décoder.")
    async def url(self, interaction: discord.Interaction, encode_or_decode: str, message: str):
        if encode_or_decode.lower() == 'decode':
            if '%20' in message:
                message = message.replace('%20', ' ')
            decoded = urllib.parse.unquote(message)
            await interaction.response.send_message(decoded)
        elif encode_or_decode.lower() == 'encode':
            encoded = urllib.parse.quote(message)
            await interaction.response.send_message(encoded)

async def setup(bot: commands.Bot):
    await bot.add_cog(Encoding(bot))
