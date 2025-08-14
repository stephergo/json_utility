import pandas as pd
import os
import sys
from pathlib import Path

# Ajoute la racine du projet au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_sync import DataSync

# --- Configuration ---
DB_PATH = "data/sales.duckdb"
TABLE_NAME = "ventes"

def run_example():
    """Démontre l'ajout de données à une table existante."""
    print("--- Exemple 2: Ajout de données à une table existante ---")

    # --- 1. Création et synchronisation des données initiales ---

    initial_data = {
        'vente_id': [1, 2],
        'produit': ['Produit A', 'Produit B'],
        'quantite': [10, 5]
    }
    df_initial = pd.DataFrame(initial_data)

    ds = DataSync(db_path=DB_PATH)
    ds.df = df_initial

    print("\nSynchronisation des données initiales (if_exists='replace'):")
    print(df_initial)
    ds.sync_to_db(TABLE_NAME, if_exists='replace')

    # Vérification du contenu de la table
    print("\nContenu de la table après la première synchronisation :")
    print(ds.query(f"SELECT * FROM {TABLE_NAME}"))

    # --- 2. Création de nouvelles données et ajout à la table ---

    new_data = {
        'vente_id': [3, 4],
        'produit': ['Produit C', 'Produit A'],
        'quantite': [7, 12]
    }
    df_new = pd.DataFrame(new_data)

    # On assigne le nouveau DataFrame à l'instance
    ds.df = df_new

    print("\nAjout de nouvelles données (if_exists='append'):")
    print(df_new)
    ds.sync_to_db(TABLE_NAME, if_exists='append')

    # --- 3. Vérification du contenu final de la table ---

    print("\nContenu final de la table après l'ajout :")
    final_df = ds.query(f"SELECT * FROM {TABLE_NAME}")
    print(final_df)

    assert len(final_df) == 4, "La table devrait contenir 4 lignes."
    print("\n-> Vérification réussie: Les données ont bien été ajoutées.")

def cleanup():
    """Nettoie les fichiers générés."""
    print("\n--- Nettoyage ---")
    wal_file = f"{DB_PATH}.wal"
    for path in [DB_PATH, wal_file]:
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
