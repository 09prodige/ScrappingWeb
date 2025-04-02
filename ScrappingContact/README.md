# 🗺️ Google Maps Scraper GUI

Application Python avec interface graphique (Tkinter) permettant d'extraire automatiquement les numéros de téléphone et les sites web depuis des recherches Google Maps basées sur un fichier CSV.

---

## ✅ Fonctionnalités

- Interface graphique simple (Tkinter)
- Chargement d’un fichier CSV contenant des requêtes d’adresses ou de lieux
- Recherches automatisées sur Google Maps avec Selenium
- Sélection **intelligente** de la meilleure suggestion grâce à `fuzzywuzzy`
- Extraction :
  - 📞 Numéro de téléphone
  - 🌐 Site web
  - 🧠 Score de similarité (comparaison avec la requête)
- Sauvegarde automatique dans un fichier `.csv` après chaque ligne

---

## 📦 Installation

```bash
# Crée un environnement virtuel (optionnel mais recommandé)
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate       # Windows

# Installe les dépendances
pip install -r requirements.txt
```

### 🧪 `requirements.txt`

```
pandas
selenium
fuzzywuzzy
python-Levenshtein
requests
```

---

## 🌐 Prérequis navigateur

Télécharge [ChromeDriver](https://chromedriver.chromium.org/downloads)  
💡 La version doit correspondre à ta version de Chrome installée.  
Place le fichier dans le même dossier que ton script ou ajoute-le au `PATH`.

---

## 🚀 Utilisation

```bash
python google_maps_scraper_gui.py
```

### Dans l'application :
1. Clique sur **“Charger CSV”** pour importer ton fichier contenant les requêtes.
2. Saisis un nom de fichier de sortie.
3. Clique sur **“Démarrer”**.
4. Les logs s’affichent en temps réel. Tu peux arrêter à tout moment avec **“Arrêter”**.

---

## 🧾 Format du fichier CSV attendu

Chaque ligne doit contenir une requête à chercher dans Google Maps :

```
COPR IMM R DU HARAS - 13 RUE DU HARAS - 49100
COPR IMM LE MAIL - 5 PL DE LORRAINE - 49100
...
```

---

## 📤 Fichier de sortie

Un fichier `.csv` est généré contenant les colonnes suivantes :

| query | phone_number | website | score |
|-------|--------------|---------|-------|
| Adresse cherchée | 📞 Numéro trouvé | 🌐 Site trouvé | 🎯 Similarité (0-100) |

---

## 🧠 Logique du score

- Utilise `fuzzywuzzy.token_sort_ratio` pour comparer la requête et la suggestion.
- Seules les suggestions avec un **score ≥ 70** sont sélectionnées.
- Le score est inclus dans le CSV pour évaluer la qualité du match.

---

## 🧩 Technologies utilisées

- [Python](https://www.python.org/)
- [Tkinter](https://docs.python.org/3/library/tkinter.html)
- [Selenium](https://www.selenium.dev/)
- [Pandas](https://pandas.pydata.org/)
- [FuzzyWuzzy](https://github.com/seatgeek/fuzzywuzzy)

---

## 📄 Licence

Projet open-source – libre d’utilisation et de modification.