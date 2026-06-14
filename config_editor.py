#!/usr/bin/env python3
"""
FABIAN.OS // Site Editor
========================
Bearbeitet die "simple" Seite (travel.json inkl. Foto-Mapping, config.json,
music.json, badges.json, watchlist.csv) UND die Desktop-Config
(data/config.json) mit allen Features aus dem Web-Admin-Dashboard:
Profil, Discord, Intel, Operations, Watchlist, Custom Windows,
Apps & Layout, Autostart, Papierkorb, Appearance (OS-Identität, Themes,
themeBg, Hintergrund), Ladescreen, Clippy, versteckte Ordner, Custom Themes.

NICHT übernommen (nicht sinnvoll portierbar):
- Security/Passwort (liegt im Browser-localStorage)
- Datei-Upload/BG-Galerie (benötigt api.php — Bilder manuell kopieren)
- "Export index.html" (weiterhin im Web-Admin nutzen)

Themes: Windows 7 (Aero) / Windows 10 Dark — umschaltbar oben rechts.
Optionale Pakete: geopy (Geocoding), Pillow (Bildvorschau).
"""

import os, sys, json, csv, time, shutil, subprocess
import tkinter as tk
from tkinter import ttk, messagebox

try:
    from geopy.geocoders import Nominatim
    GEOPY_OK = True
except ImportError:
    GEOPY_OK = False

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

# --------------------------------------------------------------------------
# PFADE
# --------------------------------------------------------------------------
DATA_DIR      = os.path.join("data", "config")
TRAVEL_JSON   = os.path.join(DATA_DIR, "travel.json")
CONFIG_JSON   = os.path.join(DATA_DIR, "config.json")     # simple-Seite
MUSIC_JSON    = os.path.join(DATA_DIR, "music.json")
BADGES_JSON   = os.path.join(DATA_DIR, "badges.json")
WATCHLIST_CSV = os.path.join(DATA_DIR, "watchlist.csv")
DESKTOP_JSON  = CONFIG_JSON     # Desktop/Admin-Config
TRAVEL_IMG    = os.path.join("data", "files", "Travel")
VALID_EXT     = (".jpg", ".jpeg", ".png", ".webp", ".gif")
WL_HEADERS    = ["title", "status", "type", "imdb", "ep"]
SETTINGS_PATH = "editor_settings.json"

# Standard-Fenster des Desktop-OS (für Apps/Autostart)
DT_WINDOWS = [("profile", "Operator File"), ("intel", "Intel File"),
              ("links", "Operations"), ("watch", "Watch List"),
              ("fileexplorer", "File Explorer"), ("settings", "Settings"),
              ("recyclebin", "Papierkorb"), ("texteditor", "Text Viewer")]

# --------------------------------------------------------------------------
# THEMES: Windows 7 (Aero) & Windows 10 Dark
# --------------------------------------------------------------------------
THEMES = {
    "Windows 7": dict(
        bg="#dfe9f5", panel="#cfe0f0", field="#ffffff", fg="#1e1e1e",
        teal="#15428b", rust="#aa3a3a", blue="#3399ff",
        muted="#5a6b7d", line="#a8c0dc"),
    "Windows 10 Dark": dict(
        bg="#1f1f1f", panel="#2b2b2b", field="#333333", fg="#ffffff",
        teal="#0078d7", rust="#c50f1f", blue="#0078d7",
        muted="#a0a0a0", line="#454545"),
}
BTN_THEMES = {
    "Windows 7": {
        "teal": dict(bg="#f2f6fb", border="#8e9cad", hover="#eaf6fd", fg="#1e1e1e"),
        "blue": dict(bg="#eaf6fd", border="#3c7fb1", hover="#bee6fd", fg="#1e1e1e"),
        "rust": dict(bg="#fcecec", border="#c98989", hover="#f5d5d5", fg="#1e1e1e")},
    "Windows 10 Dark": {
        "teal": dict(bg="#333333", border="#9a9a9a", hover="#454545", fg="#ffffff"),
        "blue": dict(bg="#0078d7", border="#0078d7", hover="#1a86dc", fg="#ffffff"),
        "rust": dict(bg="#3a2323", border="#c50f1f", hover="#5a2a2a", fg="#ffffff")},
}

def load_settings():
    """Lädt die Editor-Einstellungen (z. B. gewähltes Theme)."""
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_settings(s):
    """Speichert die Editor-Einstellungen."""
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2)
    except Exception:
        pass

SETTINGS = load_settings()
THEME = SETTINGS.get("theme", "Windows 7")
if THEME not in THEMES:
    THEME = "Windows 7"
C   = dict(THEMES[THEME])
BTN = BTN_THEMES[THEME]

FONT_UI   = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 9, "bold")
FONT_HEAD = ("Segoe UI", 11, "bold")

# --------------------------------------------------------------------------
# DATEI-HELFER
# --------------------------------------------------------------------------
def backup(path):
    """Legt vor dem Speichern ein .bak-Backup der Datei an."""
    if os.path.exists(path):
        try: shutil.copy2(path, path + ".bak")
        except Exception: pass

def load_json(path, fallback):
    """Lädt eine JSON-Datei; bei Fehler wird der Fallback zurückgegeben."""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            messagebox.showerror("Fehler", f"{path} nicht lesbar:\n{e}")
    return fallback

def save_json(path, data):
    """Speichert JSON (mit Backup). Gibt True bei Erfolg zurück."""
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        backup(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        messagebox.showerror("Fehler", f"Speichern fehlgeschlagen:\n{e}")
        return False

def open_folder(path):
    """Öffnet einen Ordner im Dateimanager (Windows/Mac/Linux)."""
    os.makedirs(path, exist_ok=True)
    if sys.platform.startswith("win"): os.startfile(path)
    elif sys.platform == "darwin":     subprocess.call(["open", path])
    else:                              subprocess.call(["xdg-open", path])

def B(v):
    """Bool → '1'/'0' für die Tabellen-Darstellung."""
    return "1" if v else "0"

def to_b(s):
    """String → Bool ('1', 'ja', 'true', 'x' = wahr)."""
    return str(s).strip().lower() in ("1", "ja", "true", "x", "yes")

def to_i(s, d=0):
    """String → int mit Fallback."""
    try: return int(str(s).strip())
    except (ValueError, TypeError): return d

# --------------------------------------------------------------------------
# FOTO-MAPPING (integriert, ersetzt build.py)
# --------------------------------------------------------------------------
def scan_city_folder(city):
    """Scannt data/files/Travel/<city>.
    Rückgabe: (globale Bilder, {ordnername: [bilder]})."""
    folder = os.path.join(TRAVEL_IMG, city)
    glob_imgs, trip_map = [], {}
    if not os.path.isdir(folder):
        return glob_imgs, trip_map
    for item in sorted(os.listdir(folder)):
        p = os.path.join(folder, item)
        if os.path.isfile(p) and item.lower().endswith(VALID_EXT):
            glob_imgs.append(f"./data/files/Travel/{city}/{item}")
        elif os.path.isdir(p):
            subs = [f"./data/files/Travel/{city}/{item}/{s}"
                    for s in sorted(os.listdir(p)) if s.lower().endswith(VALID_EXT)]
            trip_map[item] = subs
    return glob_imgs, trip_map

def apply_photo_mapping(places):
    """Gleicht alle Bilder mit travel.json ab (getrimmte Datums-Strings,
    Meldung unzugeordneter Ordner, ergänzt fehlende Keys).
    Rückgabe: (updates, log, {city: [unzugeordnete ordner]})."""
    updates, log, unmatched_all = 0, [], {}
    for place in places:
        city = (place.get("city") or "").strip()
        if not city: continue
        glob_imgs, trip_map = scan_city_folder(city)
        if place.get("images", []) != glob_imgs:
            place["images"] = glob_imgs; updates += 1
            log.append(f"[{city}] {len(glob_imgs)} Ort-Foto(s) aktualisiert")
        place.setdefault("dates", [])
        used = set()
        for trip in place["dates"]:
            frm = (trip.get("from") or "").strip()
            if frm in trip_map:
                used.add(frm)
                if trip.get("images", []) != trip_map[frm]:
                    trip["images"] = trip_map[frm]; updates += 1
                    log.append(f"[{city}] Trip {frm}: {len(trip_map[frm])} Foto(s)")
            else:
                trip.setdefault("images", [])
        rest = [k for k in trip_map if k not in used]
        if rest:
            unmatched_all[city] = rest
            log.append(f"[{city}] ⚠ unzugeordnete Ordner: {', '.join(rest)}")
    return updates, log, unmatched_all

# --------------------------------------------------------------------------
# UI-HELFER (Windows-Look)
# --------------------------------------------------------------------------
def heading(parent, text):
    """Abschnitts-Überschrift im Win-Gruppentitel-Stil."""
    return tk.Label(parent, text=text, bg=C["bg"], fg=C["teal"],
                    font=FONT_HEAD, anchor="w")

def mk_entry(parent):
    """Einheitlich gestyltes Eingabefeld."""
    return tk.Entry(parent, bg=C["field"], fg=C["fg"], bd=0,
                    insertbackground=C["fg"], relief="flat",
                    highlightthickness=1, highlightbackground=C["line"],
                    highlightcolor=C["blue"], font=FONT_UI)

def mk_text(parent, height=6):
    """Einheitlich gestyltes mehrzeiliges Textfeld."""
    return tk.Text(parent, height=height, bg=C["field"], fg=C["fg"],
                   insertbackground=C["fg"], relief="flat", wrap="word", font=FONT_UI)

def mk_btn(parent, text, cmd, kind="teal"):
    """Button im Stil des aktiven Themes (Win7-Aero / Win10-Dark)."""
    cfg = BTN.get(kind, BTN["teal"])
    b = tk.Button(parent, text=text, command=cmd, bg=cfg["bg"], fg=cfg["fg"],
                  font=FONT_UI, relief="raised" if THEME == "Windows 7" else "flat",
                  bd=1, highlightthickness=1, highlightbackground=cfg["border"],
                  activebackground=cfg["hover"], activeforeground=cfg["fg"],
                  padx=12, pady=4, cursor="hand2")
    b.bind("<Enter>", lambda e: b.config(bg=cfg["hover"]))
    b.bind("<Leave>", lambda e: b.config(bg=cfg["bg"]))
    return b

def mk_check(parent, text, var):
    """Themen-konforme Checkbox."""
    return tk.Checkbutton(parent, text=text, variable=var, bg=C["bg"], fg=C["fg"],
                          activebackground=C["bg"], activeforeground=C["fg"],
                          selectcolor=C["field"], font=FONT_UI)

def labeled_entry(parent, text):
    """Label + Entry untereinander; gibt das Entry zurück."""
    tk.Label(parent, text=text, bg=C["bg"], fg=C["muted"],
             font=FONT_UI).pack(anchor="w", pady=(6, 1))
    e = mk_entry(parent); e.pack(fill="x"); return e

def set_entry(e, text):
    """Setzt den Text eines Entry-Felds."""
    e.delete(0, "end"); e.insert(0, "" if text is None else str(text))

def mk_listbox(parent, **kw):
    """Einheitlich gestylte Listbox."""
    return tk.Listbox(parent, bg=C["field"], fg=C["fg"], bd=0,
                      selectbackground=C["blue"], selectforeground="#ffffff",
                      highlightthickness=1, highlightbackground=C["line"], **kw)

def style_app(root):
    """Globales ttk-Theme passend zum gewählten Look."""
    root.option_add("*Font", "{Segoe UI} 9")
    s = ttk.Style(root)
    if THEME == "Windows 7":
        try:
            s.theme_use("vista")
        except tk.TclError:
            s.theme_use("clam")
            s.configure(".", background=C["bg"], foreground=C["fg"],
                        fieldbackground=C["field"])
            s.configure("TNotebook", background=C["bg"], borderwidth=0)
            s.configure("TNotebook.Tab", background="#d9e7f5", foreground=C["fg"],
                        padding=(14, 5), font=FONT_UI)
            s.map("TNotebook.Tab", background=[("selected", "#ffffff")])
    else:
        s.theme_use("clam")
        s.configure(".", background=C["bg"], foreground=C["fg"],
                    fieldbackground=C["field"])
        s.configure("TNotebook", background=C["bg"], borderwidth=0)
        s.configure("TNotebook.Tab", background=C["panel"], foreground=C["muted"],
                    padding=(14, 6), font=FONT_UI)
        s.map("TNotebook.Tab", background=[("selected", C["teal"])],
              foreground=[("selected", "#ffffff")])
        s.configure("TCombobox", fieldbackground=C["field"], background=C["panel"],
                    foreground=C["fg"], arrowcolor=C["fg"])
    s.configure("Treeview", background=C["field"], fieldbackground=C["field"],
                foreground=C["fg"], rowheight=22, font=FONT_UI)
    s.configure("Treeview.Heading", font=FONT_BOLD,
                background=C["panel"], foreground=C["fg"])
    s.map("Treeview", background=[("selected", C["blue"])],
          foreground=[("selected", "#ffffff")])

def aero_banner(parent, title):
    """Win7: Aero-Verlauf · Win10 Dark: flache Leiste mit Akzentlinie."""
    cv = tk.Canvas(parent, height=46, highlightthickness=0, bd=0)
    def draw(_=None):
        cv.delete("all")
        w = max(cv.winfo_width(), 1)
        if THEME == "Windows 7":
            for i in range(46):
                t = i / 46
                r = int(0xa9 + (0xdf - 0xa9) * t)
                g = int(0xc9 + (0xe9 - 0xc9) * t)
                b = int(0xe9 + (0xf5 - 0xe9) * t)
                cv.create_line(0, i, w, i, fill=f"#{r:02x}{g:02x}{b:02x}")
            cv.create_text(14, 23, anchor="w", text=title,
                           font=("Segoe UI", 14), fill="#15428b")
        else:
            cv.create_rectangle(0, 0, w, 46, fill="#1f1f1f", width=0)
            cv.create_rectangle(0, 43, w, 46, fill=C["teal"], width=0)
            cv.create_text(14, 22, anchor="w", text=title,
                           font=("Segoe UI", 14), fill="#ffffff")
    cv.bind("<Configure>", draw)
    return cv

# ==========================================================================
# GENERISCHER LISTEN-EDITOR
# ==========================================================================
class ListEditor(tk.Frame):
    """Treeview + Formular + Hinzufügen/Aktualisieren/Verschieben/Löschen.
    columns = [(key, anzeigename, breite), ...]"""
    def __init__(self, parent, columns, on_change=None, height=6):
        super().__init__(parent, bg=C["bg"])
        self.columns, self.on_change, self.entries = columns, on_change, {}
        keys = [c[0] for c in columns]
        self.tree = ttk.Treeview(self, columns=keys, show="headings", height=height)
        for key, name, width in columns:
            self.tree.heading(key, text=name)
            self.tree.column(key, width=width)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._fill_form)
        form = tk.Frame(self, bg=C["bg"]); form.pack(fill="x", pady=2)
        for key, name, _ in columns:
            self.entries[key] = labeled_entry(form, name)
        btns = tk.Frame(self, bg=C["bg"]); btns.pack(fill="x", pady=4)
        mk_btn(btns, "+ Hinzufügen", self.add).pack(side="left")
        mk_btn(btns, "Aktualisieren", self.update_sel, "blue").pack(side="left", padx=5)
        mk_btn(btns, "↑", lambda: self.move(-1), "blue").pack(side="left", padx=(10, 2))
        mk_btn(btns, "↓", lambda: self.move(1), "blue").pack(side="left")
        mk_btn(btns, "– Löschen", self.delete, "rust").pack(side="right")

    def _fill_form(self, _=None):
        """Übernimmt die gewählte Zeile ins Formular."""
        sel = self.tree.selection()
        if not sel: return
        for key, val in zip(self.entries, self.tree.item(sel[0], "values")):
            set_entry(self.entries[key], val)

    def add(self):
        """Fügt die Formularwerte als neue Zeile hinzu."""
        self.tree.insert("", "end", values=[self.entries[k].get() for k in self.entries])
        if self.on_change: self.on_change()

    def update_sel(self):
        """Überschreibt die gewählte Zeile mit den Formularwerten."""
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Achtung", "Bitte Zeile auswählen!")
        self.tree.item(sel[0], values=[self.entries[k].get() for k in self.entries])
        if self.on_change: self.on_change()

    def delete(self):
        """Löscht die gewählte(n) Zeile(n)."""
        for s in self.tree.selection(): self.tree.delete(s)
        if self.on_change: self.on_change()

    def move(self, d):
        """Verschiebt die gewählte Zeile nach oben/unten (Sortierung)."""
        sel = self.tree.selection()
        if sel:
            self.tree.move(sel[0], "", self.tree.index(sel[0]) + d)
            if self.on_change: self.on_change()

    def set_rows(self, rows):
        """Füllt die Tabelle aus einer Liste von Dicts."""
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert("", "end", values=[r.get(c[0], "") for c in self.columns])

    def get_rows(self):
        """Liest alle Zeilen als Liste von Dicts aus."""
        return [dict(zip([c[0] for c in self.columns],
                         [str(v) for v in self.tree.item(i, "values")]))
                for i in self.tree.get_children()]

# ==========================================================================
# TAB 1: TRAVELMAP (Orte, Trips, verbessertes Foto-Mapping)
# ==========================================================================
class TravelTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app, self.places = app, []
        self.sel_place, self.sel_trip = None, None
        self.geolocator = Nominatim(user_agent="fabian_os_editor") if GEOPY_OK else None
        self._build_ui(); self.load()

    def _build_ui(self):
        """3-Spalten-Layout: Orte | Stammdaten | Trips & Fotos."""
        left = tk.Frame(self, bg=C["bg"]); left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        mid  = tk.Frame(self, bg=C["bg"]); mid.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        right= tk.Frame(self, bg=C["bg"]); right.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        heading(left, "// Orte").pack(anchor="w")
        self.lb_places = mk_listbox(left)
        self.lb_places.pack(fill="both", expand=True, pady=4)
        self.lb_places.bind("<<ListboxSelect>>", self.on_place_select)
        bf = tk.Frame(left, bg=C["bg"]); bf.pack(fill="x", pady=4)
        mk_btn(bf, "+ Neu", self.new_place).pack(side="left")
        mk_btn(bf, "– Löschen", self.delete_place, "rust").pack(side="left", padx=5)
        mk_btn(left, "🔄 Foto-Mapping ausführen", self.run_mapping, "blue").pack(fill="x", pady=(8, 0))

        heading(mid, "// Ort-Stammdaten").pack(anchor="w")
        self.e_city    = labeled_entry(mid, "Stadt (city):")
        self.e_country = labeled_entry(mid, "Land (country):")
        self.e_addr    = labeled_entry(mid, "Geocoding-Suche (Adresse):")
        mk_btn(mid, "🔍 Koordinaten suchen", self.geocode, "blue").pack(anchor="e", pady=3)
        self.e_lat  = labeled_entry(mid, "Breitengrad (lat):")
        self.e_lon  = labeled_entry(mid, "Längengrad (lon):")
        tk.Label(mid, text="Status:", bg=C["bg"], fg=C["muted"], font=FONT_UI).pack(anchor="w", pady=(6, 1))
        self.cb_status = ttk.Combobox(mid, values=["visited", "want", "home"], state="readonly")
        self.cb_status.pack(fill="x"); self.cb_status.set("visited")
        self.e_note  = labeled_entry(mid, "Notiz (note):")
        self.e_cap   = labeled_entry(mid, "Bild-Caption (picturecaption):")
        self.e_count = labeled_entry(mid, "Anzahl Besuche (count):")
        mk_btn(mid, "💾 Ort speichern", self.save_place).pack(fill="x", pady=(12, 0))

        heading(right, "// Trips").pack(anchor="w")
        self.lb_trips = mk_listbox(right, height=5)
        self.lb_trips.pack(fill="x", pady=4)
        self.lb_trips.bind("<<ListboxSelect>>", self.on_trip_select)
        tf = tk.Frame(right, bg=C["bg"]); tf.pack(fill="x")
        mk_btn(tf, "+ Trip", self.add_trip, "blue").pack(side="left")
        mk_btn(tf, "– Trip", self.delete_trip, "rust").pack(side="left", padx=5)
        self.e_from = labeled_entry(right, "Von (from), z. B. 15.05.2024:")
        self.e_to   = labeled_entry(right, "Bis (to, optional):")
        self.e_com  = labeled_entry(right, "Kommentar (comment):")
        mk_btn(right, "Trip aktualisieren", self.update_trip, "blue").pack(fill="x", pady=4)

        heading(right, "// Fotos").pack(anchor="w", pady=(10, 0))
        self.lbl_imginfo = tk.Label(right, text="—", bg=C["bg"], fg=C["muted"],
                                    anchor="w", font=FONT_UI)
        self.lbl_imginfo.pack(fill="x")
        self.lb_imgs = mk_listbox(right, height=5)
        self.lb_imgs.pack(fill="both", expand=True, pady=4)
        self.lb_imgs.bind("<<ListboxSelect>>", self.preview_image)
        self.lbl_preview = tk.Label(right, bg=C["field"]); self.lbl_preview.pack(pady=2)
        pf = tk.Frame(right, bg=C["bg"]); pf.pack(fill="x", pady=4)
        mk_btn(pf, "📂 Ordner öffnen", self.open_city_folder, "blue").pack(side="left")
        mk_btn(pf, "📁 Trip-Ordner anlegen", self.make_trip_folder, "blue").pack(side="left", padx=5)
        uf = tk.Frame(right, bg=C["bg"]); uf.pack(fill="x", pady=2)
        tk.Label(uf, text="Unzugeordneter Ordner:", bg=C["bg"], fg=C["rust"],
                 font=FONT_UI).pack(anchor="w")
        self.cb_unmatched = ttk.Combobox(uf, state="readonly"); self.cb_unmatched.pack(fill="x")
        mk_btn(uf, "→ gewähltem Trip zuordnen (umbenennen)", self.assign_folder, "rust").pack(fill="x", pady=3)

    def load(self):
        """Lädt travel.json und füllt die Ortsliste."""
        self.places = load_json(TRAVEL_JSON, [])
        self.lb_places.delete(0, "end")
        for p in self.places:
            t = p.get("city", "?") + (f" ({p['country']})" if p.get("country") else "")
            self.lb_places.insert("end", t)

    def on_place_select(self, _=None):
        """Übernimmt den gewählten Ort ins Formular."""
        sel = self.lb_places.curselection()
        if not sel: return
        self.sel_place = sel[0]; p = self.places[sel[0]]
        for e, k in [(self.e_city,"city"),(self.e_country,"country"),(self.e_lat,"lat"),
                     (self.e_lon,"lon"),(self.e_note,"note"),(self.e_cap,"picturecaption"),
                     (self.e_count,"count")]:
            set_entry(e, p.get(k, ""))
        set_entry(self.e_addr, f"{p.get('city','')} {p.get('country','')}".strip())
        self.cb_status.set(p.get("status", "visited"))
        self.refresh_trips(); self.refresh_photos()

    def refresh_trips(self):
        """Aktualisiert die Trip-Liste des gewählten Orts."""
        self.lb_trips.delete(0, "end"); self.sel_trip = None
        if self.sel_place is None: return
        for t in self.places[self.sel_place].get("dates", []):
            txt = f"// {t.get('from','??')}" + (f" bis {t['to']}" if t.get("to") else "")
            txt += f" — {len(t.get('images', []))} Foto(s)"
            if t.get("comment"): txt += f" · {t['comment']}"
            self.lb_trips.insert("end", txt)

    def on_trip_select(self, _=None):
        """Übernimmt den gewählten Trip ins Formular."""
        sel = self.lb_trips.curselection()
        if not sel: return
        self.sel_trip = sel[0]
        t = self.places[self.sel_place]["dates"][sel[0]]
        set_entry(self.e_from, t.get("from","")); set_entry(self.e_to, t.get("to",""))
        set_entry(self.e_com, t.get("comment","")); self.refresh_photos()

    def refresh_photos(self):
        """Zeigt Fotos (Ort/Trip) und unzugeordnete Ordner an."""
        self.lb_imgs.delete(0, "end"); self.lbl_preview.config(image="", text="")
        if self.sel_place is None: return
        p = self.places[self.sel_place]
        if self.sel_trip is not None:
            imgs = p["dates"][self.sel_trip].get("images", [])
            self.lbl_imginfo.config(text=f"Trip-Fotos: {len(imgs)}")
        else:
            imgs = p.get("images", [])
            self.lbl_imginfo.config(text=f"Ort-Fotos (ohne Trip): {len(imgs)}")
        for i in imgs: self.lb_imgs.insert("end", os.path.basename(i))
        self._imgs_full = imgs
        _, trip_map = scan_city_folder(p.get("city", ""))
        used = {(t.get("from") or "").strip() for t in p.get("dates", [])}
        rest = [k for k in trip_map if k not in used]
        self.cb_unmatched["values"] = rest
        self.cb_unmatched.set(rest[0] if rest else "")

    def preview_image(self, _=None):
        """Kleine Bildvorschau des gewählten Fotos (benötigt Pillow)."""
        if not PIL_OK: return
        sel = self.lb_imgs.curselection()
        if not sel: return
        path = self._imgs_full[sel[0]].lstrip("./")
        try:
            img = Image.open(path); img.thumbnail((220, 150))
            self._tkimg = ImageTk.PhotoImage(img)
            self.lbl_preview.config(image=self._tkimg)
        except Exception:
            self.lbl_preview.config(image="", text="(Vorschau fehlgeschlagen)", fg=C["muted"])

    def geocode(self):
        """Sucht Koordinaten zur Adresse (benötigt geopy)."""
        if not GEOPY_OK:
            return messagebox.showwarning("Fehlt", "geopy ist nicht installiert:\npip install geopy")
        addr = self.e_addr.get().strip()
        if not addr: return messagebox.showwarning("Achtung", "Bitte Adresse eingeben!")
        try:
            loc = self.geolocator.geocode(addr)
            if loc:
                set_entry(self.e_lat, f"{loc.latitude:.5f}")
                set_entry(self.e_lon, f"{loc.longitude:.5f}")
            else:
                messagebox.showwarning("Nicht gefunden", "Keine Koordinaten gefunden.")
        except Exception as e:
            messagebox.showerror("API-Fehler", str(e))

    def new_place(self):
        """Leert das Formular für einen neuen Ort."""
        self.sel_place = None; self.lb_places.selection_clear(0, "end")
        for e in (self.e_city, self.e_country, self.e_lat, self.e_lon,
                  self.e_note, self.e_cap, self.e_count, self.e_addr): set_entry(e, "")
        self.cb_status.set("visited"); self.refresh_trips(); self.refresh_photos()

    def save_place(self):
        """Speichert die Stammdaten des Orts in travel.json."""
        city = self.e_city.get().strip()
        if not city: return messagebox.showwarning("Fehler", "Stadt ist Pflicht!")
        try:
            lat, lon = float(self.e_lat.get()), float(self.e_lon.get())
        except ValueError:
            return messagebox.showwarning("Fehler", "lat/lon müssen Zahlen sein!")
        data = dict(city=city, country=self.e_country.get().strip(), lat=lat, lon=lon,
                    status=self.cb_status.get(), note=self.e_note.get().strip(),
                    count=self.e_count.get().strip(), picturecaption=self.e_cap.get().strip())
        if self.sel_place is not None:
            old = self.places[self.sel_place]
            data["dates"], data["images"] = old.get("dates", []), old.get("images", [])
            self.places[self.sel_place] = data
        else:
            data["dates"], data["images"] = [], []
            self.places.append(data)
        if save_json(TRAVEL_JSON, self.places):
            self.load(); self.app.status("Ort gespeichert ✔")

    def delete_place(self):
        """Löscht den gewählten Ort."""
        if self.sel_place is None: return
        if messagebox.askyesno("Löschen", "Ort samt Trips löschen?"):
            self.places.pop(self.sel_place)
            save_json(TRAVEL_JSON, self.places); self.new_place(); self.load()

    def add_trip(self):
        """Legt einen neuen Trip am gewählten Ort an."""
        if self.sel_place is None: return messagebox.showwarning("Achtung", "Erst Ort wählen!")
        self.places[self.sel_place].setdefault("dates", []).append(
            {"from": "01.01.2026", "to": "", "comment": "Neuer Trip", "images": []})
        save_json(TRAVEL_JSON, self.places); self.refresh_trips()

    def update_trip(self):
        """Speichert die Formularwerte in den gewählten Trip."""
        if self.sel_place is None or self.sel_trip is None:
            return messagebox.showwarning("Achtung", "Erst Ort + Trip wählen!")
        frm = self.e_from.get().strip()
        if not frm: return messagebox.showwarning("Fehler", "'Von'-Datum ist Pflicht!")
        t = self.places[self.sel_place]["dates"][self.sel_trip]
        t.update({"from": frm, "to": self.e_to.get().strip(),
                  "comment": self.e_com.get().strip()})
        save_json(TRAVEL_JSON, self.places); self.refresh_trips()

    def delete_trip(self):
        """Löscht den gewählten Trip."""
        if self.sel_place is None or self.sel_trip is None: return
        if messagebox.askyesno("Löschen", "Trip wirklich löschen?"):
            self.places[self.sel_place]["dates"].pop(self.sel_trip)
            save_json(TRAVEL_JSON, self.places); self.refresh_trips(); self.refresh_photos()

    def open_city_folder(self):
        """Öffnet den Foto-Ordner des Orts im Dateimanager."""
        if self.sel_place is None: return
        open_folder(os.path.join(TRAVEL_IMG, self.places[self.sel_place].get("city", "")))

    def make_trip_folder(self):
        """Legt den passenden Unterordner für den gewählten Trip an."""
        if self.sel_place is None or self.sel_trip is None:
            return messagebox.showwarning("Achtung", "Erst Ort + Trip wählen!")
        city = self.places[self.sel_place]["city"]
        frm = self.places[self.sel_place]["dates"][self.sel_trip].get("from", "").strip()
        open_folder(os.path.join(TRAVEL_IMG, city, frm))

    def assign_folder(self):
        """Benennt einen unzugeordneten Ordner auf das 'from'-Datum
        des gewählten Trips um, damit das Mapping ihn findet."""
        if self.sel_place is None or self.sel_trip is None:
            return messagebox.showwarning("Achtung", "Erst Ort + Trip wählen!")
        folder = self.cb_unmatched.get()
        if not folder: return messagebox.showwarning("Achtung", "Kein Ordner gewählt!")
        city = self.places[self.sel_place]["city"]
        frm = self.places[self.sel_place]["dates"][self.sel_trip].get("from", "").strip()
        src = os.path.join(TRAVEL_IMG, city, folder)
        dst = os.path.join(TRAVEL_IMG, city, frm)
        if os.path.exists(dst):
            return messagebox.showerror("Fehler", f"Zielordner '{frm}' existiert bereits!")
        try:
            os.rename(src, dst); self.run_mapping()
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def run_mapping(self):
        """Führt das integrierte Foto-Mapping aus und zeigt das Ergebnis."""
        updates, log, _ = apply_photo_mapping(self.places)
        save_json(TRAVEL_JSON, self.places)
        self.refresh_trips(); self.refresh_photos()
        messagebox.showinfo("Foto-Mapping",
                            f"{updates} Änderung(en).\n\n" + ("\n".join(log) if log else "Alles aktuell."))
        self.app.status(f"Foto-Mapping: {updates} Update(s) ✔")

# ==========================================================================
# TAB 2: CONFIG.JSON der simple-Seite (Profil + Links)
# ==========================================================================
class ConfigTab(tk.Frame):
    FIELDS = [("operatorName","Name (operatorName):"), ("operatorRole","Rolle (operatorRole):"),
              ("discordName","Discord-Name:"), ("discordId","Discord-ID:"),
              ("discordUrl","Discord-URL:"), ("profilePicture","Profilbild-Pfad:")]

    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"]); self.app = app
        left = tk.Frame(self, bg=C["bg"]); left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        right= tk.Frame(self, bg=C["bg"]); right.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        heading(left, "// Profil (simple-Seite)").pack(anchor="w")
        self.entries = {k: labeled_entry(left, lbl) for k, lbl in self.FIELDS}
        tk.Label(left, text="About-Text (aboutHtml):", bg=C["bg"], fg=C["muted"],
                 font=FONT_UI).pack(anchor="w", pady=(8,1))
        self.txt_about = mk_text(left, 6); self.txt_about.pack(fill="both", expand=True)
        heading(right, "// Links (where to find me)").pack(anchor="w")
        self.links = ListEditor(right, [("title","Titel",120),("url","URL",220),("sub","Anzeigetext (sub)",140)])
        self.links.pack(fill="both", expand=True)
        mk_btn(self, "💾 config.json (simple) speichern", self.save).pack(side="bottom", fill="x", padx=8, pady=8)
        self.load()

    def load(self):
        """Lädt data/config/config.json (unbekannte Keys bleiben erhalten)."""
        self.data = load_json(CONFIG_JSON, {})
        for k, _ in self.FIELDS: set_entry(self.entries[k], self.data.get(k, ""))
        self.txt_about.delete("1.0", "end"); self.txt_about.insert("1.0", self.data.get("aboutHtml", ""))
        self.links.set_rows(self.data.get("links", []))

    def save(self):
        """Speichert das Formular zurück."""
        for k, _ in self.FIELDS: self.data[k] = self.entries[k].get().strip()
        self.data["aboutHtml"] = self.txt_about.get("1.0", "end").strip()
        self.data["links"] = self.links.get_rows()
        if save_json(CONFIG_JSON, self.data): self.app.status("config.json (simple) gespeichert ✔")

# ==========================================================================
# TAB 3: MUSIC.JSON
# ==========================================================================
class MusicTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"]); self.app = app
        f = tk.Frame(self, bg=C["bg"]); f.pack(fill="both", expand=True, padx=8, pady=8)
        heading(f, "// music.json").pack(anchor="w")
        tk.Label(f, text="Intro-Text (introText):", bg=C["bg"], fg=C["muted"],
                 font=FONT_UI).pack(anchor="w", pady=(6,1))
        self.txt_intro = mk_text(f, 3); self.txt_intro.pack(fill="x")
        self.e_fav = labeled_entry(f, "Favoriten-Playlist-ID (favoritesPlaylistId, PL...):")
        heading(f, "// Playlists").pack(anchor="w", pady=(10, 0))
        self.pl = ListEditor(f, [("name","Name",140),("id","Playlist-ID (PL...)",240),("note","Notiz",160)])
        self.pl.pack(fill="both", expand=True)
        mk_btn(f, "💾 music.json speichern", self.save).pack(fill="x", pady=8)
        self.load()

    def load(self):
        """Lädt music.json ins Formular."""
        self.data = load_json(MUSIC_JSON, {})
        self.txt_intro.delete("1.0", "end"); self.txt_intro.insert("1.0", self.data.get("introText", ""))
        set_entry(self.e_fav, self.data.get("favoritesPlaylistId", ""))
        self.pl.set_rows(self.data.get("playlists", []))

    def save(self):
        """Speichert das Formular zurück nach music.json."""
        self.data["introText"] = self.txt_intro.get("1.0", "end").strip()
        self.data["favoritesPlaylistId"] = self.e_fav.get().strip()
        self.data["playlists"] = self.pl.get_rows()
        if save_json(MUSIC_JSON, self.data): self.app.status("music.json gespeichert ✔")

# ==========================================================================
# TAB 4: BADGES.JSON (88x31-Buttons der simple-Seite)
# ==========================================================================
class BadgesTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"]); self.app = app
        f = tk.Frame(self, bg=C["bg"]); f.pack(fill="both", expand=True, padx=8, pady=8)
        heading(f, "// badges.json (88×31)").pack(anchor="w")
        self.ed = ListEditor(f, [("img","Bild-URL/Pfad",240),("url","Link-URL",240),("alt","Alt-Text",120)])
        self.ed.pack(fill="both", expand=True)
        mk_btn(f, "💾 badges.json speichern", self.save).pack(fill="x", pady=8)
        self.ed.set_rows(load_json(BADGES_JSON, []))

    def save(self):
        """Speichert die Badge-Liste nach badges.json."""
        if save_json(BADGES_JSON, self.ed.get_rows()): self.app.status("badges.json gespeichert ✔")

# ==========================================================================
# TAB 5: WATCHLIST.CSV (simple-Seite)
# ==========================================================================
class WatchlistTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"]); self.app = app
        f = tk.Frame(self, bg=C["bg"]); f.pack(fill="both", expand=True, padx=8, pady=8)
        heading(f, "// watchlist.csv  (status: watching | completed | planning | dropped)").pack(anchor="w")
        self.headers = self._read_headers()
        self.ed = ListEditor(f, [(h, h, 130) for h in self.headers])
        self.ed.pack(fill="both", expand=True)
        mk_btn(f, "💾 watchlist.csv speichern", self.save).pack(fill="x", pady=8)
        self.load()

    def _read_headers(self):
        """Liest die Kopfzeile der CSV (Fallback: Standard-Spalten)."""
        try:
            with open(WATCHLIST_CSV, encoding="utf-8") as fh:
                first = fh.readline().strip()
                if first: return [h.strip() for h in first.split(";")]
        except FileNotFoundError: pass
        return WL_HEADERS

    def load(self):
        """Lädt alle CSV-Zeilen in die Tabelle."""
        rows = []
        try:
            with open(WATCHLIST_CSV, encoding="utf-8") as fh:
                rdr = csv.DictReader(fh, delimiter=";")
                rows = [{k: (v or "").strip() for k, v in r.items()} for r in rdr]
        except FileNotFoundError: pass
        self.ed.set_rows(rows)

    def save(self):
        """Schreibt die Tabelle zurück in die CSV (mit Backup)."""
        try:
            backup(WATCHLIST_CSV)
            with open(WATCHLIST_CSV, "w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=self.headers, delimiter=";")
                w.writeheader()
                for r in self.ed.get_rows(): w.writerow(r)
            self.app.status("watchlist.csv gespeichert ✔")
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

# ==========================================================================
# TAB 6: DESKTOP — alle Admin-Dashboard-Features (data/config.json)
# ==========================================================================
class DesktopTab(tk.Frame):
    """Editor für die Desktop-Config (data/config.json) mit allen Features
    aus dem Web-Admin: Profil, Discord, Intel, Operations, Watchlist,
    Custom Windows, Apps & Layout, Autostart, Papierkorb, Appearance,
    Ladescreen, Clippy, versteckte Ordner, Custom Themes."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app, self.cfg = app, {}
        self.fillers, self.collectors = [], []
        bar = tk.Frame(self, bg=C["bg"]); bar.pack(fill="x", padx=8, pady=6)
        heading(bar, "// Desktop-Config (data/config/config.json)").pack(side="left")
        mk_btn(bar, "💾 Alles speichern", self.save).pack(side="right")
        mk_btn(bar, "↻ Neu laden", self.load, "blue").pack(side="right", padx=6)
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._build_profile(); self._build_intel(); self._build_badges()
        self._build_links(); self._build_watch(); self._build_windows()
        self._build_apps(); self._build_autostart(); self._build_bin()
        self._build_appearance(); self._build_system(); self._build_clippy()
        self.load()

    # ---------------- Infrastruktur ----------------
    def _sub(self, title):
        """Erzeugt einen Unter-Tab und gibt dessen Frame zurück."""
        f = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(f, text=f" {title} ")
        return f

    def _all_win_ids(self):
        """Alle bekannten Fenster-IDs (Standard + Custom Windows)."""
        ids = [w[0] for w in DT_WINDOWS]
        for w in self.cfg.get("customWindows") or []:
            if w.get("id") and w["id"] not in ids:
                ids.append(w["id"])
        return ids

    def load(self):
        """Lädt data/config.json und füllt alle Unter-Tabs."""
        self.cfg = load_json(DESKTOP_JSON, {})
        for fn in self.fillers: fn()
        self.app.status("Desktop-Config geladen ✔")

    def save(self):
        """Speichert: frischer Dateistand + Werte aus den Formularen."""
        self.cfg = load_json(DESKTOP_JSON, {})   # aktuellen Stand als Basis
        try:
            for fn in self.collectors: fn()      # Collectors schreiben in self.cfg
        except Exception as ex:
            return messagebox.showerror("Eingabe ungültig", str(ex))
        if save_json(DESKTOP_JSON, self.cfg):
            self.app.status("config.json gespeichert ✔ (.bak angelegt)")

    # ---------------- Profil (inkl. Discord) ----------------
    def _build_profile(self):
        """Profil: Stammdaten, Discord, Name-Größe/Layout, Meta-Felder, Stat-Boxen."""
        f = self._sub("👤 Profil")
        left = tk.Frame(f, bg=C["bg"]); left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        right= tk.Frame(f, bg=C["bg"]); right.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        heading(left, "// Stammdaten & Discord").pack(anchor="w")
        e = {}
        for k, lbl in [("operatorName","Name (operatorName):"),
                       ("operatorRole","Rolle (operatorRole):"),
                       ("profilePicture","Profilbild-Pfad/URL:"),
                       ("discordId","Discord-ID (Lanyard):"),
                       ("discordName","Discord Fallback-Name:"),
                       ("discordUrl","Discord-Profil-URL:"),
                       ("nsFirst","Vorname-Größe px (nameSize.first):"),
                       ("nsLast","Nachname-Größe px (nameSize.last):"),
                       ("profileLayout","Ebenen (profileLayout: avatar,badges,text,stats):")]:
            e[k] = labeled_entry(left, lbl)
        self.dt_prof = e
        heading(right, "// Meta-Felder (Aktiv 1 = hervorgehoben)").pack(anchor="w")
        self.dt_meta = ListEditor(right, [("label","Label",110),("value","Wert",160),("hl","Aktiv (0/1)",70)], height=4)
        self.dt_meta.pack(fill="x")
        heading(right, "// Stat-Boxen").pack(anchor="w", pady=(8, 0))
        self.dt_stats = ListEditor(right, [("label","Label",140),("value","Wert",140)], height=4)
        self.dt_stats.pack(fill="x")

        def fill():
            c = self.cfg
            for k in ("operatorName","operatorRole","profilePicture",
                      "discordId","discordName","discordUrl"):
                set_entry(e[k], c.get(k, ""))
            ns = c.get("nameSize") or {}
            set_entry(e["nsFirst"], ns.get("first", 38))
            set_entry(e["nsLast"],  ns.get("last", 38))
            set_entry(e["profileLayout"], ",".join(c.get("profileLayout") or
                                                   ["avatar","badges","text","stats"]))
            self.dt_meta.set_rows([{"label": m.get("label",""), "value": m.get("value",""),
                                    "hl": B(m.get("hl"))} for m in c.get("profileMeta") or []])
            self.dt_stats.set_rows(c.get("stats") or [])

        def collect():
            c = self.cfg
            for k in ("operatorName","operatorRole","profilePicture",
                      "discordId","discordName","discordUrl"):
                c[k] = e[k].get().strip()
            c["nameSize"] = {"first": to_i(e["nsFirst"].get(), 38),
                             "last":  to_i(e["nsLast"].get(), 38)}
            c["profileLayout"] = [s.strip() for s in e["profileLayout"].get().split(",") if s.strip()]
            c["profileMeta"] = [{"label": r["label"], "value": r["value"], "hl": to_b(r["hl"])}
                                for r in self.dt_meta.get_rows()]
            c["stats"] = [{"label": r["label"], "value": r["value"]}
                          for r in self.dt_stats.get_rows()]
        self.fillers.append(fill); self.collectors.append(collect)

    # ---------------- Intel ----------------
    def _build_intel(self):
        """Intel File: About-Text (HTML), Abschnitts-Titel, Ebenen-Reihenfolge."""
        f = self._sub("◉ Intel")
        box = tk.Frame(f, bg=C["bg"]); box.pack(fill="both", expand=True, padx=8, pady=8)
        heading(box, "// About-Text (aboutHtml — <span> = Akzent, <br><br> = Absatz)").pack(anchor="w")
        self.dt_about = mk_text(box, 8); self.dt_about.pack(fill="both", expand=True, pady=4)
        self.dt_it_bg   = labeled_entry(box, "Abschnitts-Titel 'Background' (intelTitles.background):")
        self.dt_it_spec = labeled_entry(box, "Abschnitts-Titel 'Specializations' (intelTitles.specializations):")
        self.dt_ilayout = labeled_entry(box, "Ebenen-Reihenfolge (intelLayout: text,badges):")

        def fill():
            c = self.cfg
            self.dt_about.delete("1.0", "end"); self.dt_about.insert("1.0", c.get("aboutHtml", ""))
            it = c.get("intelTitles") or {}
            set_entry(self.dt_it_bg,   it.get("background", "BACKGROUND"))
            set_entry(self.dt_it_spec, it.get("specializations", "SPECIALIZATIONS"))
            set_entry(self.dt_ilayout, ",".join(c.get("intelLayout") or ["text","badges"]))

        def collect():
            c = self.cfg
            c["aboutHtml"] = self.dt_about.get("1.0", "end").strip()
            c["intelTitles"] = {"background": self.dt_it_bg.get().strip() or "BACKGROUND",
                                "specializations": self.dt_it_spec.get().strip() or "SPECIALIZATIONS"}
            c["intelLayout"] = [s.strip() for s in self.dt_ilayout.get().split(",") if s.strip()]
        self.fillers.append(fill); self.collectors.append(collect)

    # ---------------- Badges (Profil + Intel) ----------------
    def _build_badges(self):
        """Badges: Profil-Badges & Spezialisierungs-Badges.
        Farbe (t): o=Orange c=Cyan g=Grün p=Lila r=Rot y=Gold."""
        f = self._sub("🏷 Badges")
        left = tk.Frame(f, bg=C["bg"]); left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        right= tk.Frame(f, bg=C["bg"]); right.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        heading(left, "// Profil-Badges (t: o/c/g/p/r/y)").pack(anchor="w")
        self.dt_pb = ListEditor(left, [("l","Name",160),("t","Farbe (o/c/g/p/r/y)",110)])
        self.dt_pb.pack(fill="both", expand=True)
        heading(right, "// Spezialisierungs-Badges (Intel)").pack(anchor="w")
        self.dt_ib = ListEditor(right, [("l","Name",160),("t","Farbe (o/c/g/p/r/y)",110)])
        self.dt_ib.pack(fill="both", expand=True)

        def fill():
            self.dt_pb.set_rows(self.cfg.get("profileBadges") or [])
            self.dt_ib.set_rows(self.cfg.get("intelBadges") or [])

        def collect():
            self.cfg["profileBadges"] = [{"l": r["l"], "t": r["t"] or "o"}
                                         for r in self.dt_pb.get_rows() if r["l"]]
            self.cfg["intelBadges"] = [{"l": r["l"], "t": r["t"] or "o"}
                                       for r in self.dt_ib.get_rows() if r["l"]]
        self.fillers.append(fill); self.collectors.append(collect)

    # ---------------- Operations / Links ----------------
    def _build_links(self):
        """Operations-Links: code, Titel, Untertitel, URL, Icon, Discord-Status.
        Icons: github, linkedin, instagram, discord, email, link."""
        f = self._sub("▷ Operations")
        box = tk.Frame(f, bg=C["bg"]); box.pack(fill="both", expand=True, padx=8, pady=8)
        heading(box, "// Links (dcStatus 1 = zeigt Discord-Status)").pack(anchor="w")
        self.dt_links = ListEditor(box, [("code","Code",70),("title","Titel",110),
                                         ("sub","Untertitel",140),("url","URL",220),
                                         ("icon","Icon",90),("dcStatus","DC (0/1)",60)], height=10)
        self.dt_links.pack(fill="both", expand=True)

        def fill():
            self.dt_links.set_rows([{**l, "dcStatus": B(l.get("dcStatus"))}
                                    for l in self.cfg.get("links") or []])

        def collect():
            self.cfg["links"] = [{"code": r["code"], "title": r["title"], "sub": r["sub"],
                                  "url": r["url"], "icon": r["icon"] or "link",
                                  "dcStatus": to_b(r["dcStatus"])}
                                 for r in self.dt_links.get_rows() if r["title"]]
        self.fillers.append(fill); self.collectors.append(collect)

    # ---------------- Watch List (Desktop) ----------------
    def _build_watch(self):
        """Watch List des Desktops (Status: watching/completed/planning/dropped)."""
        f = self._sub("◇ Watchlist")
        box = tk.Frame(f, bg=C["bg"]); box.pack(fill="both", expand=True, padx=8, pady=8)
        heading(box, "// Typ: Anime/Serie/Film/OVA · Status: watching/completed/planning/dropped").pack(anchor="w")
        self.dt_wl = ListEditor(box, [("title","Titel",200),("type","Typ",90),
                                      ("status","Status",110),("ep","Folgen",90)], height=10)
        self.dt_wl.pack(fill="both", expand=True)

        def fill():
            self.dt_wl.set_rows(self.cfg.get("watchlist") or [])

        def collect():
            self.cfg["watchlist"] = [r for r in self.dt_wl.get_rows() if r["title"]]
        self.fillers.append(fill); self.collectors.append(collect)

    # ---------------- Custom Windows ----------------
    def _build_windows(self):
        """Custom Windows. Typen: info, image, gallery, text.
        'content' wird als JSON-String gepflegt, z. B.:
        info:    {"subtitle":"...","text":"...","image":null,"badges":[]}
        image:   {"src":"./pfad.jpg","caption":"..."}
        gallery: {"images":["./a.jpg","./b.jpg"]}
        text:    {"text":"..."}"""
        f = self._sub("⊞ Fenster")
        box = tk.Frame(f, bg=C["bg"]); box.pack(fill="both", expand=True, padx=8, pady=8)
        heading(box, "// Custom Windows (content = JSON, leere id wird generiert)").pack(anchor="w")
        self.dt_cw = ListEditor(box, [("id","ID",90),("title","Titel",110),
                                      ("subtitle","Untertitel",110),("type","Typ",70),
                                      ("icon","Icon",50),("initW","Breite",60),
                                      ("showStartMenu","Menü (0/1)",70),
                                      ("showDesktopIcon","Desktop (0/1)",80),
                                      ("content","Content (JSON)",260)], height=8)
        self.dt_cw.pack(fill="both", expand=True)

        def fill():
            rows = []
            for w in self.cfg.get("customWindows") or []:
                rows.append({"id": w.get("id",""), "title": w.get("title",""),
                             "subtitle": w.get("subtitle",""), "type": w.get("type","info"),
                             "icon": w.get("icon","◆"), "initW": w.get("initW",420),
                             "showStartMenu": B(w.get("showStartMenu")),
                             "showDesktopIcon": B(w.get("showDesktopIcon")),
                             "content": json.dumps(w.get("content") or {}, ensure_ascii=False)})
            self.dt_cw.set_rows(rows)

        def collect():
            wins = []
            for n, r in enumerate(self.dt_cw.get_rows()):
                if not r["title"]: continue
                try:
                    content = json.loads(r["content"]) if r["content"].strip() else {}
                except Exception as ex:
                    raise ValueError(f"Custom Window '{r['title']}': Content-JSON ungültig ({ex})")
                wins.append({"id": r["id"].strip() or f"cw_{int(time.time()*1000)}_{n}",
                             "title": r["title"], "subtitle": r["subtitle"],
                             "type": r["type"] or "info", "icon": r["icon"] or "◆",
                             "initW": to_i(r["initW"], 420),
                             "showStartMenu": to_b(r["showStartMenu"]),
                             "showDesktopIcon": to_b(r["showDesktopIcon"]),
                             "content": content})
            self.cfg["customWindows"] = wins
        self.fillers.append(fill); self.collectors.append(collect)

    # ---------------- Apps & Layout ----------------
    def _build_apps(self):
        """Sichtbarkeit pro App (Menü/Desktop/Versteckt/Mobil) sowie
        Rahmenlos/Fixiert für Custom Windows."""
        f = self._sub("▦ Apps")
        left = tk.Frame(f, bg=C["bg"]); left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        right= tk.Frame(f, bg=C["bg"]); right.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        heading(left, "// Sichtbarkeit (appVisibility)").pack(anchor="w")
        self.dt_av = ListEditor(left, [("id","Fenster-ID",110),("menu","Menü (0/1)",70),
                                       ("desktop","Desktop (0/1)",80),("hidden","Versteckt (0/1)",90),
                                       ("mobil","Mobil (0/1)",70)], height=10)
        self.dt_av.pack(fill="both", expand=True)
        heading(right, "// Custom-Fenster: Rahmenlos & Fixiert").pack(anchor="w")
        self.dt_ff = ListEditor(right, [("id","Fenster-ID",110),("rahmenlos","Rahmenlos (0/1)",100),
                                        ("fixiert","Fixiert (0/1)",90)], height=10)
        self.dt_ff.pack(fill="both", expand=True)

        def fill():
            av = self.cfg.get("appVisibility") or {}
            rows = []
            for i in self._all_win_ids():
                v = av.get(i, {})
                rows.append({"id": i, "menu": B(v.get("menu", True)),
                             "desktop": B(v.get("desktop")), "hidden": B(v.get("hidden")),
                             "mobil": B(v.get("mobile", True))})
            self.dt_av.set_rows(rows)
            fl = self.cfg.get("frameless") or {}; fp = self.cfg.get("fixedPos") or {}
            cw = [w.get("id") for w in self.cfg.get("customWindows") or [] if w.get("id")]
            self.dt_ff.set_rows([{"id": i, "rahmenlos": B(fl.get(i)), "fixiert": B(fp.get(i))}
                                 for i in cw])

        def collect():
            self.cfg["appVisibility"] = {
                r["id"]: {"menu": to_b(r["menu"]), "desktop": to_b(r["desktop"]),
                          "hidden": to_b(r["hidden"]), "mobile": to_b(r["mobil"])}
                for r in self.dt_av.get_rows() if r["id"]}
            fl, fp = {}, {}
            for r in self.dt_ff.get_rows():
                if r["id"]:
                    fl[r["id"]] = to_b(r["rahmenlos"]); fp[r["id"]] = to_b(r["fixiert"])
            self.cfg["frameless"] = fl; self.cfg["fixedPos"] = fp
        self.fillers.append(fill); self.collectors.append(collect)

    # ---------------- Autostart ----------------
    def _build_autostart(self):
        """Autostart-Fenster mit Startposition (x/y/Breite) und Layer
        (1 = ganz vorne, leer = egal)."""
        f = self._sub("▶ Autostart")
        box = tk.Frame(f, bg=C["bg"]); box.pack(fill="both", expand=True, padx=8, pady=8)
        heading(box, "// Aktiv 1 = startet automatisch · Layer 1 = vorne").pack(anchor="w")
        self.dt_as = ListEditor(box, [("id","Fenster-ID",120),("aktiv","Aktiv (0/1)",70),
                                      ("x","X (px)",60),("y","Y (px)",60),
                                      ("w","Breite (px)",80),("layer","Layer",60)], height=10)
        self.dt_as.pack(fill="both", expand=True)

        def fill():
            on = self.cfg.get("autostart") or []
            pos = self.cfg.get("autostartPos") or {}
            lay = self.cfg.get("windowLayers") or {}
            rows = []
            for i in self._all_win_ids():
                p = pos.get(i, {})
                rows.append({"id": i, "aktiv": B(i in on),
                             "x": p.get("x", 100), "y": p.get("y", 60),
                             "w": p.get("w", 440), "layer": lay.get(i, "")})
            self.dt_as.set_rows(rows)

        def collect():
            on, pos, lay = [], {}, {}
            for r in self.dt_as.get_rows():
                if not r["id"]: continue
                if to_b(r["aktiv"]): on.append(r["id"])
                pos[r["id"]] = {"x": to_i(r["x"], 100), "y": to_i(r["y"], 60),
                                "w": to_i(r["w"], 440)}
                z = to_i(r["layer"], 0)
                if z: lay[r["id"]] = z
            self.cfg["autostart"] = on
            self.cfg["autostartPos"] = pos
            self.cfg["windowLayers"] = lay
        self.fillers.append(fill); self.collectors.append(collect)

    # ---------------- Papierkorb ----------------
    def _build_bin(self):
        """Papierkorb: virtuelle Textdateien (name, content, date)."""
        f = self._sub("⌦ Papierkorb")
        left = tk.Frame(f, bg=C["bg"]); left.pack(side="left", fill="y", padx=8, pady=8)
        right= tk.Frame(f, bg=C["bg"]); right.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        heading(left, "// Dateien").pack(anchor="w")
        self.rb_lb = mk_listbox(left, width=30)
        self.rb_lb.pack(fill="both", expand=True, pady=4)
        self.rb_lb.bind("<<ListboxSelect>>", self._rb_select)
        bf = tk.Frame(left, bg=C["bg"]); bf.pack(fill="x")
        mk_btn(bf, "+ Neu", self._rb_new).pack(side="left")
        mk_btn(bf, "– Löschen", self._rb_del, "rust").pack(side="left", padx=5)
        heading(right, "// Inhalt").pack(anchor="w")
        self.rb_name = labeled_entry(right, "Dateiname (z. B. notizen.txt):")
        tk.Label(right, text="Inhalt:", bg=C["bg"], fg=C["muted"], font=FONT_UI).pack(anchor="w", pady=(6,1))
        self.rb_txt = mk_text(right, 12); self.rb_txt.pack(fill="both", expand=True)
        mk_btn(right, "Übernehmen (in Liste)", self._rb_apply, "blue").pack(anchor="e", pady=6)
        self.rb_items, self.rb_sel = [], None

        def fill():
            self.rb_items = [dict(x) for x in self.cfg.get("recycleBin") or []]
            self._rb_refresh()

        def collect():
            self.cfg["recycleBin"] = self.rb_items
        self.fillers.append(fill); self.collectors.append(collect)

    def _rb_refresh(self):
        """Aktualisiert die Papierkorb-Liste."""
        self.rb_lb.delete(0, "end"); self.rb_sel = None
        for it in self.rb_items:
            self.rb_lb.insert("end", f"{it.get('name','?')}  ({it.get('date','')})")

    def _rb_select(self, _=None):
        """Übernimmt die gewählte Datei ins Formular."""
        sel = self.rb_lb.curselection()
        if not sel: return
        self.rb_sel = sel[0]; it = self.rb_items[sel[0]]
        set_entry(self.rb_name, it.get("name", ""))
        self.rb_txt.delete("1.0", "end"); self.rb_txt.insert("1.0", it.get("content", ""))

    def _rb_new(self):
        """Legt eine neue Papierkorb-Datei an."""
        self.rb_items.append({"name": "neu.txt", "content": "",
                              "date": time.strftime("%d.%m.%Y")})
        self._rb_refresh()

    def _rb_apply(self):
        """Schreibt Name + Inhalt in den gewählten Eintrag."""
        if self.rb_sel is None:
            return messagebox.showwarning("Achtung", "Erst Datei links auswählen!")
        self.rb_items[self.rb_sel]["name"] = self.rb_name.get().strip() or "unbenannt.txt"
        self.rb_items[self.rb_sel]["content"] = self.rb_txt.get("1.0", "end").rstrip("\n")
        self._rb_refresh()

    def _rb_del(self):
        """Löscht den gewählten Papierkorb-Eintrag."""
        if self.rb_sel is None: return
        self.rb_items.pop(self.rb_sel); self._rb_refresh()

    # ---------------- Appearance ----------------
    def _build_appearance(self):
        """Appearance: Theme, OS-Identität, Hintergrundbilder, themeBg."""
        f = self._sub("◑ Appearance")
        left = tk.Frame(f, bg=C["bg"]); left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        right= tk.Frame(f, bg=C["bg"]); right.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        heading(left, "// Theme & OS-Identität").pack(anchor="w")
        tk.Label(left, text="Aktives Theme (dark / gold / yellow / custom-<id>):",
                 bg=C["bg"], fg=C["muted"], font=FONT_UI).pack(anchor="w", pady=(6,1))
        self.dt_theme = ttk.Combobox(left, values=["dark", "gold", "yellow"])
        self.dt_theme.pack(fill="x")
        self.dt_osname = labeled_entry(left, "OS-Name (osName):")
        self.dt_ossub  = labeled_entry(left, "Untertitel (osSub):")
        self.dt_oshl   = labeled_entry(left, "Highlight-Buchstabe (osHighlight, 1 Zeichen):")
        self.dt_bg     = labeled_entry(left, "Hintergrund (bgImage, Pfad/URL — leer = keiner):")
        self.dt_bgdef  = labeled_entry(left, "Standard-Hintergrund (bgImageDefault):")
        tk.Label(left, text="Hinweis: Bilder manuell nach data/files/... kopieren\n"
                            "und hier den Pfad eintragen (Upload braucht api.php).",
                 bg=C["bg"], fg=C["muted"], font=FONT_UI, justify="left").pack(anchor="w", pady=6)
        heading(right, "// Theme-Hintergründe (themeBg: theme → URL)").pack(anchor="w")
        self.dt_tbg = ListEditor(right, [("theme","Theme",100),("url","Hintergrund-URL/Pfad",260)], height=5)
        self.dt_tbg.pack(fill="x")

        def fill():
            c = self.cfg
            self.dt_theme.set(c.get("theme", "dark"))
            set_entry(self.dt_osname, c.get("osName", "FA|BIAN"))
            set_entry(self.dt_ossub,  c.get("osSub", "ENDFIELD OS // v3.0"))
            set_entry(self.dt_oshl,   c.get("osHighlight", "B"))
            set_entry(self.dt_bg,     c.get("bgImage") or "")
            set_entry(self.dt_bgdef,  c.get("bgImageDefault") or "")
            self.dt_tbg.set_rows([{"theme": k, "url": v}
                                  for k, v in (c.get("themeBg") or {}).items()])

        def collect():
            c = self.cfg
            c["theme"] = self.dt_theme.get().strip() or "dark"
            c["osName"] = self.dt_osname.get().strip() or "FA|BIAN"
            c["osSub"] = self.dt_ossub.get().strip()
            c["osHighlight"] = (self.dt_oshl.get().strip() or "B")[0]
            c["bgImage"] = self.dt_bg.get().strip() or None
            c["bgImageDefault"] = self.dt_bgdef.get().strip() or None
            c["themeBg"] = {r["theme"]: r["url"] for r in self.dt_tbg.get_rows()
                            if r["theme"] and r["url"]}
        self.fillers.append(fill); self.collectors.append(collect)

    # ---------------- System (Ladescreen, versteckte Ordner, Custom Themes) ---
    def _build_system(self):
        """Ladescreen, versteckte Ordner und Custom Themes (als JSON)."""
        f = self._sub("◷ System")
        left = tk.Frame(f, bg=C["bg"]); left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        right= tk.Frame(f, bg=C["bg"]); right.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        heading(left, "// Ladescreen").pack(anchor="w")
        self.dt_lden = tk.BooleanVar(value=True)
        mk_check(left, "Ladescreen aktiviert (loadingEnabled)", self.dt_lden).pack(anchor="w", pady=4)
        self.dt_lddur = labeled_entry(left, "Ladezeit in ms (loadingDuration, 1000 = 1 s):")
        self.dt_ldtxt = labeled_entry(left, "Untertitel-Text (loadingText):")
        heading(left, "// Versteckte Ordner (hiddenFolders)").pack(anchor="w", pady=(12, 0))
        self.dt_hidden = ListEditor(left, [("path","Pfad (relativ zu data/files)",260)], height=4)
        self.dt_hidden.pack(fill="x")
        heading(right, "// Custom Themes (customThemes — Roh-JSON-Liste)").pack(anchor="w")
        self.dt_ct = mk_text(right, 18); self.dt_ct.pack(fill="both", expand=True, pady=4)
        tk.Label(right, text="Format wie im Web-Admin-Export: "
                             '[{"id":"t...","name":"...","sub":"...","vars":{"--bg":"#..."}}]',
                 bg=C["bg"], fg=C["muted"], font=FONT_UI, justify="left").pack(anchor="w")

        def fill():
            c = self.cfg
            self.dt_lden.set(c.get("loadingEnabled", True) is not False)
            set_entry(self.dt_lddur, c.get("loadingDuration", 2800))
            set_entry(self.dt_ldtxt, c.get("loadingText", "INITIALIZING DESKTOP"))
            self.dt_hidden.set_rows([{"path": p} for p in c.get("hiddenFolders") or []])
            self.dt_ct.delete("1.0", "end")
            self.dt_ct.insert("1.0", json.dumps(c.get("customThemes") or [],
                                                indent=2, ensure_ascii=False))

        def collect():
            c = self.cfg
            c["loadingEnabled"] = bool(self.dt_lden.get())
            c["loadingDuration"] = to_i(self.dt_lddur.get(), 2800)
            c["loadingText"] = self.dt_ldtxt.get().strip()
            c["hiddenFolders"] = [r["path"] for r in self.dt_hidden.get_rows() if r["path"]]
            txt = self.dt_ct.get("1.0", "end").strip()
            if txt:
                try:
                    data = json.loads(txt)
                except Exception as ex:
                    raise ValueError(f"customThemes-JSON ungültig: {ex}")
                if not isinstance(data, list):
                    raise ValueError("customThemes muss eine JSON-Liste sein!")
                c["customThemes"] = data
            else:
                c["customThemes"] = []
        self.fillers.append(fill); self.collectors.append(collect)

    # ---------------- Clippy ----------------
    def _build_clippy(self):
        """Clippy (Multi): Name, aktiv, Ecke (br/bl/tr/tl), Timer, Bilder."""
        f = self._sub("❖ Clippy")
        box = tk.Frame(f, bg=C["bg"]); box.pack(fill="both", expand=True, padx=8, pady=8)
        heading(box, "// Bilder mit ; trennen · Ecke: br/bl/tr/tl").pack(anchor="w")
        self.dt_cl = ListEditor(box, [("name","Name",100),("enabled","Aktiv (0/1)",70),
                                      ("corner","Ecke",60),("minSec","Min s",60),
                                      ("maxSec","Max s",60),("images","Bilder (mit ; getrennt)",300)],
                                height=8)
        self.dt_cl.pack(fill="both", expand=True)

        def fill():
            rows = []
            for cl in self.cfg.get("clippys") or []:
                rows.append({"name": cl.get("name",""), "enabled": B(cl.get("enabled")),
                             "corner": cl.get("corner","br"), "minSec": cl.get("minSec",45),
                             "maxSec": cl.get("maxSec",120),
                             "images": ";".join(cl.get("images") or [])})
            self.dt_cl.set_rows(rows)
            self._cl_ids = [cl.get("id") for cl in self.cfg.get("clippys") or []]

        def collect():
            out = []
            for n, r in enumerate(self.dt_cl.get_rows()):
                cid = self._cl_ids[n] if n < len(getattr(self, "_cl_ids", [])) else None
                out.append({"id": cid or f"cl{int(time.time()*1000)}{n}",
                            "name": r["name"] or f"Clippy {n+1}",
                            "enabled": to_b(r["enabled"]),
                            "corner": r["corner"] or "br",
                            "minSec": to_i(r["minSec"], 45),
                            "maxSec": to_i(r["maxSec"], 120),
                            "images": [s.strip() for s in r["images"].split(";") if s.strip()]})
            self.cfg["clippys"] = out
        self.fillers.append(fill); self.collectors.append(collect)

# ==========================================================================
# TAB 7: RAW-EDITOR (alle JSONs inkl. Desktop-Config, mit Validierung)
# ==========================================================================
class RawTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"]); self.app = app
        self.current, self.paths = None, []
        left = tk.Frame(self, bg=C["bg"]); left.pack(side="left", fill="y", padx=8, pady=8)
        right= tk.Frame(self, bg=C["bg"]); right.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        heading(left, "// Dateien").pack(anchor="w")
        self.lb = mk_listbox(left, width=28)
        self.lb.pack(fill="both", expand=True, pady=4)
        self.lb.bind("<<ListboxSelect>>", self.open_file)
        mk_btn(left, "↻ Aktualisieren", self.scan, "blue").pack(fill="x")
        heading(right, "// Raw JSON").pack(anchor="w")
        self.txt = tk.Text(right, bg=C["field"], fg=C["fg"], insertbackground=C["fg"],
                           relief="flat", wrap="none", font=("Consolas", 10))
        self.txt.pack(fill="both", expand=True, pady=4)
        bf = tk.Frame(right, bg=C["bg"]); bf.pack(fill="x")
        mk_btn(bf, "✔ Validieren", self.validate, "blue").pack(side="left")
        mk_btn(bf, "💾 Speichern", self.save).pack(side="right")
        self.scan()

    def scan(self):
        """Listet alle JSON-Dateien (data/config/config.json + data/config/*.json)."""
        self.lb.delete(0, "end"); self.paths = []
        if os.path.exists(DESKTOP_JSON):
            self.lb.insert("end", "config.json (Desktop)")
            self.paths.append(DESKTOP_JSON)
        if os.path.isdir(DATA_DIR):
            for fn in sorted(os.listdir(DATA_DIR)):
                if fn.endswith(".json"):
                    self.lb.insert("end", fn)
                    self.paths.append(os.path.join(DATA_DIR, fn))

    def open_file(self, _=None):
        """Lädt die gewählte Datei in den Editor."""
        sel = self.lb.curselection()
        if not sel: return
        self.current = self.paths[sel[0]]
        with open(self.current, encoding="utf-8") as fh:
            self.txt.delete("1.0", "end"); self.txt.insert("1.0", fh.read())
        self.app.status(f"Geöffnet: {self.current}")

    def validate(self):
        """Prüft den Editor-Inhalt auf gültiges JSON."""
        try:
            json.loads(self.txt.get("1.0", "end"))
            messagebox.showinfo("OK", "Gültiges JSON ✔"); return True
        except Exception as e:
            messagebox.showerror("Ungültig", str(e)); return False

    def save(self):
        """Speichert den Editor-Inhalt (nur bei gültigem JSON, mit Backup)."""
        if not self.current: return
        try:
            data = json.loads(self.txt.get("1.0", "end"))
        except Exception as e:
            return messagebox.showerror("Ungültiges JSON", str(e))
        if save_json(self.current, data):
            self.app.status(f"{self.current} gespeichert ✔")

# ==========================================================================
# HAUPTFENSTER
# ==========================================================================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FABIAN.OS – Site Editor")
        self.geometry("1380x860"); self.configure(bg=C["bg"])
        style_app(self)
        aero_banner(self, "FABIAN.OS  ›  Site Editor").pack(fill="x")

        # Theme-Umschalter oben rechts
        tf = tk.Frame(self, bg=C["bg"]); tf.pack(fill="x", padx=8, pady=(4, 0))
        tk.Label(tf, text="Design:", bg=C["bg"], fg=C["muted"],
                 font=FONT_UI).pack(side="right", padx=(0, 4))
        self.cb_theme = ttk.Combobox(tf, values=list(THEMES.keys()),
                                     state="readonly", width=18)
        self.cb_theme.set(THEME); self.cb_theme.pack(side="right")
        self.cb_theme.bind("<<ComboboxSelected>>", self.switch_theme)

        # ── Statusleiste ZUERST anlegen (Tabs rufen status() beim Laden auf!) ──
        bar = tk.Frame(self, bg=C["panel"]); bar.pack(fill="x", side="bottom")
        tk.Frame(bar, bg=C["line"], height=1).pack(fill="x")
        self.lbl_status = tk.Label(bar, text="Bereit", bg=C["panel"], fg=C["muted"],
                                   anchor="w", padx=10, font=FONT_UI)
        self.lbl_status.pack(fill="x")

        # ── Tabs erst danach ──
        nb = ttk.Notebook(self); nb.pack(fill="both", expand=True, padx=6, pady=(6, 0))
        nb.add(DesktopTab(nb, self),   text=" 👤 Config ")
        nb.add(TravelTab(nb, self),    text=" 🗺 Travelmap ")
        nb.add(MusicTab(nb, self),     text=" ♫ Music ")
        nb.add(BadgesTab(nb, self),    text=" 🏷 Badges (simple) ")
        nb.add(WatchlistTab(nb, self), text=" 📺 Watchlist (CSV) ")
        nb.add(RawTab(nb, self),       text=" {} Raw JSON ")

    def status(self, msg):
        """Setzt die Statuszeile am unteren Rand."""
        self.lbl_status.config(text=msg)

    def switch_theme(self, _=None):
        """Speichert das gewählte Theme und startet den Editor neu."""
        choice = self.cb_theme.get()
        if choice == THEME: return
        SETTINGS["theme"] = choice
        save_settings(SETTINGS)
        if messagebox.askyesno("Design wechseln",
                               f"'{choice}' wird beim Neustart übernommen.\nJetzt neu starten?"):
            self.destroy()
            os.execl(sys.executable, sys.executable, *sys.argv)

if __name__ == "__main__":
    App().mainloop()