import json
import re
import discord
from discord.ext import commands
from pushDocs import setToGoogleSheet

# Charger le fichier de configuration
with open('config.json') as config_file:
    config = json.load(config_file)

DISCORD_TOKEN = config['DISCORD_TOKEN']

# Initialisation du bot avec les intents
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Variables globales
listening = False
listening_harem_name = False

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



# Événement `on_ready`
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


# Lancer le bot avec le token
bot.run(DISCORD_TOKEN)