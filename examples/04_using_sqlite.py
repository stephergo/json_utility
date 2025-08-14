import pandas as pd
import os
import sys
from pathlib import Path

# Ajoute la racine du projet au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_sync import DataSync

# --- Configuration ---
DB_PATH = "data/database.sqlite"
TABLE_NAME = "utilisateurs"

def run_example():
    """Démontre l'utilisation de la bibliothèque avec une base de données SQLite."""
    print("--- Exemple 4: Utilisation avec SQLite ---")

    # --- 1. Création des données ---

    data = {
        'id': [1, 2, 3],
        'nom': ['Alice', 'Bob', 'Charlie'],
        'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com']
    }
    df = pd.DataFrame(data)
    print("\nDataFrame à synchroniser :")
    print(df)

    # --- 2. Initialisation avec db_type='sqlite' et synchronisation ---

    print(f"\nUtilisation de la base de données SQLite : {DB_PATH}")
    ds = DataSync(db_path=DB_PATH, db_type='sqlite')

    ds.df = df
    ds.sync_to_db(TABLE_NAME)
    print(f"-> Données synchronisées avec la table '{TABLE_NAME}'.")

    # --- 3. Rechargement et vérification ---

    print("\nRechargement des données depuis la base de données SQLite...")
    # On crée une nouvelle instance pour s'assurer de bien lire depuis le fichier
    ds_loader = DataSync(db_path=DB_PATH, db_type='sqlite')
    ds_loader.load_from_db(TABLE_NAME)

    loaded_df = ds_loader.get_df()
    print("DataFrame rechargé :")
    print(loaded_df)

    pd.testing.assert_frame_equal(df, loaded_df)
    print("\n-> Vérification réussie : Les données rechargées sont identiques.")

def cleanup():
    """Nettoie les fichiers générés."""
    print("\n--- Nettoyage ---")
    # SQLite peut créer des fichiers de journalisation
    journal_file = f"{DB_PATH}-journal"
    for path in [DB_PATH, journal_file]:
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
        run_example()
    finally:
        cleanup()
