import psycopg2
from psycopg2.extras import RealDictCursor

## Configuration de la base PostgreSQL : lue depuis les variables d'environnement
## (copie backend/.env.example vers backend/.env et renseigne tes valeurs — ce fichier n'est jamais versionné)
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv est optionnel : les variables peuvent venir du système

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "gestion_ecole"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
}

## Fonction unique pour récupérer une connexion avec curseur en Dictionnaire
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

## Fonction pour insérer un étudiant importé du JSON avec ses notes
## Fonction pour insérer un étudiant importé du JSON ou du formulaire avec ses notes
def executer_insertion_base(etudiant_valide, notes_nettoyees, moyenne_g):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            try:
                # 1. Insertion de l'étudiant
                cur.execute("""
                    INSERT INTO etudiants (code, numero, nom, prenom, date_naissance, classe, moyenne_generale)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;
                """, (
                    etudiant_valide.code, 
                    etudiant_valide.numero, 
                    etudiant_valide.nom, 
                    etudiant_valide.prenom, 
                    getattr(etudiant_valide, 'date_naissance', getattr(etudiant_valide, 'date', None)), 
                    etudiant_valide.classe, 
                    moyenne_g
                ))
                # Récupération de l'ID généré en base de données
                etudiant_id = cur.fetchone()["id"]
                
                # 2. Insertion des matières et des notes liées
                for nom_matiere, infos in notes_nettoyees.items():
                    # Crée la matière si elle n'existe pas, sinon récupère son ID
                    cur.execute("""
                        INSERT INTO matieres (nom_matiere) VALUES (%s)
                        ON CONFLICT (nom_matiere) DO UPDATE SET nom_matiere = EXCLUDED.nom_matiere 
                        RETURNING id;
                    """, (nom_matiere,))
                    matiere_id = cur.fetchone()["id"]
                
                    # CORRECTION ICI : On utilise le "." à la place des "[]" car infos est un objet DetailNotes
                    cur.execute("""
                        INSERT INTO notes (etudiant_id, matiere_id, note_devoir, note_examen, moyenne_matiere)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (
                        etudiant_id, 
                        matiere_id, 
                        infos.devoirs,  # Corrigé (au lieu de infos["devoirs"])
                        infos.examen,   # Corrigé (au lieu de infos["examen"])
                        infos.moyenne   # Corrigé (au lieu de infos["moyenne"])
                    ))
                    
                conn.commit()
            except psycopg2.errors.UniqueViolation:
                conn.rollback() # Gère tranquillement les doublons sans faire planter le serveur