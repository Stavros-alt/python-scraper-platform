import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
from bs4 import BeautifulSoup

CONFIG_FILE = 'configs.json'

def perform_scrape(url, selector):
    """Takes a URL and a CSS selector, returns a list of scraped text items."""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        elements = soup.select(selector)
        
        return [elem.get_text(strip=True) for elem in elements]
    except requests.exceptions.RequestException as e:
        return [f"Network Error: {e}"]
    except Exception as e:
        return [f"An error occurred: {e}"]

class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Scraper Configurator v1.0")
        self.root.geometry("900x700")
        self.configs = {}

        style = ttk.Style()
        style.theme_use('clam')

        paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(paned_window, width=250, height=400)
        paned_window.add(left_frame, weight=1)

        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=3)

        ttk.Label(left_frame, text="Saved Jobs", font=('Arial', 12, 'bold')).pack(pady=5)
        self.job_listbox = tk.Listbox(left_frame, exportselection=False)
        self.job_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.job_listbox.bind('<<ListboxSelect>>', self.on_job_select)

        details_frame = ttk.LabelFrame(right_frame, text="Job Details", padding=10)
        details_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(details_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.name_entry = ttk.Entry(details_frame, width=50)
        self.name_entry.grid(row=0, column=1, sticky=tk.EW, pady=2)

        ttk.Label(details_frame, text="URL:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.url_entry = ttk.Entry(details_frame, width=50)
        self.url_entry.grid(row=1, column=1, sticky=tk.EW, pady=2)

        ttk.Label(details_frame, text="CSS Selector:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.selector_entry = ttk.Entry(details_frame, width=50)
        self.selector_entry.grid(row=2, column=1, sticky=tk.EW, pady=2)
        
        details_frame.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, padx=10)
        ttk.Button(btn_frame, text="New", command=self.new_job).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save", command=self.save_job).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_job).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(right_frame, text="RUN SCRAPE", command=self.run_scrape, style="Accent.TButton").pack(pady=10)
        style.configure("Accent.TButton", font=('Arial', 12, 'bold'), background="#0984e3")

        results_frame = ttk.LabelFrame(right_frame, text="Scraped Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD)
        self.results_text.pack(fill=tk.BOTH, expand=True)

        self.load_configs()

    def load_configs(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                self.configs = json.load(f)
        self.update_job_listbox()

    def save_configs(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.configs, f, indent=4)

    def update_job_listbox(self):
        self.job_listbox.delete(0, tk.END)
        for job_name in sorted(self.configs.keys()):
            self.job_listbox.insert(tk.END, job_name)

    def on_job_select(self, event):
        selection_indices = self.job_listbox.curselection()
        if not selection_indices:
            return
        
        job_name = self.job_listbox.get(selection_indices[0])
        config = self.configs.get(job_name, {})
        
        self.clear_entries()
        self.name_entry.insert(0, job_name)
        self.url_entry.insert(0, config.get('url', ''))
        self.selector_entry.insert(0, config.get('selector', ''))

    def clear_entries(self):
        self.name_entry.delete(0, tk.END)
        self.url_entry.delete(0, tk.END)
        self.selector_entry.delete(0, tk.END)

    def new_job(self):
        self.clear_entries()
        self.job_listbox.selection_clear(0, tk.END)

    def save_job(self):
        job_name = self.name_entry.get().strip()
        url = self.url_entry.get().strip()
        selector = self.selector_entry.get().strip()

        if not all([job_name, url, selector]):
            messagebox.showerror("Error", "Name, URL, and Selector cannot be empty.")
            return

        self.configs[job_name] = {'url': url, 'selector': selector}
        self.save_configs()
        self.update_job_listbox()
        messagebox.showinfo("Success", f"Job '{job_name}' saved successfully.")

    def delete_job(self):
        job_name = self.name_entry.get().strip()
        if not job_name:
            messagebox.showerror("Error", "No job selected to delete.")
            return

        if job_name in self.configs:
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the job '{job_name}'?"):
                del self.configs[job_name]
                self.save_configs()
                self.update_job_listbox()
                self.clear_entries()
                messagebox.showinfo("Success", f"Job '{job_name}' deleted.")
        else:
            messagebox.showerror("Error", "Job not found in saved configs.")

    def run_scrape(self):
        url = self.url_entry.get().strip()
        selector = self.selector_entry.get().strip()

        if not all([url, selector]):
            messagebox.showerror("Error", "URL and Selector must be filled out to run a scrape.")
            return
        
        self.results_text.delete('1.0', tk.END)
        self.results_text.insert(tk.END, "Scraping, please wait...")
        self.root.update_idletasks()

        results = perform_scrape(url, selector)

        self.results_text.delete('1.0', tk.END)
        if results:
            self.results_text.insert(tk.END, "\n".join(results))
        else:
            self.results_text.insert(tk.END, "No elements found with the given selector.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperApp(root)
    root.mainloop()