# -*- coding: utf-8 -*-
"""
Ce module contient des schémas de données prédéfinis utilisant `pandera`.
Ces schémas peuvent être utilisés pour valider la structure et les types de données
des DataFrames chargés.
"""
import pandera as pa
from pandera.typing import Series


# Schéma de base pour les données de type Personne
PersonSchema = pa.DataFrameSchema(
    {
        "givenName": pa.Column(str, checks=pa.Check.str_length(min_value=1), description="Prénom de la personne."),
        "familyName": pa.Column(str, checks=pa.Check.str_length(min_value=1), description="Nom de famille de la personne."),
        "email": pa.Column(str, checks=pa.Check.str_matches(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'), description="Adresse e-mail valide."),
        "birthDate": pa.Column(pa.DateTime, nullable=True, description="Date de naissance (optionnelle)."),
    },
    strict=False,  # N'échoue pas si des colonnes supplémentaires sont présentes
    ordered=False, # N'impose pas un ordre de colonnes spécifique
)
