import pytest
from pathlib import Path
import sys
import pandas as pd

# Ajoute la racine du projet au PYTHONPATH pour permettre l'importation de data_sync
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_sync import DataSync, DataSyncError
from src.data_sync.schemas import PersonSchema


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Fixture pour fournir un chemin vers une base de données de test temporaire."""
    return tmp_path / "test_db.duckdb"

@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Fixture pour fournir un DataFrame d'exemple."""
    return pd.DataFrame({
        'id': [1, 2],
        'nom': ['Produit A', 'Produit B']
    })

def test_initialization_duckdb(db_path: Path):
    """
    Teste que la classe DataSync peut être initialisée correctement avec DuckDB.
    """
    # Action
    ds = DataSync(db_path=str(db_path))

    # Assertions
    assert ds is not None
    assert ds.engine is not None
    # L'initialisation seule ne crée pas le fichier pour DuckDB,
    # il est créé lors de la première connexion.
    # On va donc le créer en synchronisant des données.
    ds.df = pd.DataFrame({'a': [1]})
    ds.sync_to_db('test_table')

    assert db_path.exists()
    assert db_path.is_file()

def test_initialization_sqlite(tmp_path: Path):
    """
    Teste que la classe DataSync peut être initialisée avec SQLite.
    """
    db_path_sqlite = tmp_path / "test_db.sqlite"
    ds = DataSync(db_path=str(db_path_sqlite), db_type='sqlite')

    assert ds is not None
    assert "sqlite" in str(ds.engine.url)

    # Le fichier de la base de données est créé à la première connexion.
    # Forçons une connexion pour le créer.
    with ds.engine.connect() as conn:
        pass

    assert db_path_sqlite.exists()

def test_invalid_db_type():
    """
    Teste que l'initialisation avec un db_type invalide lève une ValueError.
    """
    with pytest.raises(ValueError, match="db_type doit être 'duckdb' ou 'sqlite'"):
        DataSync(db_path="test.db", db_type="mysql")

def test_sync_to_db_and_load_from_db(db_path: Path, sample_df: pd.DataFrame):
    """
    Teste la synchronisation vers la base de données et le rechargement depuis celle-ci.
    """
    table_name = "test_produits"
    ds = DataSync(db_path=str(db_path))

    # Charger les données et synchroniser
    ds.df = sample_df
    ds.sync_to_db(table_name)

    # Créer une nouvelle instance et recharger
    ds_loader = DataSync(db_path=str(db_path))
    ds_loader.load_from_db(table_name)

    # Assertions
    pd.testing.assert_frame_equal(ds_loader.get_df(), sample_df)


def test_column_mapping_excel(tmp_path: Path):
    """
    Teste que le mappage de colonnes fonctionne correctement lors du chargement depuis Excel.
    """
    # Arrange
    file_path = tmp_path / "test_mapping.xlsx"
    mapping = {'Prénom': 'givenName', 'Nom': 'familyName'}
    data = pd.DataFrame([{'Prénom': 'John', 'Nom': 'Doe'}])
    data.to_excel(file_path, index=False)

    ds = DataSync(db_path=str(tmp_path / "test.db"))

    # Act
    ds.load_from_excel(file_path, column_mapping=mapping)

    # Assert
    assert 'givenName' in ds.get_df().columns
    assert 'familyName' in ds.get_df().columns
    assert 'Prénom' not in ds.get_df().columns

def test_validation_success():
    """
    Teste que la méthode de validation réussit avec des données conformes.
    """
    # Arrange
    compliant_data = pd.DataFrame({
        'givenName': ['Alice'],
        'familyName': ['Smith'],
        'email': ['alice@example.com'],
        'birthDate': [pd.to_datetime('1995-02-10')]
    })
    ds = DataSync(db_path="in_memory.db")
    ds.df = compliant_data

    # Act & Assert
    try:
        ds.validate(PersonSchema)
    except DataSyncError:
        pytest.fail("La validation aurait dû réussir, mais elle a échoué.")

def test_validation_failure():
    """
    Teste que la méthode de validation échoue avec des données non conformes.
    """
    # Arrange
    non_compliant_data = pd.DataFrame({
        'givenName': ['Bob'],
        'familyName': ['Jones'],
        'email': ['not-an-email'], # Email invalide
    })
    ds = DataSync(db_path="in_memory.db")
    ds.df = non_compliant_data

    # Act & Assert
    with pytest.raises(DataSyncError, match="La validation des données a échoué"):
        ds.validate(PersonSchema)
