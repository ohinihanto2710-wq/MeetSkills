# MeetSkills 🎓

**MeetSkills** est une plateforme web de mentorat académique entre étudiants du Bénin. Elle permet aux étudiants de toutes filières et universités de se connecter pour s'entraider : certains proposent leur aide sur des matières qu'ils maîtrisent, d'autres recherchent du soutien sur leurs lacunes.

🌐 **Site en ligne** : [https://stately-meerkat-256530.netlify.app](https://stately-meerkat-256530.netlify.app)

---

## 🎯 Objectif

Mettre en relation des étudiants béninois souhaitant offrir ou bénéficier de mentorat académique, toutes filières confondues, via une plateforme simple, moderne et accessible.

---

## ✨ Fonctionnalités principales

- **Inscription / Connexion** sécurisée avec authentification JWT
- **Profil utilisateur** avec compétences, lacunes et disponibilités
- **Algorithme de matching** automatique basé sur les compétences, disponibilités et domaines d'études
- **Publication d'annonces** d'offres et de demandes de mentorat
- **Messagerie instantanée** entre mentor et mentoré
- **Interface responsive** adaptée mobile et desktop

---

## 🛠️ Technologies utilisées

### Backend
- Python / Django
- Django REST Framework (DRF)
- JWT (authentification)
- PostgreSQL (Supabase)
- Gunicorn / WhiteNoise

### Frontend
- HTML / CSS / JavaScript (vanilla)
- Design responsive mobile-first

### Déploiement
- Backend : [Render](https://render.com)
- Frontend : [Netlify](https://netlify.app)
- Base de données : [Supabase](https://supabase.com)

---

## 📁 Structure du projet
MeetSkills/
├── backend/ # API Django
│ ├── accounts/ # Gestion des utilisateurs
│ ├── matching/ # Algorithme de matching et annonces
│ ├── messaging/ # Messagerie instantanée
│ ├── meetskills/ # Configuration Django
│ └── manage.py
├── frontend/ # Interface web
│ ├── css/ # Styles
│ ├── js/ # Scripts
│ ├── index.html # Page d'accueil
│ ├── connexion.html # Page de connexion
│ ├── inscription.html # Page d'inscription
│ ├── profil.html # Page de profil
│ ├── recherche.html # Recherche de mentors
│ ├── publication.html # Publication d'annonces
│ └── messagerie.html # Messagerie
└── docs/ # Documentation

---

## 🚀 Installation et déploiement local

### Prérequis
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (gestionnaire de paquets Python)
- Git

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/ohinihanto2710-wq/MeetSkills.git
cd MeetSkills

# 2. Installer les dépendances
cd backend
uv sync

# 3. Configurer les variables d'environnement
cp .env.example .env
# Remplir les valeurs dans .env (SECRET_KEY, DATABASE_URL, etc.)

# 4. Appliquer les migrations
uv run python manage.py migrate

# 5. Lancer le serveur
uv run python manage.py runserver
```

### Frontend
Ouvrir `frontend/index.html` avec un serveur local (ex: Live Server dans VS Code).

---

## 👤 Auteur

**HANTO Ohini Jordy-Mayel**  
Étudiant en L1 Informatique — IFRI, Université d'Abomey-Calavi, Bénin  
GitHub : [@ohinihanto2710-wq](https://github.com/ohinihanto2710-wq)

---

## 📄 Licence

Projet personnel — tous droits réservés © 2026 HANTO Ohini Jordy-Mayel 
