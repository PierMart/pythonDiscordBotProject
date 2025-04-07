import os
from datetime import datetime


def main():
    print("Le script fonctionne correctement sur la Raspberry Pi !")

    # Créer un fichier de test
    filename = "test_raspberry_output.txt"
    with open(filename, "w") as f:
        f.write(f"Script exécuté avec succès le {datetime.now()}\n")

    print(f"Fichier '{filename}' créé avec succès.")


if __name__ == "__main__":
    main()