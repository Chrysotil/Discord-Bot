import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import ffmpeg
from discord import FFmpegPCMAudio
import asyncio

TOKEN = 'ur token here'
SPOTIFY_CLIENT_ID = 'ur client id here'
SPOTIFY_CLIENT_SECRET = 'ur client secret here'

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))

@bot.event
async def on_ready():
    print(f'Bot olarak giriş yapıldı: {bot.user.name}')

@bot.command()
async def play(ctx):
    voice_channel = ctx.author.voice.channel

    if voice_channel:
        if not ctx.voice_client:
            voice_client = await voice_channel.connect()
            await ctx.send(f'Bot, {voice_channel.name} kanalına bağlandı.')
        else:
            await ctx.send('Bot zaten bir ses kanalına bağlı.')
    else:
        await ctx.send('Bir ses kanalında olmanız gerekiyor.')
        return

    # Spotify API'den çalma listesi al
    playlist_id = '2dRGyefBTtruj4AhjDl5B6'
    results = spotify.playlist(playlist_id)

    if 'tracks' in results and 'items' in results['tracks']:
        tracks = results['tracks']['items']

        if not tracks:
            await ctx.send('Çalma listesinde hiçbir şarkı bulunamadı.')
            return

        # İlk şarkıyı alalım
        first_track = tracks[0]
        track_name = first_track['track']['name']
        artists = [artist['name'] for artist in first_track['track']['artists']]
        artist_names = ', '.join(artists)
        track_info = f'{track_name} - {artist_names}'

        await ctx.send(f'Şimdi çalınıyor: {track_info}')

        # Şarkıyı ses kanalında çalma işlemini ekleyin
        voice_client = ctx.voice_client

        if voice_client.is_playing():
            voice_client.stop()

        # Şarkının ses dosyasının URL'sini alın veya doğrudan ses dosyasının yolunu belirtin
        song_url = first_track['track']['preview_url']

        # FFmpeg ile sesi çal
        voice_client.play(discord.FFmpegPCMAudio(song_url), after=lambda e: play_next(ctx, tracks, first_track))

    else:
        await ctx.send('Çalma listesinden şarkılar alınırken bir hata oluştu.')

def play_next(ctx, tracks, current_track):
    voice_client = ctx.voice_client

    if voice_client.is_playing():
        return

    current_index = tracks.index(current_track)
    next_index = current_index + 1

    if next_index < len(tracks):
        next_track = tracks[next_index]
        track_name = next_track['track']['name']
        artists = [artist['name'] for artist in next_track['track']['artists']]
        artist_names = ', '.join(artists)
        track_info = f'{track_name} - {artist_names}'

        asyncio.run_coroutine_threadsafe(ctx.send(f'Şimdi çalınıyor: {track_info}'), bot.loop)

        song_url = next_track['track']['preview_url']

        if song_url is not None:
            voice_client.play(discord.FFmpegPCMAudio(song_url), after=lambda e: play_next(ctx, tracks, next_track))
        else:
            play_next(ctx, tracks, next_track)  # Şarkı URL'si yoksa bir sonraki şarkıya geç

    else:
        asyncio.run_coroutine_threadsafe(voice_client.disconnect(), bot.loop)
        asyncio.run_coroutine_threadsafe(ctx.send('Çalma listesi tamamlandı. Ses kanalından ayrıldım.'), bot.loop)

@bot.command()
async def volume(ctx, level: int):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice_client:
        if 0 <= level <= 100:
            voice_client.volume = level / 100  # 0-1 aralığında bir değer bekleniyor
            await ctx.send(f"Ses seviyesi {level}% olarak ayarlandı.")
        else:
            await ctx.send("Geçerli bir ses seviyesi giriniz (0-100 aralığında).")
    else:
        await ctx.send("Bot hiçbir ses kanalına bağlı değil.")


@bot.command()
async def stop(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice_client.is_connected():
        voice_client.stop()
        await voice_client.disconnect()
        await ctx.send('Çalma durduruldu ve ses kanalından ayrıldım.')
    else:
        await ctx.send('Bot hiçbir ses kanalına bağlı değil.')

@bot.command()
async def next(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice_client.is_playing():
        voice_client.stop()
        await ctx.send('Şarkı atlandı.')
    else:
        await ctx.send('Şu anda herhangi bir şarkı çalmıyor.')

@bot.command()
async def pause(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice_client.is_playing():
        voice_client.pause()
        await ctx.send('Şarkı duraklatıldı.')
    else:
        await ctx.send('Şu anda herhangi bir şarkı çalmıyor.')

@bot.command()
async def resume(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice_client.is_paused():
        voice_client.resume()
        await ctx.send('Şarkı devam ettiriliyor.')
    else:
        await ctx.send('Şu anda herhangi bir şarkı duraklatılmış değil.')

@bot.event
async def on_message(message):
    if message.content.lower() == 'sa':
        await message.channel.send(f'{message.author.mention} Merhaba, nasılsınız?')

    target_user = "Target User"  # Hedef kullanıcının tam kullanıcı adını buraya yazın

    if str(message.author) == target_user:
        user = message.author
        dm_channel = await user.create_dm()
        await dm_channel.send('type here')

    await bot.process_commands(message)


bot.run(TOKEN)