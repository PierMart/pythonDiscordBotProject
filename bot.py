import json
from xml.etree.ElementTree import tostring

import discord
from discord.ext import commands
from pushDocs import setToGoogleSheet

# Charger le fichier de configuration
with open('config.json') as config_file:
    config = json.load(config_file)

# Accéder à la clé API
DISCORD_TOKEN = config['DISCORD_TOKEN']

# Crée une instance des intents
intents = discord.Intents.default()
intents.message_content = True  # Nécessaire pour lire le contenu des messages
intents.messages = True  # Nécessaire pour lire les messages

# Crée une instance du bot avec le préfixe de commande '!' et les intents spécifiés
bot = commands.Bot(command_prefix='!', intents=intents)

# Variable pour suivre si l'écoute est activée
listening = False
listening_harem_name = False
# Dictionnaire pour stocker les messages originaux des utilisateurs
user_messages = {}
first_waifu = {}

# Dictionnaire pour stocker les messages originaux de Mudae
mudae_original_messages = {}

# Dictionnaire pour compter les modifications de chaque message
message_edit_count = {}

# Liste pour stocker les messages de Mudae
mudae_messages = []

# nbr de page mm
nbr_page = 0

# Dictionnaire pour stocker les données du harem
harem_dict = {
  "user": "",
  "characters": []
}



def save_harem_dict(harem_dict, name):
    with open('harem_data_' + name + '.json', 'w') as file:
        json.dump(harem_dict, file)


# Commande pour activer l'écoute des messages de Mudae
@bot.command()
async def ls(ctx):
    global listening
    listening = True
    user_messages[ctx.author.id] = None
    await ctx.send('Écoute des messages de Mudae activée.')


@bot.command()
async def hello(ctx):
    await ctx.send(f'Bonjour {ctx.author.mention} !')


@bot.command()
async def set(ctx):
    global listening_harem_name
    listening_harem_name = True
    user_messages[ctx.author.id] = None
    await ctx.send('Faites la commande $mm pour définir le nom du harem.')


@bot.command()
async def nls(ctx):
    global listening
    listening = False
    await ctx.send('Écoute des messages de Mudae désactivée.')


@bot.command()
async def ph(ctx, harem_name: str):
    try:
        if harem_name == "Naxos":
            harem_owner_name = "Macross"
        elif harem_name == "Xioratus":
            harem_owner_name = "La Foret Interdit D'Ivern"
        setToGoogleSheet(harem_owner_name)
        await ctx.send(f'Les données du harem "{harem_owner_name}" ont été envoyées avec succès à Google Sheets.')
    except FileNotFoundError:
        await ctx.send(f'Le fichier harem_data{harem_name}.json n\'existe pas.')
    except json.JSONDecodeError:
        await ctx.send(f'Erreur lors de la lecture du fichier JSON harem_data{harem_name}.json.')
    except Exception as e:
        await ctx.send(f'Une erreur inattendue s\'est produite : {e}')

@bot.command()
async def push(ctx):
    try:
        print(ctx.author.name)
        harem_name=ctx.author.name
        await setToGoogleSheet(harem_name)
        await ctx.send(f'Les données du harem "{ctx.author.mention}" ont été envoyées avec succès à Google Sheets.')
    except FileNotFoundError:
        await ctx.send(f'Le fichier harem_data{harem_name}.json n\'existe pas.')
    except json.JSONDecodeError:
        await ctx.send(f'Erreur lors de la lecture du fichier JSON harem_data{harem_name}.json.')
    except Exception as e:
        await ctx.send(f'Une erreur inattendue s\'est produite : {e}')


@bot.event
async def on_message(message):
    global listening, listening_harem_name

    # Vérifie si l'écoute est activée pour le harem
    if listening_harem_name:
        if message.author.name == 'Mudae':
            if message.embeds:
                embed = message.embeds[0]
                embed_dict = embed.to_dict()
                # Extract author name
                author_name = embed_dict.get('author', {}).get('name', '')
                image_url = embed_dict.get('image', {}).get('url', '')
                description = embed_dict.get('description', '')
                description_part = description.split('<')[0].strip()

                user_id = list(user_messages.keys())[-1]
                user = await bot.fetch_user(user_id)
                harem_dict["user"] = user.name
                harem_dict["characters"].append({
                    "author_name": author_name,
                    "image_url": image_url,
                    "description_part": description_part
                })
                first_waifu[message.id] = author_name
                message_edit_count[message.id] = 0  # Initialiser le compteur de modifications
                await message.channel.send(
                    f'Le nom du harem  a été enregistré pour l\'utilisateur {user_id}.')
    # Vérifie si l'écoute est activée pour les messages de Mudae
    if listening:
        if message.author.name == 'Mudae':
            if message.embeds:
                embed = message.embeds[0]
                embed_description = embed.description
                names = embed_description.split('\n')
                for name in names:
                    if name not in mudae_messages:
                        mudae_messages.append(name)
                mudae_original_messages[message.id] = embed_description
                message_edit_count[message.id] = 0  # Initialiser le compteur de modifications
    # Appelle le gestionnaire de commandes pour traiter les commandes
    await bot.process_commands(message)


# Événement pour détecter les modifications de messages
@bot.event
async def on_message_edit(before, after):
    global listening, listening_harem_name,harem_dict
    if listening:
        if after.author.name == 'Mudae':
            original_embed_description = []
            original_embed_description = mudae_original_messages.get(after.id)
            if after.embeds:
                new_embed = after.embeds[0]
                harem_name = new_embed.author.name
                new_embed_description = after.embeds[0].description
                if original_embed_description and original_embed_description != new_embed_description:
                    new_names = new_embed_description.split('\n')
                    for name in new_names:
                        if name not in mudae_messages:
                            mudae_messages.append(name)
                    mudae_original_messages[after.id] = new_embed_description
                    message_edit_count[after.id] += 1  # Incrémenter le compteur de modifications
                    if new_embed.footer and new_embed.footer.text:
                        footer_text = new_embed.footer.text
                        print(footer_text)
                        # Trouver l'index du caractère '/'
                        index_slash = footer_text.find("/")
                        if index_slash != -1:
                            # Extraire la sous-chaîne après le '/
                            sous_chaine = footer_text[index_slash + 1:].strip()
                            # Convertir la sous-chaîne en entier
                            nbr_page = int(sous_chaine) - 1
                            print(nbr_page)
                        else:
                            print("Le caractère '/' n'a pas été trouvé dans le texte du footer.")

                    print(f'Nombre de modifications du message {nbr_page} : {message_edit_count[after.id]}')
                    if message_edit_count[after.id] == nbr_page:
                        # mettre fin à tout les listening
                        harem_dict = {
                            "harem": harem_name,
                            "waifu": mudae_messages
                        }
                        listening = False
                        await after.channel.send('Écoute des messages de Mudae désactivée.')
                        save_harem_dict(harem_dict, harem_name)  # Sauvegarder les données dans un fichier JSON
                        harem_dict = {
                            "harem": "",
                            "waifu": []
                        }
                        mudae_messages.clear()  # Vider la liste mudae_messages
    elif listening_harem_name:
        if after.author.name == 'Mudae':
            user_id = list(user_messages.keys())[-1]
            user = await bot.fetch_user(user_id)
            original_embed_description = []
            original_embed_description = first_waifu.get(after.id)
            if after.embeds:
                new_embed = after.embeds[0]
                harem_name = user.name
                new_embed_description = after.embeds[0].author.name
                if original_embed_description and original_embed_description != new_embed_description:
                    embed_dict = new_embed.to_dict()
                    # Extract author name
                    author_name = embed_dict.get('author', {}).get('name', '')
                    image_url = embed_dict.get('image', {}).get('url', '')
                    description = embed_dict.get('description', '')
                    description_part = description.split('<')[0].strip()
                    harem_dict["characters"].append({
                        "author_name": author_name,
                        "image_url": image_url,
                        "description_part": description_part
                    })
                    message_edit_count[after.id] += 1  # Incrémenter le compteur de modifications
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
                            print(nbr_page)
                        else:
                            print("Le caractère '/' n'a pas été trouvé dans le texte du footer.")

                    print(f'Nombre de modifications du message {nbr_page} : {message_edit_count[after.id]}')
                    if message_edit_count[after.id] == nbr_page:
                        # mettre fin à tout les listening
                        listening_harem_name = False
                        await after.channel.send('Écoute des messages de Mudae désactivée.')
                        save_harem_dict(harem_dict, harem_name)  # Sauvegarder les données dans un fichier JSON
                        harem_dict = {
                            "user": "",
                            "characters": []
                        }
                        mudae_messages.clear()  # Vider la liste mudae_messages


@bot.event
async def on_ready():
    # Remplacez 'CHANNEL_ID' par l'ID du canal où vous voulez envoyer la commande
    channel_id = 1306612366980550756  # Remplacez par l'ID de votre canal
    channel = bot.get_channel(channel_id)
    if channel:
        print(f'We have logged in as {bot.user} in channel {channel}.')
    else:
        print(f'Channel with ID {channel_id} not found.')


# Lance le bot avec le DISCORD_TOKEN
bot.run(DISCORD_TOKEN)
