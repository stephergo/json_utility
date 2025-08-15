import pandas as pd
import os
import sys
from pathlib import Path

# Ajoute la racine du projet au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_sync import DataSync, DataSyncError
# Importer le schéma que nous avons défini
from src.data_sync.schemas import PersonSchema

# --- Configuration ---
INPUT_JSON_PATH = "data/personnes.json"

def setup_initial_file():
    """Crée un fichier JSON de test avec des en-têtes en français et des données invalides."""
    print("--- Préparation: Création du fichier JSON initial ---")

    raw_data = [
        {'Prénom': 'Alice', 'Nom': 'Dubois', 'Courriel': 'alice@example.com', 'Date de Naissance': '1990-01-15'},
        {'Prénom': 'Bob', 'Nom': 'Martin', 'Courriel': 'bob@invalid-email', 'Date de Naissance': '1985-05-20'},
        {'Prénom': '', 'Nom': 'Personne Vide', 'Courriel': 'vide@example.com', 'Date de Naissance': '2000-10-10'}
    ]

    os.makedirs("data", exist_ok=True)
    with open(INPUT_JSON_PATH, 'w', encoding='utf-8') as f:
        import json
        json.dump(raw_data, f, ensure_ascii=False, indent=4)

    print(f"-> Fichier initial créé : {INPUT_JSON_PATH}")

def run_example():
    """Démontre le mappage de colonnes et la validation de schéma."""
    print("\n--- Exemple 6: Mappage de colonnes et validation de schéma ---")

    # --- 1. Définir le mappage des colonnes ---
    column_mapping = {
        'Prénom': 'givenName',
        'Nom': 'familyName',
        'Courriel': 'email',
        'Date de Naissance': 'birthDate'
    }
    print("\n1. Dictionnaire de mappage défini :")
    print(column_mapping)

    # --- 2. Charger les données en appliquant le mappage ---
    ds = DataSync(db_path="data/validation_db.duckdb") # La BDD n'est pas utilisée ici, mais requise par __init__
    ds.load_from_json(INPUT_JSON_PATH, column_mapping=column_mapping)

    # Le JSON ne gère pas les dates, il faut donc les convertir manuellement
    ds.df['birthDate'] = pd.to_datetime(ds.df['birthDate'])

    print("\n2. DataFrame après chargement, mappage et conversion de date :")
    print(ds.get_df().to_string())

    # --- 3. Tenter la validation (doit échouer) ---
    print("\n3. Tentative de validation sur les données brutes (doit échouer)...")
    try:
        ds.validate(PersonSchema)
    except DataSyncError as e:
        print("\n-> Erreur de validation attendue capturée !")
        print("   Détails de l'erreur :")
        # On affiche une version courte de l'erreur pour la lisibilité
        print(str(e).splitlines()[0])
        assert "La validation des données a échoué" in str(e)

    # --- 4. Nettoyer les données et valider à nouveau (doit réussir) ---
    print("\n4. Nettoyage des données et nouvelle validation...")

    # Correction des données
    df = ds.get_df()
    # On enlève la ligne avec un prénom vide
    df = df[df['givenName'] != ''].copy()
    # On corrige l'e-mail de Bob
    df.loc[df['familyName'] == 'Martin', 'email'] = 'bob.martin@example.com'
    ds.df = df

    print("   -> DataFrame après nettoyage :")
    print(ds.get_df().to_string())

    ds.validate(PersonSchema)
    print("\n-> Validation réussie sur les données nettoyées !")

def cleanup():
    """Nettoie tous les fichiers générés."""
    print("\n--- Nettoyage ---")
    db_path = "data/validation_db.duckdb"
    for path in [INPUT_JSON_PATH, db_path, f"{db_path}.wal"]:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"-> Fichier supprimé : {path}")
            except OSError as e:
                print(f"Erreur lors de la suppression du fichier {path}: {e}")
    try:
        if os.path.exists("data") and not os.listdir("data"):
            os.rmdir("data")
            print("-> Répertoire 'data' supprimé.")
    except OSError:
        pass

if __name__ == "__main__":
    try:
        setup_initial_file()
        run_example()
    finally:
        cleanup()
