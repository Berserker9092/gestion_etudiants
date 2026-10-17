import re
from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel, Field, field_validator

## 1. MODÈLE DE VALIDATION DES NOTES DÉTAILLÉES PAR MATIÈRE
class DetailNotes(BaseModel):
    devoirs: List[float]
    examen: float
    moyenne: float

### 2. MODÈLE PRINCIPAL DE VALIDATION DES ÉTUDIANTS
class EtudiantPropreSchema(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)
    numero: str = Field(..., min_length=7, max_length=7)
    nom: str = Field(..., min_length=2, max_length=100)
    prenom: str = Field(..., min_length=2, max_length=100)
    date_naissance: str
    classe: str = Field(..., min_length=2, max_length=10)
    notes: Dict[str, DetailNotes]

    # Décorateur ajouté pour appliquer la règle de validation du code
    @field_validator('code')
    @classmethod
    def valider_format_code(cls, v: str) -> str:
        if not re.match(r"^[A-Z]{3}\d{3}$", v):
            raise ValueError("Le code doit être composé exactement de 3 lettres majuscules suivies de 3 chiffres (Ex: AAD001).")
        return v

    # Une seule déclaration pour le formatage de la date
    @field_validator('date_naissance')
    @classmethod
    def formater_date(cls, v: str) -> str:
        try:
            return datetime.strptime(v.replace("-", "/"), "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            return v  # Conserve la chaîne si la conversion échoue ou est déjà au format YYYY-MM-DD

## 3. SCHÉMA DE RÉCEPTION POUR L'IMPORTATION DE SÉLECTION D'ÉTUDIANTS
class ImportSelectionSchema(BaseModel):
    numeros_selectionnes: List[str] = Field(..., alias="numeros")

    class Config:
        populate_by_name = True

## 4. SCHÉMA DE VALIDATION POUR LA MISE À JOUR DES INFORMATIONS D'UN ÉTUDIANT
class EtudiantUpdateSchema(BaseModel):
    nom: str
    prenom: str
    classe: str

## 5. SCHÉMA DE VALIDATION POUR LA MISE À JOUR DES NOTES D'UN EXAMEN OU DEVOIR
class NoteUpdateSchema(BaseModel):
    note_id: int
    note_devoir: List[float]
    note_examen: float