# 📬 Scraper Serveur Mail (Whois Outlook Checker)

Application Python avec interface graphique (Tkinter) qui vérifie automatiquement si un domaine utilise un serveur mail Outlook via le site [whois-raynette.fr](https://www.whois-raynette.fr).

---

## ✅ Fonctionnalités

- Interface utilisateur simple avec Tkinter
- Chargement d’un fichier CSV contenant une liste de domaines
- Accès automatisé à la page Whois de Raynette pour chaque domaine
- Extraction du champ **Serveur(s) mail**
- Vérifie si le serveur contient **"outlook"**
- Sauvegarde automatique dans un CSV (`OUI` / `NON`)
- Affichage de progression et journalisation en temps réel

---

## 📦 Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### Exemple de `requirements.txt` :

```
pandas
selenium
requests
```

---

## 🌐 Pré-requis navigateur

1. Avoir **Google Chrome** installé.
2. Télécharger le **ChromeDriver** correspondant à ta version ici :  
   👉 https://chromedriver.chromium.org/downloads
3. Place le binaire dans le même dossier que ton script ou dans le PATH système.

---

## 🚀 Utilisation

```bash
python whois_outlook_scraper_gui.py
```

Dans l’application :
- Clique sur **Charger CSV** pour importer le fichier contenant les domaines.
- Indique un nom de fichier de sortie (ex: `résultat.csv`)
- Clique sur **Démarrer**
- Clique sur **Arrêter** pour interrompre si besoin

---

## 🧾 Format du fichier CSV attendu

Une seule colonne contenant des noms de domaine, sans en-tête :

```
microsoft.com
monentreprise.fr
laposte.net
```

---

## 📤 Fichier de sortie

Fichier CSV généré avec deux colonnes :

| domain           | outlook_server |
|------------------|----------------|
| microsoft.com    | OUI            |
| laposte.net      | NON            |
| domaine-invalide | Erreur         |

---

## 🧠 Notes techniques

- Le scraping repose sur Selenium et XPath pour identifier le champ `Serveur(s) mail`.
- L'utilisation d'`outlook` est détectée de manière insensible à la casse (`.lower()`).

---

## 📄 Licence

Libre d’utilisation, modification et distribution pour tout usage personnel ou professionnel.