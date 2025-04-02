import tkinter as tk
from tkinter import filedialog, scrolledtext
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import threading
import requests
import time

# === CONFIGURATION SELENIUM ===
def configure_driver():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-webgl")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--enable-unsafe-webgl")
    options.add_argument("--log-level=3")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Ignorer les erreurs SSL
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-insecure-localhost")
    options.add_argument("--allow-running-insecure-content")
    
    return webdriver.Chrome(options=options)


# === VERIFICATION DE LA CONNEXION INTERNET ===
def check_internet_connection(log, retry_interval=5):
    while True:
        try:
            requests.get("https://www.google.com", timeout=5)
            return True
        except requests.ConnectionError:
            log("Connexion Internet interrompue. Réessai dans quelques secondes...")
            time.sleep(retry_interval)

# === SCRIPT SELENIUM ===
class MailServerScraper:
    def __init__(self):
        self.stop_requested = False

    def search_and_extract(self, driver, domain, log):
        if self.stop_requested:
            return "Interrompu"

        check_internet_connection(log)

        try:
            # Accéder à la page whois de la rainette
            url = f"https://www.whois-raynette.fr/whois/{domain}"
            driver.get(url)
            log(f"Ouverture de la page Whois pour : {domain}")

            # Extraire le serveur mail
            try:
                # XPath modifié pour trouver le serveur mail après "Serveur(s) mail :"
                server_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//strong[text()='Serveur(s) mail :']/following::td[1]")
                    )
                )
                server_text = server_element.text.strip()
                log(f"Serveur mail trouvé pour {domain} : {server_text}")
                
                # Vérifier si le serveur contient "outlook"
                if "outlook" in server_text.lower():
                    return "OUI"
                else:
                    return "NON"
            except TimeoutException:
                log(f"Aucun serveur mail trouvé pour : {domain}.")
                return "NON"

        except Exception as e:
            log(f"Erreur lors de la recherche pour {domain} : {e}")
            return "Erreur"

# === INTERFACE TKINTER ===
class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Scraper Serveur Mail")
        self.scraper = MailServerScraper()
        self.driver = configure_driver()

        # Variables
        self.input_file = None
        self.output_file = None
        self.results = []  # Stocker les résultats partiels
        self.total_queries = 0

        # Interface
        self.setup_ui()

    def setup_ui(self):
        self.load_button = tk.Button(self.root, text="Charger CSV", command=self.load_file)
        self.load_button.pack(pady=5)

        self.output_label = tk.Label(self.root, text="Nom du fichier de sortie :")
        self.output_label.pack(pady=5)
        self.output_entry = tk.Entry(self.root, width=40)
        self.output_entry.pack(pady=5)

        self.start_button = tk.Button(self.root, text="Démarrer", command=self.start_scraping)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(self.root, text="Arrêter", command=self.stop_scraping)
        self.stop_button.pack(pady=5)

        self.log_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=80, height=20)
        self.log_area.pack(pady=5)

        self.progress_label = tk.Label(self.root, text="Progression : 0/0")
        self.progress_label.pack(pady=5)

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def update_progress(self, current):
        self.progress_label.config(text=f"Progression : {current}/{self.total_queries}")

    def load_file(self):
        self.input_file = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if self.input_file:
            self.log(f"Fichier chargé : {self.input_file}")
        else:
            self.log("Aucun fichier sélectionné.")

    def start_scraping(self):
        if not self.input_file:
            self.log("Veuillez d'abord charger un fichier CSV.")
            return

        self.output_file = self.output_entry.get().strip()
        if not self.output_file:
            self.log("Veuillez entrer un nom pour le fichier de sortie.")
            return

        if not self.output_file.endswith(".csv"):
            self.output_file += ".csv"

        threading.Thread(target=self.scrape).start()

    def stop_scraping(self):
        self.scraper.stop_requested = True
        self.log("Arrêt demandé.")

    def scrape(self):
        data = pd.read_csv(self.input_file, header=None, names=["domain"])
        self.total_queries = len(data)

        try:
            for idx, row in enumerate(data.iterrows(), start=1):
                if self.scraper.stop_requested:
                    self.log("Traitement interrompu par l'utilisateur.")
                    break

                domain = row[1]["domain"]
                self.log(f"Traitement {idx}/{self.total_queries} : {domain}")
                result = self.scraper.search_and_extract(self.driver, domain, self.log)
                self.results.append({"domain": domain, "outlook_server": result})

                # Mise à jour de la progression
                self.update_progress(idx)

                # Sauvegarde partielle après chaque itération
                pd.DataFrame(self.results).to_csv(self.output_file, index=False)

        except Exception as e:
            self.log(f"Erreur imprévue : {e}")
            self.log("Sauvegarde des résultats partiels avant arrêt...")
            pd.DataFrame(self.results).to_csv(self.output_file, index=False)
        finally:
            self.driver.quit()
            self.log(f"Résultats sauvegardés dans {self.output_file}")

# === MAIN ===
if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperApp(root)
    root.mainloop()
