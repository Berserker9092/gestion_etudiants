#def extraire_notes_depuis_texte(texte_notes):
#    if not texte_notes:
#        return {}
#
#    dictionnaire_matieres = {}
#    blocs = texte_notes.split("#")
#
#    for bloc in blocs:
#        bloc = bloc.strip()
#        if not bloc or "[" not in bloc:
#            continue
#
#        nom_matiere, reste = bloc.split("[")
#        nom_matiere = nom_matiere.strip()
#        corps_notes = reste.replace("]", "").strip()
#
#        if ":" in corps_notes:
#            partie_dev, partie_exam = corps_notes.split(":")
#
#            partie_dev = partie_dev.replace(",", "|")
#            if "|" in partie_dev:
#                liste_devoirs = [float(d) for d in partie_dev.split("|") if d.strip()]
#            else:
#                liste_devoirs = [float(partie_dev)] if partie_dev.strip() else []
#
#            note_examen = float(partie_exam)
#
#            moyenne = (sum(liste_devoirs) / len(liste_devoirs) + 2 * note_examen) / 3
#
#            dictionnaire_matieres[nom_matiere] = {
#                "devoirs": liste_devoirs,
#                "examen": note_examen,
#                "moyenne": round(moyenne, 2)
#            }
#
#    return dictionnaire_matieres

import json
import pandas as pd


def extraire_notes_depuis_texte(texte_notes):
    if not texte_notes:
        return {}

    dictionnaire_matieres = {}
    blocs = texte_notes.split("#")

    for bloc in blocs:
        bloc = bloc.strip()

        if not bloc or "[" not in bloc:
            continue

        nom_matiere, reste = bloc.split("[", 1)
        nom_matiere = nom_matiere.strip()

        corps_notes = reste.replace("]", "").strip()

        if ":" in corps_notes:
            partie_dev, partie_exam = corps_notes.split(":", 1)

            partie_dev = partie_dev.replace(",", "|")

            liste_devoirs = [
                float(x)
                for x in partie_dev.split("|")
                if x.strip()
            ]

            note_examen = float(partie_exam)

            moyenne = (
                (sum(liste_devoirs) / len(liste_devoirs))
                + 2 * note_examen
            ) / 3

            dictionnaire_matieres[nom_matiere] = round(moyenne, 2)

    return dictionnaire_matieres

test=extraire_notes_depuis_texte("PC[7|10|9:10]#Math[11|10|12:10]#Francais[14:15]#Anglais[14:14]#SVT[14|12|10:10]#HG[14:14]")
print(test)
 #Lecture du fichier JSON
with open("/home/berserker9092/Documents/sql/projet/backend/data/valides.json", "r", encoding="utf-8") as f:
    donnees = json.load(f)

lignes = []

for eleve in donnees:

    ligne = {
        "code": eleve.get("code"),
        "numero": eleve.get("numero"),
        "nom": eleve.get("nom"),
        "prenom": eleve.get("prenom"),
        "date": eleve.get("date"),
        "classe": eleve.get("classe")
    }

    notes = extraire_notes_depuis_texte(eleve.get("note", ""))

    ligne.update(notes)

    lignes.append(ligne)

# Création du DataFrame
df = pd.DataFrame(lignes)

import csv
import json

with open("/home/berserker9092/Documents/sql/projet/backend/eleves_reorganises.csv", "r", encoding="utf-8") as f:
    donnees = list(csv.DictReader(f))

with open("/home/berserker9092/Documents/sql/projet/backend/eleves_reorganises.json", "w", encoding="utf-8") as f:
    json.dump(donnees, f, ensure_ascii=False, indent=4)
# Sauvegarde CSV
#df.to_csv(
#    "eleves_reorganises.csv",
#    index=False,
#    encoding="utf-8-sig"
#)
#
#print("CSV généré : eleves_reorganises.csv")