import gspread
import json
from google.oauth2.service_account import Credentials
import time
from gspread.exceptions import APIError

def update_google_sheet(data, harem_owner_name):
    # Définit les permissions nécessaires
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

    # Charge les identifiants depuis le fichier JSON
    creds = Credentials.from_service_account_file("API_KEY/testapi-441816-3660e34de71c.json", scopes=scope)

    # Se connecte à Google Sheets
    client = gspread.authorize(creds)
    # Charger le fichier de configuration
    with open('config.json') as config_file:
        config = json.load(config_file)

    # Ouvre le classeur "Need Mudae"
    spreadsheet = client.open("Need Mudae")
    # Sélectionne la feuille spécifiée par harem_owner_name
    worksheet = spreadsheet.worksheet(harem_owner_name)

    # Définit la ligne de départ pour ajouter les données
    start_row = 3

    # Ajoute chaque valeur de data dans la colonne C
    for i, value in enumerate(data):
        try:
            worksheet.update_cell(start_row + i, 3, value)  # Colonne C correspond à l'index 3
            time.sleep(1)  # Ajoute une temporisation de 1 seconde entre chaque requête
        except APIError as e:
            if e.response.status_code == 429:
                print("Quota dépassé, attente de 60 secondes avant de réessayer...")
                time.sleep(60)  # Attend 60 secondes avant de réessayer
                worksheet.update_cell(start_row + i, 3, value)  # Réessaye la requête
            else:
                raise e

    print("Données envoyées avec succès !")