import gspread
import json
from google.oauth2.service_account import Credentials
import asyncio
from gspread.exceptions import APIError

async def update_google_sheet(data, harem_owner_name):
    # Définir les autorisations nécessaires
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

    # Charger les identifiants à partir du fichier JSON
    creds = Credentials.from_service_account_file("API_KEY/apiKeyGoogle.json", scopes=scope)

    # Connexion à Google Sheets
    client = gspread.authorize(creds)

    # Ouvrir le spreadsheet "Need Mudae"
    spreadsheet = client.open("Need Mudae")
    # Sélectionner le worksheet spécifié par harem_owner_name
    worksheet = spreadsheet.worksheet(harem_owner_name)

    # Définir la ligne de départ pour ajouter des données
    start_row = 3

    # Préparer les données pour une mise à jour par lot
    updates = []
    for i, value in enumerate(data['characters']):
        row = start_row + i
        updates.append({'range': f"B{row}", 'values': [[value['sex']+str(i+1)]]})
        updates.append({'range': f"C{row}", 'values': [[value['author_name']]]})
        updates.append({'range': f"D{row}", 'values': [[f'=IMAGE("{value["image_url"]}")']]})
        updates.append({'range': f"E{row}", 'values': [[value['description_part']]]})
        updates.append({'range': f"F{row}", 'values': [[value['kakera']]]})

    # Envoyer les requêtes par lot
    try:
        print(f"Envoi des données pour {len(data['characters'])} personnages...")
        worksheet.batch_update(updates, value_input_option='USER_ENTERED')
        print("Données envoyées avec succès !")
    except APIError as e:
        print(f"Erreur API : {e}")
        await retry_backoff(e)

async def retry_backoff(e):
    """Gestion du backoff exponentiel en cas d'erreur API."""
    delay = 1
    max_delay = 64
    while delay <= max_delay:
        print(f"Erreur API rencontrée, attente de {delay} seconde(s)...")
        await asyncio.sleep(delay)
        delay *= 2
        if delay > max_delay:
            print("Attente maximale atteinte, réessayez plus tard.")
            break
