import json
from pushToGoogleSheet import update_google_sheet
def load_harem_dict(harem_name):
    try:
        with open(f"harem_data{harem_name}.json", "r") as file:
            harem_dict = json.load(file)
            return harem_dict
    except FileNotFoundError:
        raise FileNotFoundError(f"Le fichier 'harem_data{harem_name}.json' n'a pas été trouvé.")
    except json.JSONDecodeError:
        raise json.JSONDecodeError(f"Erreur lors de la lecture du fichier JSON 'harem_data{harem_name}.json'.", doc="", pos=0)
    except Exception as e:
        raise Exception(f"Une erreur inattendue s'est produite : {e}")

def get_waifu_list(harem_name):
    harem_dict = load_harem_dict(harem_name)
    return harem_dict.get("waifu", [])
def setToGoogleSheet(harem_name):
    # Charger le fichier de configuration
    with open('config.json') as config_file:
        config = json.load(config_file)
    tbl = get_waifu_list(harem_name)
    cleaned_tbl = [waifu.replace("_", "").replace("\u200b", "") for waifu in tbl if waifu.strip()]
    cleaned_tbl = [waifu for waifu in cleaned_tbl if waifu]
    if harem_name == "Macross":
        harem_name = config['HAREM_NAXOS']
    elif harem_name == "La Foret Interdit D'Ivern":
        harem_name = config['HAREM_XIORATUS']
    update_google_sheet(cleaned_tbl, harem_name)
    print(f"Les données du harem '{harem_name}' ont été envoyées avec succès à Google Sheets.")
# Example usage
