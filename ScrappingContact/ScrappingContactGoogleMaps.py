import tkinter as tk
from tkinter import filedialog, scrolledtext
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from fuzzywuzzy import fuzz
import re
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
class Scraper:
    def __init__(self):
        self.cookies_accepted = False
        self.stop_requested = False

    def accept_cookies(self, driver, log):
        if not self.cookies_accepted:
            try:
                accept_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Tout accepter']"))
                )
                accept_button.click()
                self.cookies_accepted = True
                log("Cookies acceptés.")
            except TimeoutException:
                log("Le bouton de cookies n'est pas apparu. Peut-être déjà accepté.")
            except Exception as e:
                log(f"Erreur lors de l'acceptation des cookies : {e}")

    def get_best_suggestion_index(self, suggestions, query):
        scores = []
        for s in suggestions:
            full_text = s.text.replace("\n", " ").strip()
            score = fuzz.token_sort_ratio(full_text.lower(), query.lower())
            scores.append((score, full_text))
        if not scores:
            return -1, 0, ""
        best_score, best_text = max(scores, key=lambda x: x[0])
        best_index = [i for i, (s, _) in enumerate(scores) if s == best_score][0]
        return best_index, best_score, best_text

    def search_and_extract(self, driver, query, log):
        if self.stop_requested:
            return "Interrompu", "Interrompu", 0

        check_internet_connection(log)

        try:
            driver.get("https://www.google.com/maps")
            self.accept_cookies(driver, log)
            log(f"Ouverture de Google Maps pour : {query}")

            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "searchboxinput"))
            )
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.ENTER)
            log(f"Recherche effectuée pour : {query}")

            score = 0
            try:
                suggestions = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//div[contains(@class, 'Nv2PK tH5CWc THOPZb')]")
                    )
                )
                if suggestions:
                    best_index, score, best_text = self.get_best_suggestion_index(suggestions, query)
                    if score >= 70:
                        suggestions[best_index].click()
                        log(f"Suggestion sélectionnée : {best_text} (score {score})")
                    else:
                        log(f"Aucune correspondance pertinente pour : {query} (score max {score}). Ignoré.")
                        return "Aucun résultat", "Aucun site", score
            except TimeoutException:
                log(f"Aucune suggestion détectée pour : {query}. Affichage direct du lieu.")

            elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[contains(@class, 'Io6YTe fontBodyMedium kR99db fdkmkc')]")
                )
            )
            phone_number = "Numéro non trouvé"
            website = "Site non trouvé"

            for element in elements:
                text = element.text.strip()
                if re.match(r"^\+?\d[\d\s\-().]{8,}$", text):
                    phone_number = text
                elif re.match(r".+\.(fr|com|org|net|io|info|gov|biz|edu)$", text):
                    website = text

            log(f"Numéro trouvé : {phone_number}")
            log(f"Site web trouvé : {website}")
            return phone_number, website, score

        except Exception as e:
            log(f"Erreur lors de la recherche pour {query} : {e}")
            return "Erreur numéro", "Erreur site", 0

# === INTERFACE TKINTER ===
class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Scraper Google Maps")
        self.scraper = Scraper()
        self.driver = configure_driver()

        self.input_file = None
        self.output_file = None
        self.results = []

        self.setup_ui()

    def setup_ui(self):
        tk.Button(self.root, text="Charger CSV", command=self.load_file).pack(pady=5)

        tk.Label(self.root, text="Nom du fichier de sortie :").pack(pady=5)
        self.output_entry = tk.Entry(self.root, width=40)
        self.output_entry.pack(pady=5)

        tk.Button(self.root, text="Démarrer", command=self.start_scraping).pack(pady=5)
        tk.Button(self.root, text="Arrêter", command=self.stop_scraping).pack(pady=5)

        self.log_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=80, height=20)
        self.log_area.pack(pady=5)

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

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
        data = pd.read_csv(self.input_file, header=None, names=["search_query"], on_bad_lines='skip')
        total_queries = len(data)

        try:
            for idx, row in enumerate(data.iterrows(), start=1):
                if self.scraper.stop_requested:
                    self.log("Traitement interrompu par l'utilisateur.")
                    break

                query = row[1]["search_query"]
                self.log(f"Traitement {idx}/{total_queries} : {query}")
                phone_number, website, score = self.scraper.search_and_extract(self.driver, query, self.log)
                self.results.append({"query": query, "phone_number": phone_number, "website": website, "score": score})
                pd.DataFrame(self.results).to_csv(self.output_file, index=False)

        except Exception as e:
            self.log(f"Erreur imprévue : {e}")
            self.log("Sauvegarde des résultats partiels avant arrêt...")
            pd.DataFrame(self.results).to_csv(self.output_file, index=False)
        finally:
            if self.driver:
                self.driver.quit()
            self.log(f"Résultats sauvegardés dans {self.output_file}")

# === MAIN ===
if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperApp(root)
    root.mainloop()
