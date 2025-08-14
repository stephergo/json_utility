import pandas as pd
import os
import sys
from pathlib import Path

# Ajoute la racine du projet au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_sync import DataSync

# --- Configuration ---
DB_PATH = "data/inventory.duckdb"

def run_example():
    """Démontre la gestion de plusieurs tables dans une seule base de données."""
    print("--- Exemple 1: Gestion de plusieurs tables ---")

    # --- 1. Création des données pour deux tables ---

    # Données des produits
    products_data = {
        'produit_id': [101, 102, 103],
        'nom_produit': ['Stylo', 'Cahier', 'Gomme'],
        'fournisseur_id': [1, 2, 1]
    }
    df_products = pd.DataFrame(products_data)
    print("\nDataFrame des produits :")
    print(df_products)

    # Données des fournisseurs
    suppliers_data = {
        'fournisseur_id': [1, 2],
        'nom_fournisseur': ['Fournitout', 'Papeterie ABC']
    }
    df_suppliers = pd.DataFrame(suppliers_data)
    print("\nDataFrame des fournisseurs :")
    print(df_suppliers)

    # --- 2. Initialisation et synchronisation ---

    ds = DataSync(db_path=DB_PATH)

    # Synchroniser la première table
    ds.df = df_products
    ds.sync_to_db('produits')
    print("\n-> Table 'produits' synchronisée.")

    # Pour synchroniser la deuxième table, on change le DataFrame de l'instance
    ds.df = df_suppliers
    ds.sync_to_db('fournisseurs')
    print("-> Table 'fournisseurs' synchronisée.")

    # --- 3. Interrogation des données avec une jointure ---

    print("\n--- Requête de jointure pour lier produits et fournisseurs ---")
    query = """
    SELECT
        p.nom_produit,
        f.nom_fournisseur
    FROM produits p
    JOIN fournisseurs f ON p.fournisseur_id = f.fournisseur_id
    ORDER BY p.nom_produit
    """

    joined_df = ds.query(query)

    print("Résultat de la requête de jointure :")
    print(joined_df)

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

    # On vérifie si le répertoire data est vide avant de le supprimer
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
