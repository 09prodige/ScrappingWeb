import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading
import requests
import time
import re
from bs4 import BeautifulSoup

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
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-insecure-localhost")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--unsafely-treat-insecure-origin-as-secure=http://www.whois-raynette.fr")
    return webdriver.Chrome(options=options)

def check_internet_connection(log, retry_interval=5):
    while True:
        try:
            requests.get("http://www.google.com", timeout=3)
            return True
        except requests.ConnectionError:
            log("Connexion Internet interrompue. Réessai dans quelques secondes...")
            time.sleep(retry_interval)

class MailServerScraper:
    def __init__(self):
        self.stop_requested = False
        self.pause_requested = False

    def is_microsoft_server(self, text):
        patterns = [
            r"outlook", r"office365", r"microsoft",
            r"msn", r"hotmail", r"exchange",
            r"mail\\.protection\\.outlook\\.com"
        ]
        return any(re.search(pat, text.lower()) for pat in patterns)

    def categorize_server(self, servers):
        for s in servers:
            s = s.lower()
            if self.is_microsoft_server(s):
                return "OUI"
            elif re.match(r"^mx\\d*\\.", s):
                return "NON"
        return "NON DÉFINI"

    def search_and_extract(self, driver, domain, log):
        if self.stop_requested:
            return "Interrompu", []

        while self.pause_requested:
            time.sleep(0.2)

        if domain.strip().lower() == "aucun site" or domain.strip() == "":
            return "aucun", []

        check_internet_connection(log)

        try:
            url = f"http://www.whois-raynette.fr/whois/{domain}"
            driver.get(url)
            log(f"Consultation de Whois pour : {domain}")

            rows = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//table[contains(@class, 'whois_section_content')]/tbody/tr")
                )
            )

            mail_servers = []
            for row in rows:
                try:
                    label = row.find_element(By.XPATH, ".//td[1]/strong").text.strip()
                    if "Serveur(s) mail" in label:
                        td_element = row.find_element(By.XPATH, ".//td[2]")
                        inner_html = td_element.get_attribute("innerHTML")
                        soup = BeautifulSoup(inner_html, "html.parser")
                        lines = [line.strip() for line in soup.stripped_strings]

                        mail_servers = [
                            re.sub(r"\\(.*\\)", "", l).strip('" ').strip()
                            for l in lines if l
                        ]
                        break
                except Exception as e:
                    log(f"Erreur lecture ligne serveur mail : {e}")
                    continue

            category = self.categorize_server(mail_servers) if mail_servers else "aucun"
            log(f"{domain} → {category} → {mail_servers}")
            return category, mail_servers

        except Exception as e:
            log(f"Erreur Whois pour {domain} : {e}")
            return "Erreur", []

class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Scraper Serveur Mail Outlook")
        self.scraper = MailServerScraper()
        self.driver = configure_driver()
        self.results = []
        self.total_queries = 0
        self.setup_ui()

    def setup_ui(self):
        self.root.configure(bg="#f0f2f5")
        frame = tk.Frame(self.root, bg="#f0f2f5", padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        tk.Button(frame, text="📁 Charger CSV", command=self.load_file, bg="#007ACC", fg="white").grid(row=0, column=0, sticky="w", pady=5)
        tk.Label(frame, text="Nom fichier sortie :", bg="#f0f2f5").grid(row=1, column=0, sticky="w")
        self.output_entry = tk.Entry(frame, width=40)
        self.output_entry.grid(row=1, column=1, sticky="w", pady=5)

        tk.Button(frame, text="▶️ Démarrer", command=self.start_scraping, bg="#28a745", fg="white").grid(row=2, column=0, pady=5, sticky="w")
        tk.Button(frame, text="⏹ Arrêter", command=self.stop_scraping, bg="#dc3545", fg="white").grid(row=2, column=1, pady=5, sticky="w")
        tk.Button(frame, text="⏸ Pause / ▶️ Reprendre", command=self.toggle_pause, bg="#ffc107", fg="black").grid(row=3, column=0, columnspan=2, pady=5)

        self.progress_label = tk.Label(frame, text="Progression : 0/0", bg="#f0f2f5")
        self.progress_label.grid(row=4, column=0, columnspan=2, pady=5)

        self.log_area = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=80, height=20, font=("Courier", 10))
        self.log_area.grid(row=5, column=0, columnspan=2, pady=5)

    def log(self, msg):
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)

    def update_progress(self, current):
        self.progress_label.config(text=f"Progression : {current}/{self.total_queries}")

    def load_file(self):
        self.input_file = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        self.log(f"Fichier sélectionné : {self.input_file}")

    def toggle_pause(self):
        self.scraper.pause_requested = not self.scraper.pause_requested
        state = "Pause" if self.scraper.pause_requested else "Reprise"
        self.log(f"{state} activée.")

    def stop_scraping(self):
        self.scraper.stop_requested = True
        self.log("Scraping interrompu.")

    def start_scraping(self):
        self.output_file = self.output_entry.get().strip()
        if not self.output_file.endswith(".csv"):
            self.output_file += ".csv"

        threading.Thread(target=self.scrape).start()

    def scrape(self):
        data = pd.read_csv(self.input_file, header=None, names=["domain"])
        self.total_queries = len(data)

        try:
            try:
                done_df = pd.read_csv(self.output_file)
                done_domains = set(done_df['domain'])
                self.results = done_df.to_dict(orient="records")
            except FileNotFoundError:
                done_domains = set()
                self.results = []

            for idx, row in enumerate(data.iterrows(), start=1):
                domain = row[1]["domain"]
                if domain in done_domains:
                    continue

                if self.scraper.stop_requested:
                    break
                while self.scraper.pause_requested:
                    time.sleep(1)

                self.log(f"[{idx}/{self.total_queries}] {domain}")
                result, servers = self.scraper.search_and_extract(self.driver, domain, self.log)

                result_record = {
                    "domain": domain,
                    "outlook_server": result,
                }
                for i, srv in enumerate(servers):
                    result_record[f"mail_server_{i+1}"] = srv

                self.results.append(result_record)
                self.update_progress(idx)
                pd.DataFrame(self.results).to_csv(self.output_file, index=False)

        except Exception as e:
            self.log(f"Erreur générale : {e}")
        finally:
            self.driver.quit()
            self.log(f"Scraping terminé. Résultats : {self.output_file}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperApp(root)
    root.mainloop()
