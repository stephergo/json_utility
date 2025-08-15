import pandas as pd
import json
import pandera as pa
from pathlib import Path
from sqlalchemy import create_engine, text
from .exceptions import DataSyncError

class DataSync:
    """
    Une classe pour synchroniser les données entre les fichiers (JSON, Excel) et une base de données.
    """

    def __init__(self, db_path: str, db_type: str = 'duckdb'):
        """
        Initialise l'objet DataSync et se connecte à la base de données.

        :param db_path: Chemin vers le fichier de la base de données.
        :param db_type: Type de la base de données ('duckdb' ou 'sqlite').
        """
        if db_type not in ['duckdb', 'sqlite']:
            raise ValueError("db_type doit être 'duckdb' ou 'sqlite'")

        self.db_path = Path(db_path)
        self.engine = create_engine(f"{db_type}:///{self.db_path}")
        self.df = pd.DataFrame()
        self._ensure_db_directory_exists()

    def _ensure_db_directory_exists(self):
        """S'assure que le répertoire parent du fichier de base de données existe."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def load_from_excel(self, file_path: str, sheet_name: str | int = 0, column_mapping: dict | None = None):
        """
        Charge les données d'un fichier Excel dans le DataFrame interne.

        :param file_path: Chemin vers le fichier Excel.
        :param sheet_name: Nom ou index de la feuille à lire.
        :param column_mapping: Dictionnaire pour renommer les colonnes. Ex: {'Ancien Nom': 'nouveau_nom'}
        """
        try:
            self.df = pd.read_excel(file_path, sheet_name=sheet_name)
            if column_mapping:
                self.df.rename(columns=column_mapping, inplace=True)
        except FileNotFoundError:
            raise DataSyncError(f"Fichier Excel non trouvé à {file_path}")
        except Exception as e:
            raise DataSyncError(f"Erreur lors de la lecture du fichier Excel : {e}")

    def load_from_json(self, file_path: str, orient: str = 'records', column_mapping: dict | None = None):
        """
        Charge les données d'un fichier JSON dans le DataFrame interne.

        :param file_path: Chemin vers le fichier JSON.
        :param orient: Orientation du format JSON.
        :param column_mapping: Dictionnaire pour renommer les colonnes. Ex: {'Ancien Nom': 'nouveau_nom'}
        """
        try:
            self.df = pd.read_json(file_path, orient=orient)
            if column_mapping:
                self.df.rename(columns=column_mapping, inplace=True)
        except FileNotFoundError:
            raise DataSyncError(f"Fichier JSON non trouvé à {file_path}")
        except Exception as e:
            raise DataSyncError(f"Erreur lors de la lecture du fichier JSON : {e}")

    def save_to_excel(self, file_path: str, sheet_name: str = 'Sheet1', index: bool = False):
        """
        Sauvegarde le DataFrame interne dans un fichier Excel.

        :param file_path: Chemin vers le fichier Excel de sortie.
        :param sheet_name: Nom de la feuille dans laquelle écrire.
        :param index: Indique s'il faut écrire l'index du DataFrame.
        """
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            self.df.to_excel(file_path, sheet_name=sheet_name, index=index)
        except Exception as e:
            raise DataSyncError(f"Erreur lors de l'écriture dans le fichier Excel : {e}")

    def save_to_json(self, file_path: str, orient: str = 'records', indent: int = 4):
        """
        Sauvegarde le DataFrame interne dans un fichier JSON.

        :param file_path: Chemin vers le fichier JSON de sortie.
        :param orient: Orientation du format JSON.
        :param indent: Niveau d'indentation pour une sortie formatée.
        """
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            self.df.to_json(file_path, orient=orient, indent=indent, force_ascii=False)
        except Exception as e:
            raise DataSyncError(f"Erreur lors de l'écriture dans le fichier JSON : {e}")

    def sync_to_db(self, table_name: str, if_exists: str = 'replace'):
        """
        Synchronise le DataFrame interne avec une table de la base de données.

        :param table_name: Nom de la table de la base de données.
        :param if_exists: Comportement si la table existe déjà ('replace', 'append', 'fail').
        """
        if self.df.empty:
            raise DataSyncError("Le DataFrame est vide. Rien à synchroniser avec la base de données.")

        try:
            with self.engine.connect() as connection:
                self.df.to_sql(table_name, connection, if_exists=if_exists, index=False)
        except Exception as e:
            raise DataSyncError(f"Erreur lors de la synchronisation avec la base de données : {e}")

    def load_from_db(self, table_name: str):
        """
        Charge les données d'une table de base de données dans le DataFrame interne.

        :param table_name: Nom de la table de la base de données.
        """
        try:
            self.df = pd.read_sql_table(table_name, self.engine)
        except Exception as e:
            raise DataSyncError(f"Erreur lors du chargement depuis la table de base de données '{table_name}': {e}")

    def query(self, sql_query: str) -> pd.DataFrame:
        """
        Exécute une requête SQL sur la base de données et retourne le résultat sous forme de DataFrame.

        :param sql_query: La requête SQL à exécuter.
        :return: Un DataFrame pandas avec les résultats de la requête.
        """
        try:
            with self.engine.connect() as connection:
                result_df = pd.read_sql_query(text(sql_query), connection)
            return result_df
        except Exception as e:
            raise DataSyncError(f"Erreur lors de l'exécution de la requête : {e}")

    def get_df(self) -> pd.DataFrame:
        """
        Retourne le DataFrame interne.

        :return: Le DataFrame pandas actuel.
        """
        return self.df

    def validate(self, schema: pa.DataFrameSchema):
        """
        Valide le DataFrame interne par rapport à un schéma pandera.

        :param schema: Le schéma pandera à utiliser pour la validation.
        :raises DataSyncError: Si la validation échoue.
        """
        try:
            schema.validate(self.df, lazy=True)
            # Le paramètre lazy=True permet de rapporter toutes les erreurs de validation en une fois.
        except pa.errors.SchemaErrors as e:
            # Renvoyer l'erreur de pandera encapsulée dans une DataSyncError
            raise DataSyncError(f"La validation des données a échoué :\n{e}")
