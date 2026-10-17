# Registre — Plateforme de gestion des étudiants

Application web de gestion de scolarité : registre des étudiants, fiches détaillées, classes, archives et tableau de bord analytique.
Frontend **Vue 3** connecté à une API **FastAPI** et à une base **PostgreSQL**.

## Fonctionnalités

- **Accueil** : indicateurs animés, meilleurs résultats, répartition par classe, étudiants à accompagner, actions rapides
- **Registre** : recherche en direct, filtres avancés, tri, pagination, vue tableau ou cartes, édition rapide, import depuis JSON, export Excel et PDF
- **Fiche étudiant** : identité, moyenne générale, mention, rang dans la classe, comparaison à la moyenne de classe, détail des notes, **bulletin PDF**
- **Classes** : effectif, moyenne et taux de réussite par classe
- **Analyses** : graphiques Chart.js (moyennes par matière, répartition, distribution, sources par classe)
- **Archives** : restauration ou suppression définitive
- **Palette de recherche** (`Ctrl/⌘ + K`) pour retrouver un étudiant ou changer de page
- Thème clair/sombre, interface FR/EN, responsive, accessibilité clavier

## Stack

Vue 3 (`<script setup>`) · Vue Router · vue-i18n · Chart.js · jsPDF · SheetJS · Vite — FastAPI · Pydantic · PostgreSQL

## Structure

```
src/
  config.js            nom de l'application et liens
  App.vue              coque : menu latéral, barre supérieure, palette
  router/index.js      routes et métadonnées (titres, fil d'Ariane)
  services/api.js      appels à l'API FastAPI
  composables/         état partagé (stats, thème, toasts, confirmation, shell)
  components/          avatar, anneau de score, sidebar, topbar, palette...
  views/               Home, EtudiantsListe, EtudiantFiche, Classes, Archive, Dashboard...
  utils/               calculs de notes/mentions, exports Excel et PDF
backend/               API FastAPI + schéma de validation
```

## Installation

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # puis renseigne DB_PASSWORD
uvicorn app.main:app --reload
```

### Frontend

```bash
cp .env.example .env
npm install
npm run dev                 # http://localhost:5173
npm run build               # production → dist/
```

## Personnalisation

Le nom de la plateforme, le slogan et le lien GitHub se modifient dans `src/config.js`.

## Captures d'écran

Ajoute tes captures dans `docs/` puis référence-les ici (accueil, fiche étudiant, analyses).
