import json
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

# Dictionnaire pour stocker les messages originaux de Mudae
mudae_original_messages = {}

# Dictionnaire pour compter les modifications de chaque message
message_edit_count = {}

# Liste pour stocker les messages de Mudae
mudae_messages = []

#nbr de page mm
nbr_page = 0

# Dictionnaire pour stocker les données du harem
harem_dict = {
    "harem": "",
    "waifu": []
}

def save_harem_dict(harem_dict,name):
    with open('harem_data'+name+'.json', 'w') as file:
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




@bot.event
async def on_message(message):
    global listening_harem_name
    # Vérifie si l'écoute est activée
    if listening_harem_name:
        # Vérifie si le message provient de Mudae
        if message.author.name == 'Mudae':
            # Copie et renvoie le message
            if message.embeds:
                embed = message.embeds[0]
                embed_harem_name = embed.author.name
                user_id = list(user_messages.keys())[-1]
                harem_dict["harem"] = embed_harem_name
                listening_harem_name = False
                await message.channel.send(f'Le nom du harem "{embed_harem_name}" a été enregistré pour l\'utilisateur {user_id}.')


    # Appelle le gestionnaire de commandes pour traiter les commandes
    await bot.process_commands(message)

# Événement pour écouter les messages
@bot.event
async def on_message(message):
    global listening
    # Vérifie si l'écoute est activée
    if listening:
        # Vérifie si le message provient de Mudae
        if message.author.name == 'Mudae':
            # Copie et renvoie le message
            if message.content:
                await message.channel.send(f'Message de Mudae : {message.content}')
                mudae_messages.append(message.content)

            elif message.embeds:
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
    global listening
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
                            # Extraire la sous-chaîne après le '/'
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