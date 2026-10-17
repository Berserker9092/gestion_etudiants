import json
import logging
from datetime import date
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
from app.database import get_db_connection, executer_insertion_base
from app.logging_config import setup_logging 

# Initialisation du logger structuré
setup_logging() 
logger = logging.getLogger("fastapi_app")

from app.validation import (
    EtudiantPropreSchema, 
    EtudiantUpdateSchema, 
    ImportSelectionSchema, 
    NoteUpdateSchema
)

app = FastAPI(title="API Gestion Étudiants - Production")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROPRES_JSON_PATH = "data/donnees_propres.json"

# 1. ROUTE DE LISTING ET RECHERCHE HYBRIDE (BASE DE DONNÉES + FALLBACK JSON)
@app.get("/api/etudiants")
def list_etudiants(
    page: int = Query(1, ge=1), size: int = Query(5, ge=1),
    numero: str = Query(None), code: str = Query(None),
    nom_prenom: str = Query(None), classe: str = Query(None),
    source: str = Query(None), uniquement_archives: bool = Query(False)
):
    limit, offset = size, (page - 1) * size
    sql_base = "FROM etudiants WHERE est_archive = %s"
    params = [uniquement_archives]

    for field, val in [("numero", numero), ("code", code)]:
        if val:
            sql_base += f" AND {field} ILIKE %s"
            params.append(f"%{val}%")
    if nom_prenom:
        sql_base += " AND (nom ILIKE %s OR prenom ILIKE %s)"
        params.extend([f"%{nom_prenom}%", f"%{nom_prenom}%"])
    if classe:
        sql_base += " AND classe = %s"
        params.append(classe)

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) {sql_base};", tuple(params))
            total_db = cursor.fetchone()["count"]

            db_students = []
            if source != "JSON":
                cursor.execute(f"SELECT * {sql_base} LIMIT %s OFFSET %s;", tuple(params + [limit, offset]))
                db_students = cursor.fetchall()
            
            cursor.execute("SELECT numero FROM etudiants;")
            tous_les_numeros_db = {row["numero"] for row in cursor.fetchall()}

    results = [{
        "id": s["id"], "code": s["code"], "numero": s["numero"], "nom": s["nom"],
        "prenom": s["prenom"], "date_naissance": str(s["date_naissance"]), "classe": s["classe"],
        "moyenne_generale": float(s["moyenne_generale"]) if s["moyenne_generale"] else 0.0,
        "est_archive": s["est_archive"], "provenance": "DB"
    } for s in db_students]

    if uniquement_archives:
        return {"page": page, "size": size, "data": results}

    if source != "DB" and len(results) < limit:
        try:
            with open(PROPRES_JSON_PATH, "r", encoding="utf-8") as f:
                json_data = json.load(f)
        except FileNotFoundError:
            json_data = []

        filtered_json = []
        for item in json_data:
            if item.get("est_archive", False) or item.get("numero") in tous_les_numeros_db:
                continue
            if numero and numero.lower() not in item.get("numero", "").lower(): continue
            if code and code.lower() not in item.get("code", "").lower(): continue
            if nom_prenom and nom_prenom.lower() not in item.get("nom", "").lower() and nom_prenom.lower() not in item.get("prenom", "").lower(): continue
            if classe and item.get("classe") != classe: continue
            filtered_json.append(item)

        json_offset = max(0, offset - total_db)
        for item in filtered_json[json_offset : json_offset + (limit - len(results))]:
            notes = item.get("notes", {})
            moy_g = round(sum(n["moyenne"] for n in notes.values() if "moyenne" in n) / len(notes), 2) if notes else 0.0
            results.append({
                "id": item.get("id"), "code": item.get("code"), "numero": item.get("numero"),
                "nom": item.get("nom"), "prenom": item.get("prenom"), "date_naissance": item.get("date_naissance"),
                "classe": str(item.get("classe")), "moyenne_generale": moy_g, "est_archive": False, "provenance": "JSON"
            })

    # Log d'action de recherche avec attributs
    logger.info("Consultation de la liste des étudiants", extra={
        "extra_data": {
            "action": "recherche_etudiants",
            "classe_filtre": classe,
            "resultats_count": len(results),
            "page": page
        }
    })

    return {"page": page, "size": size, "data": results}


# 2. ROUTE POUR CRÉER ET AJOUTER UN NOUVEL ÉTUDIANT (AVEC SES NOTES) EN DB
@app.post("/api/etudiants/ajouter")
def ajouter_etudiant(etudiant: EtudiantPropreSchema):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM etudiants WHERE numero = %s;", (etudiant.numero,))
            if cursor.fetchone():
                logger.warning("Échec d'ajout : étudiant déjà existant", extra={
                    "extra_data": {
                        "action": "ajout_etudiant_echec",
                        "etudiant_numero": etudiant.numero,
                        "etudiant_code": etudiant.code
                    }
                })
                raise HTTPException(
                    status_code=400, 
                    detail="Un étudiant avec ce numéro matricule existe déjà."
                )
    
    notes_eleve = etudiant.notes
    if notes_eleve:
        somme_moyennes = sum(info.moyenne for info in notes_eleve.values())
        moyenne_g = round(somme_moyennes / len(notes_eleve), 2)
    else:
        moyenne_g = 0.0

    try:
        executer_insertion_base(
            etudiant_valide=etudiant, 
            notes_nettoyees=notes_eleve, 
            moyenne_g=moyenne_g
        )
        
        # Log structuré complet émis vers ELK
        logger.info("Nouvel étudiant ajouté avec succès", extra={
            "extra_data": {
                "action": "ajout_etudiant",
                "etudiant_code": etudiant.code,
                "etudiant_numero": etudiant.numero,
                "etudiant_classe": etudiant.classe,
                "moyenne_generale": moyenne_g,
                "nb_matieres": len(notes_eleve) if notes_eleve else 0
            }
        })
    except Exception as e:
        logger.error(f"Erreur d'insertion DB: {str(e)}", extra={
            "extra_data": {
                "action": "erreur_db_ajout",
                "etudiant_code": etudiant.code
            }
        })
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de l'insertion en base de données : {str(e)}"
        )

    return {
        "status": "success", 
        "message": f"L'étudiant {etudiant.prenom} {etudiant.nom} et ses notes ont été insérés avec succès dans la db."
    }

# 3. ROUTE D'IMPORTATION DE SÉLECTION D'ÉTUDIANTS DU FICHIER JSON VERS LA BASE DE DONNÉES
@app.post("/api/etudiants/importer")
def importer_etudiants(payload: ImportSelectionSchema):
    try:
        with open(PROPRES_JSON_PATH, "r", encoding="utf-8") as f:
            etudiants_json = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Fichier JSON introuvable.")

    import_count = 0
    liste_numeros = payload.numeros_selectionnes

    for item in etudiants_json:
        if item.get("numero") in liste_numeros:
            try:
                etudiant_valide = EtudiantPropreSchema(**item)
                notes_pydantic = etudiant_valide.notes
                
                if notes_pydantic:
                    somme_moyennes = sum(info.moyenne for info in notes_pydantic.values())
                    moy_g = round(somme_moyennes / len(notes_pydantic), 2)
                else:
                    moy_g = 0.0
                
                executer_insertion_base(
                    etudiant_valide=etudiant_valide, 
                    notes_nettoyees=notes_pydantic, 
                    moyenne_g=moy_g
                )
                import_count += 1
            except Exception as e:
                print(f"Erreur : {e}")

    logger.info("Importation d'étudiants terminée", extra={
        "extra_data": {
            "action": "import_json_to_db",
            "import_count": import_count
        }
    })
                
    return {"status": "success", "message": f"{import_count} étudiants traités."}


# 4. ROUTE DES STATISTIQUES GLOBALES POUR ALIMENTER LE DASHBOARD
@app.get("/api/statistiques")
def obtenir_statistiques():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT classe, COUNT(*) as total FROM etudiants WHERE est_archive = FALSE GROUP BY classe;")
            repartition_classes = cursor.fetchall()

            cursor.execute("SELECT classe, ROUND(AVG(moyenne_generale)::numeric, 2) as moyenne_classe FROM etudiants WHERE est_archive = FALSE GROUP BY classe;")
            moyennes_par_classe = cursor.fetchall()

            cursor.execute("SELECT nom, prenom, moyenne_generale, 'DB' as provenance FROM etudiants WHERE est_archive = FALSE ORDER BY moyenne_generale DESC LIMIT 10;")
            top_db = cursor.fetchall()

            cursor.execute("SELECT COUNT(*) as total FROM etudiants WHERE est_archive = FALSE;")
            actifs_db = cursor.fetchone()["total"]
            
            cursor.execute("SELECT COUNT(*) as total FROM etudiants WHERE est_archive = TRUE;")
            archives_db = cursor.fetchone()["total"]

            cursor.execute("SELECT numero FROM etudiants;")
            tous_les_numeros_db = {row["numero"] for row in cursor.fetchall()}

    try:
        with open(PROPRES_JSON_PATH, "r", encoding="utf-8") as f:
            json_data = json.load(f)
    except FileNotFoundError:
        json_data = []

    json_actifs = [item for item in json_data if not item.get("est_archive", False) and item.get("numero") not in tous_les_numeros_db]
    total_json = len(json_actifs)

    top_json = []
    for item in json_actifs:
        notes = item.get("notes", {})
        moy_g = round(sum(n["moyenne"] for n in notes.values() if "moyenne" in n) / len(notes), 2) if notes else 0.0
        top_json.append({"nom": item.get("nom"), "prenom": item.get("prenom"), "moyenne_generale": moy_g, "provenance": "JSON"})

    tous_les_top = top_db + top_json
    tous_les_top.sort(key=lambda x: x["moyenne_generale"], reverse=True)

    return {
        "indicateurs": {
            "total_global": actifs_db + total_json + archives_db,
            "total_db": actifs_db, "total_json": total_json, "total_archives": archives_db
        },
        "repartition_classes": repartition_classes,
        "repartition_sources": [{"source": "Base de données (DB)", "total": actifs_db}, {"source": "Fichier JSON", "total": total_json}],
        "moyennes_par_classe": moyennes_par_classe,
        "top_etudiants": tous_les_top[:10]
    }


# 5. ROUTE POUR MODIFIER LES INFORMATIONS DE BASE D'UN ÉTUDIANT
@app.put("/api/etudiants/{numero}")
def modifier_etudiants(numero: str, data: EtudiantUpdateSchema):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE etudiants SET nom = %s, prenom = %s, classe = %s WHERE numero = %s;", (data.nom, data.prenom, data.classe, numero))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Étudiant non trouvé.")

    logger.info("Modification des informations de l'étudiant", extra={
        "extra_data": {
            "action": "modification_etudiant",
            "etudiant_numero": numero,
            "nouvelle_classe": data.classe
        }
    })
    return {"status": "success", "message": "Étudiant mis à jour."}


# 6. ROUTE POUR ARCHIVER UN ÉTUDIANT (SOFT DELETE)
@app.post("/api/etudiants/{numero}/archiver")
def archiver_etudiant(numero: str):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE etudiants SET est_archive = TRUE WHERE numero = %s;", (numero,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Étudiant non trouvé.")

    logger.info("Archivage d'un étudiant", extra={
        "extra_data": {
            "action": "archivage_etudiant",
            "etudiant_numero": numero
        }
    })
    return {"status": "success", "message": "Étudiant archivé."}


# 7. ROUTE POUR SUPPRIMER DÉFINITIVEMENT UN ÉTUDIANT
@app.delete("/api/etudiants/{numero}")
def supprimer_etudiant(numero: str):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM etudiants WHERE numero = %s;", (numero,))
            res = cursor.fetchone()
            if not res: raise HTTPException(status_code=404, detail="Étudiant introuvable.")
            
            cursor.execute("DELETE FROM notes WHERE etudiant_id = %s;", (res["id"],))
            cursor.execute("DELETE FROM etudiants WHERE id = %s;", (res["id"],))
            conn.commit()

    logger.info("Suppression définitive d'un étudiant", extra={
        "extra_data": {
            "action": "suppression_etudiant",
            "etudiant_numero": numero
        }
    })
    return {"status": "success", "message": "Étudiant et notes supprimés définitivement."}


# 8. ROUTE POUR RÉCUPÉRER TOUTES LES NOTES PAR MATIÈRE
@app.get("/api/etudiants/{numero}/notes")
def recuperer_notes_etudiant(numero: str):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT n.id as note_id, m.nom_matiere, n.note_devoir, n.note_examen, n.moyenne_matiere
                FROM notes n JOIN etudiants e ON n.etudiant_id = e.id JOIN matieres m ON n.matiere_id = m.id
                WHERE e.numero = %s;
            """, (numero,))
            return cursor.fetchall()


# 9. ROUTE POUR MODIFIER LES NOTES ET RECALCULER AUTOMATIQUEMENT LES MOYENNES
@app.put("/api/etudiants/{numero}/notes")
def modifier_notes_etudiant(numero: str, payload: list[NoteUpdateSchema]):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            total_moyennes, nombre_matieres = 0, len(payload)
            for n in payload:
                moy_dev = sum(n.note_devoir) / len(n.note_devoir) if n.note_devoir else 0
                nouvelle_moy = round((moy_dev + (2 * n.note_examen)) / 3, 2)
                total_moyennes += nouvelle_moy
                cursor.execute("UPDATE notes SET note_devoir = %s, note_examen = %s, moyenne_matiere = %s WHERE id = %s;", (n.note_devoir, n.note_examen, nouvelle_moy, n.note_id))

            nouvelle_mg = round(total_moyennes / nombre_matieres, 2) if nombre_matieres else 0
            cursor.execute("UPDATE etudiants SET moyenne_generale = %s WHERE numero = %s;", (nouvelle_mg, numero))
            conn.commit()

    logger.info("Mise à jour des notes et de la moyenne générale", extra={
        "extra_data": {
            "action": "modification_notes",
            "etudiant_numero": numero,
            "nouvelle_moyenne_generale": nouvelle_mg
        }
    })
    return {"status": "success", "message": "Notes et moyennes recalculées."}


# 10. ROUTE POUR DÉSARCHIVER / RESTAURER UN ÉTUDIANT
@app.post("/api/etudiants/{numero}/restaurer")
def restaurer_etudiant(numero: str):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE etudiants SET est_archive = FALSE WHERE numero = %s;", (numero,))
            conn.commit()
            if cursor.rowcount == 0: raise HTTPException(status_code=404, detail="Étudiant non trouvé.")

    logger.info("Restauration d'un étudiant archivé", extra={
        "extra_data": {
            "action": "restauration_etudiant",
            "etudiant_numero": numero
        }
    })
    return {"status": "success", "message": "Étudiant restauré."}