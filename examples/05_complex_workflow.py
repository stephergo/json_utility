import pandas as pd
import os
import sys
from pathlib import Path

# Ajoute la racine du projet au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_sync import DataSync

# --- Configuration ---
DB_PATH = "data/workflow_db.duckdb"
INPUT_EXCEL_PATH = "data/raw_data.xlsx"
OUTPUT_JSON_PATH = "data/processed_data.json"
TABLE_NAME = "ventes_nettoyees"

def setup_initial_file():
    """Crée un fichier Excel de test pour servir d'entrée."""
    print("--- Préparation: Création du fichier Excel initial ---")
    raw_data = {
        'produit': ['   Pomme  ', '  Banane', 'orange', 'FRAISE'],
        'prix_unitaire': [1.2, 0.8, 1.0, 2.5],
        'quantite': [100, 150, 0, 80] # 'orange' a une quantité de 0
    }
    df = pd.DataFrame(raw_data)
    # Crée le répertoire 'data' s'il n'existe pas
    os.makedirs("data", exist_ok=True)
    df.to_excel(INPUT_EXCEL_PATH, index=False)
    print(f"-> Fichier initial créé : {INPUT_EXCEL_PATH}")

def run_example():
    """Démontre un flux de travail plus complexe."""
    print("\n--- Exemple 5: Flux de travail complexe ---")

    # --- 1. Chargement des données brutes depuis Excel ---
    ds = DataSync(db_path=DB_PATH)
    ds.load_from_excel(INPUT_EXCEL_PATH)
    print("\n1. Données chargées depuis Excel :")
    print(ds.get_df())

    # --- 2. Manipulation et nettoyage des données avec Pandas ---
    print("\n2. Nettoyage et transformation des données...")

    # Récupérer le DataFrame
    df = ds.get_df()

    # a. Nettoyer les noms de produits (espaces, casse)
    df['produit'] = df['produit'].str.strip().str.capitalize()

    # b. Calculer le total et ajouter une nouvelle colonne
    df['total_vente'] = df['prix_unitaire'] * df['quantite']

    # c. Filtrer les produits qui ne sont pas en stock
    df_processed = df[df['quantite'] > 0].copy()

    print("   -> Données transformées :")
    print(df_processed)

    # Mettre à jour le DataFrame dans l'objet DataSync
    ds.df = df_processed

    # --- 3. Synchronisation des données nettoyées avec la BDD ---
    print(f"\n3. Synchronisation des données nettoyées vers la table '{TABLE_NAME}'...")
    ds.sync_to_db(TABLE_NAME)
    print("   -> Synchronisation réussie.")

    # --- 4. Sauvegarde du résultat final en JSON ---
    print(f"\n4. Sauvegarde des données finales dans {OUTPUT_JSON_PATH}...")
    ds.save_to_json(OUTPUT_JSON_PATH)
    print("   -> Sauvegarde réussie.")

    # --- 5. Vérification finale ---
    print("\n5. Vérification dans la base de données...")
    result_df = ds.query(f"SELECT COUNT(*) as count, SUM(total_vente) as total_sum FROM {TABLE_NAME}")
    print("   Résultat de la vérification :")
    print(result_df)
    assert result_df['count'][0] == 3
    # 1.2*100 + 0.8*150 + 2.5*80 = 120 + 120 + 200 = 440
    assert result_df['total_sum'][0] == 440.0

    print("\n-> Flux de travail complexe terminé avec succès !")

def cleanup():
    """Nettoie tous les fichiers générés."""
    print("\n--- Nettoyage ---")
    wal_file = f"{DB_PATH}.wal"
    for path in [DB_PATH, wal_file, INPUT_EXCEL_PATH, OUTPUT_JSON_PATH]:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"-> Fichier supprimé : {path}")
            except OSError as e:
                print(f"Erreur lors de la suppression du fichier {path}: {e}")

    try:
        if os.path.exists("data") and os.listdir("data") == []:
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
