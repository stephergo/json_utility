import os
import sys
from pathlib import Path

# Ajoute la racine du projet au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_sync import DataSync, DataSyncError

# --- Configuration ---
DB_PATH = "data/error_test.duckdb"

def run_example():
    """Démontre comment gérer les exceptions DataSyncError."""
    print("--- Exemple 3: Gestion des erreurs ---")

    ds = DataSync(db_path=DB_PATH)

    # --- 1. Tenter de charger un fichier inexistant ---

    non_existent_file = "data/fichier_qui_n_existe_pas.json"
    print(f"\nTentative de chargement du fichier inexistant : {non_existent_file}")

    try:
        ds.load_from_json(non_existent_file)
    except DataSyncError as e:
        print("\n-> Erreur attendue capturée !")
        print(f"   Message d'erreur : {e}")
        # On vérifie que le message d'erreur est bien celui attendu
        assert "Fichier JSON non trouvé" in str(e)

    # --- 2. Tenter une requête sur une table inexistante ---

    non_existent_table = "table_inexistante"
    print(f"\n\nTentative de chargement depuis une table inexistante : '{non_existent_table}'")

    try:
        ds.load_from_db(non_existent_table)
    except DataSyncError as e:
        print("\n-> Erreur attendue capturée !")
        print(f"   Message d'erreur : {e}")
        # Le message d'erreur exact peut varier selon le moteur de BDD,
        # on vérifie juste qu'il contient le nom de la table.
        assert non_existent_table in str(e)

    print("\n\nL'exemple de gestion des erreurs s'est terminé avec succès.")

def cleanup():
    """Nettoie les fichiers générés."""
    print("\n--- Nettoyage ---")
    # Le fichier de BDD n'est pas créé dans cet exemple,
    # mais on garde le nettoyage par sécurité.
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
    # Note: Ce script doit s'exécuter sans erreur finale,
    # car les exceptions sont prévues et capturées.
    try:
        run_example()
    finally:
        cleanup()
