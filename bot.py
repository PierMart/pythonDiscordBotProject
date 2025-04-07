import asyncio
import json, re,os,sys,discord,yt_dlp

from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL

discord.opus.load_opus('/opt/homebrew/lib/libopus.dylib')  # pour mac M1/M2/M3
from discord.ext import commands
from pushDocs import setToGoogleSheet
from datetime import datetime
# Charger le fichier de configuration
with open('API_KEY/config.json') as config_file:
    config = json.load(config_file)

DISCORD_TOKEN = config['DISCORD_TOKEN']
# Variables globales
log_channel_id = 1358832435613405224  # Salon de logs
log_guild_id = 958079421607186453  # ID de la guilde (serveur)
# Chemin vers le fichier pour stocker l'ID du salon
FILE_PATH = "reboot_channel_id.json"
music_queue = []

def clear_json_file(file_path):
    # Ouvre le fichier en mode écriture pour le vider
    with open(file_path, 'w') as file:
        # Écrire un objet vide dans le fichier JSON
        json.dump({}, file)

def save_reboot_channel_id(channel_id):
    """Sauvegarde l'ID du salon dans un fichier JSON."""
    with open(FILE_PATH, "w") as file:
        json.dump({"reboot_channel_id": channel_id}, file)

def load_reboot_channel_id():
    """Charge l'ID du salon depuis le fichier JSON."""
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r") as file:
            data = json.load(file)
            return data.get("reboot_channel_id")
    return None
reboot_channel_id = load_reboot_channel_id() # Charge l'ID du salon de reboot


# Initialisation du bot avec les intents
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Variables globales
listening = False
listening_harem_name = False
FFMPEG_OPTIONS = {
    'options': '-vn -loglevel panic'
}


# Fonction pour récupérer le lien direct audio YouTube
def get_audio_url(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info['url'], info['title']
user_messages = {}
first_waifu = {}
mudae_original_messages = {}
message_edit_count = {}
mudae_messages = []
nbr_page = 0

# Dictionnaire pour stocker les données du harem
harem_dict = {
    "user": "",
    "characters": []
}


# Sauvegarder l'état actuel dans un fichier JSON
def save_state(harem_dict, page_number, name):
    state = {
        "harem": harem_dict,
        "page_number": page_number
    }
    with open(f'harem_data_{name}.json', 'w') as file:
        json.dump(state, file, indent=4)


# Charger l'état depuis un fichier JSON
def load_state(name):
    try:
        with open(f'harem_data_{name}.json', 'r') as file:
            state = json.load(file)
            return state["harem"], state["page_number"]
    except FileNotFoundError:
        return {"user": "", "characters": []}, 0


# Commande pour activer l'écoute des messages de Mudae
@bot.command()
async def ls(ctx):
    global listening
    listening = True
    user_messages[ctx.author.id] = None
    await ctx.send('Écoute des messages de Mudae activée.')

# Redémarre le bot
@bot.command()
async def reboot(ctx):
    global reboot_channel_id
    reboot_channel_id = ctx.channel.id  # Stocke l'ID du salon où !reboot a été tapé
    save_reboot_channel_id(reboot_channel_id)  # Sauvegarde l'ID dans le fichier
    await ctx.send("🔄 Redémarrage de Freyja en cours...")
    await bot.close()
    os.execl(sys.executable, sys.executable, *sys.argv)


# Commande pour désactiver l'écoute
@bot.command()
async def nls(ctx):
    global listening
    listening = False
    await ctx.send('Écoute des messages de Mudae désactivée.')


# Commande pour définir un utilisateur pour le harem
@bot.command()
async def set(ctx, user: discord.User = None):
    global listening_harem_name
    listening_harem_name = True

    if user is None:
        user_messages[ctx.author.id] = ctx.author.id
    else:
        user_messages[user.id] = user.id

    await ctx.send('Faites la commande !mmi pour mettre a jour puis $mmi pour commencer à enregistrer le harem. Ou sinon faire directement $mmi pour commencer à enregistrer le harem pour la 1er fois .')


# Commande pour initialiser la capture du harem avec $mmi
@bot.command()
async def mmi(ctx):
    global listening_harem_name, harem_dict, message_edit_count, nbr_page

    listening_harem_name = True
    user_id = list(user_messages.keys())[-1]
    user = await bot.fetch_user(user_id)

    # Charger l'état précédent s'il existe
    harem_dict, nbr_page = load_state(user.name)
    message_edit_count = {}
    await ctx.send(f'Chargement de la progression pour {user.name}.')
@bot.command()
async def push(ctx, user: discord.User = None):
    if user is None:
        # Aucun utilisateur mentionné, utiliser l'auteur du message
        harem_name = ctx.author.name
        await ctx.send('Faites la commande $mmi pour définir le harem avec les images etc.')
    else:
        # Utilisateur mentionné, enregistrer l'identifiant de l'utilisateur mentionné
        harem_name = user.name
        await ctx.send(f'Faites la commande $mmi pour définir le harem avec les images etc. pour {user.mention}.')
    try:
        print(harem_name)
        await setToGoogleSheet(harem_name)
        await ctx.send(f'Les données du harem "{harem_name}" ont été envoyées avec succès à Google Sheets.')
    except FileNotFoundError:
        await ctx.send(f'Le fichier harem_data{harem_name}_.json n\'existe pas.')
    except json.JSONDecodeError:
        await ctx.send(f'Erreur lors de la lecture du fichier JSON harem_data{harem_name}_.json.')
    except Exception as e:
        await ctx.send(f'Une erreur inattendue s\'est produite : {e}')
@bot.command()
async def join(ctx):
    """Fait rejoindre le bot dans le canal vocal de l'utilisateur."""
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
        await ctx.send(f"✅ Rejoint {ctx.author.voice.channel.name}")
    else:
        await ctx.send("❌ Tu dois être dans un canal vocal.")

@bot.command()
async def leave(ctx):
    """Fait quitter le canal vocal au bot."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Déconnexion du canal vocal.")
    else:
        await ctx.send("Je ne suis pas dans un canal vocal.")

@bot.command()
async def skip(ctx):
    global music_queue

    # Vérifiez si le bot est connecté à un canal vocal
    if not ctx.voice_client:
        await ctx.send("❌ Je ne suis pas dans un canal vocal.")
        return

    # Arrête la musique actuelle s'il y en a une
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()

    # Passe à la musique suivante dans la file d'attente
    await play_next(ctx)

async def play_next(ctx):
    global music_queue

    if music_queue:
        url, title = music_queue.pop(0)  # Récupère la prochaine musique dans la file d'attente
        source = FFmpegPCMAudio(
            url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options="-vn"
        )
        ctx.voice_client.play(
            source,
            after=lambda e: bot.loop.create_task(play_next(ctx)) if music_queue else None
        )
        await ctx.send(f"🎶 Lecture : **{title}**")
    else:
        await ctx.send("✅ La file d'attente est vide.")
# Ajout d'une variable globale pour suivre l'activité
inactivity_timer = None
inactivity_timeout = 60  # 60 secondes d'inactivité avant de quitter le canal vocal

# Fonction pour arrêter la minuterie et faire quitter le bot
async def check_inactivity(ctx):
    global inactivity_timer
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("⏰ Le bot a quitté le canal vocal en raison de l'inactivité.")

# Fonction pour réinitialiser le timer
async def reset_inactivity_timer(ctx):
    global inactivity_timer
    if inactivity_timer:
        inactivity_timer.cancel()  # Annuler l'ancienne minuterie

    # Créer une nouvelle minuterie d'inactivité
    inactivity_timer = asyncio.get_event_loop().call_later(inactivity_timeout, lambda: asyncio.create_task(check_inactivity(ctx)))

# Exemple d'utilisation dans la commande `play`
@bot.command()
async def play(ctx, *, query):
    """Joue une musique ou l'ajoute à la file d'attente."""
    global music_queue

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'search': query,
            'default_search': 'ytsearch',
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Recherche de la musique : {query}")
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']
            title = info.get('title', 'Musique inconnue')

        # Vérifie si l'utilisateur est dans un salon vocal
        if not ctx.author.voice:
            await ctx.send("❌ Tu dois être dans un canal vocal pour utiliser cette commande.")
            return

        voice_channel = ctx.author.voice.channel

        # Vérifie si le bot est déjà connecté à un salon vocal
        if not ctx.voice_client:
            await voice_channel.connect()
        elif ctx.voice_client.channel != voice_channel:
            await ctx.voice_client.move_to(voice_channel)

        # Ajoute la musique à la file d'attente
        music_queue.append((url, title))
        await ctx.send(f"🎵 **{title}** a été ajouté à la file d'attente.")

        # Si aucune musique n'est en cours de lecture, démarre la lecture
        if not ctx.voice_client.is_playing():
            # Utilise PCMVolumeTransformer pour ajuster le volume à 50%
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url), volume=0.3)
            ctx.voice_client.play(source, after=lambda e: print('Musique terminée', e))

    except yt_dlp.utils.DownloadError as e:
        await ctx.send(f"❌ Impossible de trouver la vidéo : {e}")
    except Exception as e:
        await ctx.send(f"❌ Une erreur est survenue : {e}")
@bot.command()
async def pause(ctx):
    """Met en pause la lecture actuelle."""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸ Lecture mise en pause.")
    else:
        await ctx.send("❌ Aucune musique n'est en cours de lecture.")
@bot.command()
async def resume(ctx):
    """Reprend la lecture mise en pause."""
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Lecture reprise.")
    else:
        await ctx.send("❌ Aucune musique n'est mise en pause.")
@bot.command()
async def queue(ctx):
    """Affiche la file d'attente."""
    if music_queue:
        queue_list = "\n".join([f"{i + 1}. {title}" for i, (_, title) in enumerate(music_queue)])
        await ctx.send(f"📜 **File d'attente :**\n{queue_list}")
    else:
        await ctx.send("❌ La file d'attente est vide.")

@bot.command()
async def stop(ctx):
    """Arrête la lecture actuelle et déconnecte le bot du canal vocal."""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏹ Lecture arrêtée.")
    elif ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Déconnecté du canal vocal.")
    else:
        await ctx.send("❌ Je ne suis pas dans un canal vocal.")
# Événement pour écouter les nouveaux messages
@bot.event
async def on_message(message):
    global listening, listening_harem_name
    if listening_harem_name and message.author.name == 'Mudae':
        if message.embeds:
            embed = message.embeds[0]
            embed_dict = embed.to_dict()

            author_name = embed_dict.get('author', {}).get('name', '')
            image_url = embed_dict.get('image', {}).get('url', '')
            description = embed_dict.get('description', '')

            match = re.search(r'\*\*(\d+)\*\*', description)
            kakera = match.group(1) if match else None

            sex_match = re.search(r'<:([a-zA-Z]+):', description)
            sex = sex_match.group(1) if sex_match else 'Other'
            if sex == 'female':
                sex = 'Waifu'
            elif sex == 'male':
                sex = 'Husbando'

            description_part = description.split('<')[0].strip()
            user_id = list(user_messages.keys())[-1]
            user = await bot.fetch_user(user_id)

            harem_dict["user"] = user.name
            harem_dict["characters"].append({
                "author_name": author_name,
                "image_url": image_url,
                "description_part": description_part,
                "kakera": kakera,
                "sex": sex
            })

            # Sauvegarde après chaque ajout
            save_state(harem_dict, len(harem_dict["characters"]), user.name)

    await bot.process_commands(message)


# Événement pour écouter les modifications de messages
@bot.event
async def on_message_edit(before, after):
    global listening_harem_name, harem_dict

    if listening_harem_name and after.author.name == 'Mudae':
        user_id = list(user_messages.keys())[-1]
        user = await bot.fetch_user(user_id)

        if after.embeds:
            new_embed = after.embeds[0]
            embed_dict = new_embed.to_dict()
            if new_embed.footer and new_embed.footer.text:
                footer_text = new_embed.footer.text
                print(footer_text)
                # Trouver l'index du caractère '/'
                index_slash = footer_text.find("/")
                if index_slash != -1:
                    # Extraire la sous-chaîne après le '/'
                    sous_chaine = footer_text[index_slash + 1:].strip()
                    # Convertir la sous-chaîne en entier
                    nbr_page = int(sous_chaine)
            author_name = embed_dict.get('author', {}).get('name', '')
            image_url = embed_dict.get('image', {}).get('url', '')
            description = embed_dict.get('description', '')

            match = re.search(r'\*\*(\d+)\*\*', description)
            kakera = match.group(1) if match else None

            sex_match = re.search(r'<:([a-zA-Z]+):', description)
            sex = sex_match.group(1) if sex_match else 'Other'
            if sex == 'female':
                sex = 'Waifu'
            elif sex == 'male':
                sex = 'Husbando'

            description_part = description.split('<')[0].strip()

            harem_dict["characters"].append({
                "author_name": author_name,
                "image_url": image_url,
                "description_part": description_part,
                "kakera": kakera,
                "sex": sex
            })

            save_state(harem_dict, len(harem_dict["characters"]), user.name)
            if harem_dict["page_number"] == nbr_page:
                listening_harem_name = False
                await after.channel.send('Fin de la capture du harem.')
@bot.event
async def on_voice_state_update(member, before, after):
    # Vérifie si c'est le bot qui quitte le salon vocal
    if member == bot.user and before.channel is not None and after.channel is None:
        # Le bot a quitté un salon vocal
        global music_queue
        music_queue = []  # Vide la file d'attente
        print("Le bot a quitté le salon vocal, la file d'attente a été réinitialisée.")
@bot.command()
async def pclear(ctx):
    """Vide la playlist."""
    global music_queue
    music_queue = []
    await ctx.send("✅ La playlist a été vidée.")

# Événement `on_ready`
@bot.event
async def on_ready():
    global reboot_channel_id
    message = "✅ Freyja est prête ! 🎤✨"

    # Envoie dans le salon de logs
    if log_guild_id and log_channel_id:
        guild = bot.get_guild(log_guild_id)  # Récupère la guilde
        if guild:
            log_channel = guild.get_channel(log_channel_id)  # Récupère le salon dans cette guilde
            if log_channel:
                # On ajoute l'heure de redémarrage dans le message de logs
                # On ajoute l'heure de redémarrage dans le message de logs
                reboot_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                log_message = f"🔧 Redémarrage effectué le {reboot_time}."
                await log_channel.send(log_message)
    # Envoie dans le salon du reboot (si défini)
    if reboot_channel_id:
        reboot_channel = bot.get_channel(reboot_channel_id)
        if reboot_channel:
            await reboot_channel.send(message)
            file_path = "reboot_channel_info.json"  # Le chemin vers ton fichier JSON
            clear_json_file(file_path)
            reboot_channel_id = None  # Reset après usage


# Lancer le bot avec le token
bot.run(DISCORD_TOKEN)