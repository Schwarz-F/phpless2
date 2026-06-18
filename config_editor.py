#!/usr/bin/env python3
"""
FABIAN.OS // Site Editor  —  PySide6-Edition (Block 1: Fundament)
=================================================================
Design 1:1 an simple.txt (CSS :root). music-bg via QRadialGradient.
Benötigt:  pip install PySide6
Optional:  pip install geopy pillow
"""

import os, sys, json, csv, time, shutil, subprocess
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QLineEdit, QTextEdit,
    QPushButton, QCheckBox, QComboBox, QTableWidget, QTableWidgetItem,
    QListWidget, QListWidgetItem, QTabWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QScrollArea, QFileDialog, QMessageBox, QHeaderView,
    QAbstractItemView, QSizePolicy, QStatusBar
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QRadialGradient, QColor, QFont, QPixmap

try:
    from geopy.geocoders import Nominatim
    GEOPY_OK = True
except ImportError:
    GEOPY_OK = False

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

# --------------------------------------------------------------------------
# PFADE
# --------------------------------------------------------------------------
DATA_DIR      = os.path.join("data", "config")
TRAVEL_JSON   = os.path.join(DATA_DIR, "travel.json")
CONFIG_JSON   = os.path.join(DATA_DIR, "config.json")
MUSIC_JSON    = os.path.join(DATA_DIR, "music.json")
BADGES_JSON   = os.path.join(DATA_DIR, "badges.json")
WATCHLIST_CSV = os.path.join(DATA_DIR, "watchlist.csv")
DESKTOP_JSON  = CONFIG_JSON
TRAVEL_IMG    = os.path.join("data", "files", "Travel")
VALID_EXT     = (".jpg", ".jpeg", ".png", ".webp", ".gif")
WL_HEADERS    = ["title", "status", "type", "imdb", "ep"]

DT_WINDOWS = [("profile", "Operator File"), ("intel", "Intel File"),
              ("links", "Operations"), ("watch", "Watch List"),
              ("fileexplorer", "File Explorer"), ("settings", "Settings"),
              ("recyclebin", "Papierkorb"), ("texteditor", "Text Viewer")]

# --------------------------------------------------------------------------
# FARBEN  (aus simple.txt :root)
# --------------------------------------------------------------------------
PAPER   = "#0d121f"   # --paper
PAPER2  = "#272d3a"   # --paper2 (opak)
INK     = "#bfdaff"   # --ink
RUST    = "#e08358"   # --rust
MUSTARD = "#2d44c4"   # --mustard
TEAL    = "#4fc7ad"   # --teal
PLUM    = "#c98bb0"   # --plum
LINE    = "#3a3f4b"   # --line
FADED   = "#8a909c"   # --faded
FIELD   = "#080d18"   # input-BG
FONT_FAM = "Courier New"

# --------------------------------------------------------------------------
# QSS-STYLESHEET  (CSS deiner Seite -> Qt)
# --------------------------------------------------------------------------
QSS = f"""
* {{
    font-family: "{FONT_FAM}", "Consolas", monospace;
    font-size: 13px;
    color: {INK};
}}
QMainWindow, QWidget#bgRoot {{ background: transparent; }}

QLabel#heading {{ color: {TEAL}; font-size: 15px; font-weight: bold; }}
QLabel#fieldLabel {{ color: {RUST}; font-size: 10px; font-weight: bold; }}
QLabel#muted {{ color: {FADED}; }}
QLabel#title {{ color: {TEAL}; font-size: 22px; font-weight: bold; }}
QLabel#subtitle {{ color: {RUST}; font-size: 13px; }}

QFrame#card {{
    background: {PAPER2};
    border: 1px solid {LINE};
    border-radius: 8px;
}}

QLineEdit, QTextEdit, QComboBox {{
    background: {FIELD};
    color: {INK};
    border: 1px solid {LINE};
    border-radius: 4px;
    padding: 5px 7px;
    selection-background-color: {MUSTARD};
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{ border: 1px solid {RUST}; }}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background: {FIELD}; color: {INK};
    border: 1px solid {LINE}; selection-background-color: {MUSTARD};
}}

QPushButton {{
    background: transparent;
    color: {TEAL};
    border: 2px solid {TEAL};
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: bold;
}}
QPushButton:hover {{ background: {RUST}; color: {PAPER}; border-color: {RUST}; }}
QPushButton:pressed {{ background: {LINE}; }}
QPushButton[kind="blue"] {{ color: {MUSTARD}; border-color: {MUSTARD}; }}
QPushButton[kind="blue"]:hover {{ background: {RUST}; color: {PAPER}; border-color: {RUST}; }}
QPushButton[kind="rust"] {{ color: {RUST}; border-color: {RUST}; }}
QPushButton[kind="rust"]:hover {{ background: {RUST}; color: {PAPER}; }}

QCheckBox {{ color: {INK}; spacing: 7px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px; border: 1px solid {LINE};
    border-radius: 3px; background: {FIELD};
}}
QCheckBox::indicator:checked {{ background: {TEAL}; border-color: {TEAL}; }}

QTableWidget, QListWidget {{
    background: {FIELD};
    border: 1px solid {LINE};
    border-radius: 4px;
    gridline-color: {LINE};
    outline: none;
}}
QTableWidget::item, QListWidget::item {{ padding: 3px; }}
QTableWidget::item:selected, QListWidget::item:selected {{
    background: {MUSTARD}; color: #ffffff;
}}
QHeaderView::section {{
    background: {PAPER2}; color: {RUST};
    border: none; border-right: 1px solid {LINE}; border-bottom: 1px solid {LINE};
    padding: 5px; font-size: 10px; font-weight: bold;
}}
QTableWidget QTableCornerButton::section {{ background: {PAPER2}; border: none; }}

QTabWidget::pane {{ border: 1px solid {LINE}; border-radius: 6px; background: {PAPER2}; top: -1px; }}
QTabBar::tab {{
    background: {PAPER2}; color: {FADED};
    border: 1px solid {LINE}; border-bottom: none;
    border-top-left-radius: 5px; border-top-right-radius: 5px;
    padding: 7px 14px; margin-right: 2px;
}}
QTabBar::tab:selected {{ background: {MUSTARD}; color: #ffffff; }}
QTabBar::tab:hover:!selected {{ color: {INK}; }}

QScrollArea {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: {PAPER}; width: 12px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {LINE}; border-radius: 6px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {RUST}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollBar:horizontal {{ background: {PAPER}; height: 12px; }}
QScrollBar::handle:horizontal {{ background: {LINE}; border-radius: 6px; min-width: 24px; }}
QScrollBar::handle:horizontal:hover {{ background: {RUST}; }}

QStatusBar {{ background: {PAPER2}; color: {FADED}; border-top: 1px solid {LINE}; }}
QMessageBox {{ background: {PAPER2}; }}
"""

# --------------------------------------------------------------------------
# DATEI-HELFER
# --------------------------------------------------------------------------
def backup(path):
    if os.path.exists(path):
        try: shutil.copy2(path, path + ".bak")
        except Exception: pass

def load_json(path, fallback):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.critical(None, "Fehler", f"{path} nicht lesbar:\n{e}")
    return fallback

def save_json(path, data):
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        backup(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        QMessageBox.critical(None, "Fehler", f"Speichern fehlgeschlagen:\n{e}")
        return False

def open_folder(path):
    os.makedirs(path, exist_ok=True)
    if sys.platform.startswith("win"): os.startfile(path)
    elif sys.platform == "darwin":     subprocess.call(["open", path])
    else:                              subprocess.call(["xdg-open", path])

def B(v):  return "1" if v else "0"
def to_b(s): return str(s).strip().lower() in ("1", "ja", "true", "x", "yes")
def to_i(s, d=0):
    try: return int(str(s).strip())
    except (ValueError, TypeError): return d

# --------------------------------------------------------------------------
# UI-HELFER
# --------------------------------------------------------------------------
def heading(text):
    l = QLabel(text); l.setObjectName("heading"); return l

def field_label(text):
    l = QLabel(text.upper()); l.setObjectName("fieldLabel"); return l

def muted(text):
    l = QLabel(text); l.setObjectName("muted"); return l

def mk_btn(text, cmd, kind="teal"):
    b = QPushButton(text)
    if kind != "teal": b.setProperty("kind", kind)
    b.clicked.connect(cmd); b.setCursor(Qt.PointingHandCursor)
    return b

def card():
    f = QFrame(); f.setObjectName("card"); return f

def labeled_entry(layout, text):
    """Fügt Label + QLineEdit ins Layout ein, gibt das LineEdit zurück."""
    layout.addWidget(field_label(text))
    e = QLineEdit(); layout.addWidget(e); return e

def vbox(parent=None, m=10, s=6):
    l = QVBoxLayout(parent) if parent else QVBoxLayout()
    l.setContentsMargins(m, m, m, m); l.setSpacing(s); return l

def hbox(parent=None, m=0, s=6):
    l = QHBoxLayout(parent) if parent else QHBoxLayout()
    l.setContentsMargins(m, m, m, m); l.setSpacing(s); return l

def scroll_area(inner_widget):
    sa = QScrollArea(); sa.setWidgetResizable(True); sa.setWidget(inner_widget)
    sa.setFrameShape(QFrame.Shape.NoFrame); return sa

# --------------------------------------------------------------------------
# music-bg  —  QRadialGradient (nativ, scharf)
# --------------------------------------------------------------------------
class BackgroundWidget(QWidget):
    """Zeichnet die 4 radialen Verläufe aus body.music-bg."""
    def __init__(self):
        super().__init__()
        self.setObjectName("bgRoot")
        # (x%, y%, farbe, alpha 0-255, radius% von max(w,h))
        self.blobs = [(0.15, 0.20, QColor(RUST),    int(0.22*255), 0.55),
                      (0.85, 0.30, QColor(MUSTARD), int(0.25*255), 0.55),
                      (0.50, 0.85, QColor(TEAL),    int(0.18*255), 0.60),
                      (0.70, 0.60, QColor(PLUM),    int(0.15*255), 0.50)]

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(PAPER))
        m = max(w, h)
        for bx, by, col, a, rad in self.blobs:
            cx, cy, r = bx * w, by * h, rad * m
            g = QRadialGradient(cx, cy, r)
            c0 = QColor(col); c0.setAlpha(a)
            c1 = QColor(col); c1.setAlpha(0)
            g.setColorAt(0.0, c0); g.setColorAt(1.0, c1)
            p.setBrush(g); p.setPen(Qt.NoPen)
            p.drawEllipse(int(cx - r), int(cy - r), int(2 * r), int(2 * r))

# ==========================================================================
# TableEditor  —  Inline-editierbare Tabelle (ersetzt ListEditor)
# ==========================================================================
class TableEditor(QWidget):
    """Editierbare Tabelle mit + Zeile / – Zeile / ↑ / ↓.
    columns = [(key, anzeigename, breite), ...].  API: set_rows/get_rows."""
    def __init__(self, columns, on_change=None):
        super().__init__()
        self.columns = columns
        self.keys = [c[0] for c in columns]
        self.on_change = on_change

        lay = vbox(self, m=0, s=4)
        self.table = QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels([c[1] for c in columns])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        hh = self.table.horizontalHeader()
        for i, (_, _, wdt) in enumerate(columns):
            self.table.setColumnWidth(i, wdt)
        hh.setStretchLastSection(True)
        if self.on_change:
            self.table.itemChanged.connect(lambda *_: self.on_change())
        lay.addWidget(self.table)

        bf = hbox(s=6)
        bf.addWidget(mk_btn("+ Zeile", self.add_row))
        bf.addWidget(mk_btn("– Zeile", self.del_row, "rust"))
        bf.addWidget(mk_btn("↑", lambda: self.move(-1), "blue"))
        bf.addWidget(mk_btn("↓", lambda: self.move(1), "blue"))
        bf.addStretch(1)
        lay.addLayout(bf)

    def add_row(self):
        r = self.table.rowCount(); self.table.insertRow(r)
        for c in range(len(self.columns)):
            self.table.setItem(r, c, QTableWidgetItem(""))
        if self.on_change: self.on_change()

    def del_row(self):
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)
            if self.on_change: self.on_change()

    def move(self, d):
        r = self.table.currentRow(); j = r + d
        if r < 0 or not (0 <= j < self.table.rowCount()): return
        row_a = [self.table.takeItem(r, c) for c in range(self.table.columnCount())]
        row_b = [self.table.takeItem(j, c) for c in range(self.table.columnCount())]
        for c in range(self.table.columnCount()):
            self.table.setItem(j, c, row_a[c]); self.table.setItem(r, c, row_b[c])
        self.table.setCurrentCell(j, 0)
        if self.on_change: self.on_change()

    def set_rows(self, rows):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount(); self.table.insertRow(r)
            for c, key in enumerate(self.keys):
                self.table.setItem(r, c, QTableWidgetItem(str(row.get(key, ""))))
        self.table.blockSignals(False)

    def get_rows(self):
        out = []
        for r in range(self.table.rowCount()):
            row = {}
            for c, key in enumerate(self.keys):
                it = self.table.item(r, c)
                row[key] = it.text() if it else ""
            out.append(row)
        return out
# ==========================================================================
# FOTO-MAPPING
# ==========================================================================
def scan_city_folder(city):
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

# ==========================================================================
# TAB: TRAVELMAP
# ==========================================================================
class TravelTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app, self.places = app, []
        self.sel_place, self.sel_trip = None, None
        self.geolocator = Nominatim(user_agent="fabian_os_editor") if GEOPY_OK else None
        self._build_ui(); self.load()

    def _build_ui(self):
        root = hbox(self, m=8, s=8)

        # -- Spalte 1: Orte --
        c1 = card(); l1 = vbox(c1)
        l1.addWidget(heading("// ORTE"))
        self.lb_places = QListWidget()
        self.lb_places.currentRowChanged.connect(self.on_place_select)
        l1.addWidget(self.lb_places, 1)
        bf = hbox()
        bf.addWidget(mk_btn("+ Neu", self.new_place))
        bf.addWidget(mk_btn("– Löschen", self.delete_place, "rust"))
        bf.addStretch(1); l1.addLayout(bf)
        l1.addWidget(mk_btn("🔄 Foto-Mapping", self.run_mapping, "blue"))
        root.addWidget(c1, 1)

        # -- Spalte 2: Stammdaten (scrollbar) --
        c2 = card(); l2 = vbox(c2)
        inner2 = QWidget(); f2 = vbox(inner2, m=0)
        f2.addWidget(heading("// ORT-STAMMDATEN"))
        self.e_city    = labeled_entry(f2, "Stadt (city):")
        self.e_country = labeled_entry(f2, "Land (country):")
        self.e_addr    = labeled_entry(f2, "Geocoding-Suche (Adresse):")
        f2.addWidget(mk_btn("🔍 Koordinaten suchen", self.geocode, "blue"))
        self.e_lat = labeled_entry(f2, "Breitengrad (lat):")
        self.e_lon = labeled_entry(f2, "Längengrad (lon):")
        f2.addWidget(field_label("Status:"))
        self.cb_status = QComboBox(); self.cb_status.addItems(["visited", "want", "home"])
        f2.addWidget(self.cb_status)
        self.e_note  = labeled_entry(f2, "Notiz (note):")
        self.e_cap   = labeled_entry(f2, "Bild-Caption (picturecaption):")
        self.e_count = labeled_entry(f2, "Anzahl Besuche (count):")
        self.e_trip  = labeled_entry(f2, "Reise-Gruppe (trip), z. B. 'USA 2025':")
        self.e_route = labeled_entry(f2, "Verbindung zu (routeTo, ; getrennt):")
        f2.addWidget(mk_btn("💾 Ort speichern", self.save_place))
        f2.addStretch(1)
        l2.addWidget(scroll_area(inner2))
        root.addWidget(c2, 1)

        # -- Spalte 3: Trips + Fotos (scrollbar) --
        c3 = card(); l3 = vbox(c3)
        inner3 = QWidget(); f3 = vbox(inner3, m=0)
        f3.addWidget(heading("// TRIPS"))
        self.lb_trips = QListWidget()
        self.lb_trips.currentRowChanged.connect(self.on_trip_select)
        self.lb_trips.setMaximumHeight(140)
        f3.addWidget(self.lb_trips)
        tf = hbox()
        tf.addWidget(mk_btn("+ Trip", self.add_trip, "blue"))
        tf.addWidget(mk_btn("– Trip", self.delete_trip, "rust"))
        tf.addStretch(1); f3.addLayout(tf)
        self.e_from = labeled_entry(f3, "Von (from), z. B. 15.05.2024:")
        self.e_to   = labeled_entry(f3, "Bis (to, optional):")
        self.e_com  = labeled_entry(f3, "Kommentar (comment):")
        f3.addWidget(mk_btn("Trip aktualisieren", self.update_trip, "blue"))

        f3.addWidget(heading("// FOTOS"))
        self.lbl_imginfo = muted("—"); f3.addWidget(self.lbl_imginfo)
        self.lb_imgs = QListWidget()
        self.lb_imgs.currentRowChanged.connect(self.preview_image)
        self.lb_imgs.setMaximumHeight(130)
        f3.addWidget(self.lb_imgs)
        self.lbl_preview = QLabel(); self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setMinimumHeight(120)
        f3.addWidget(self.lbl_preview)
        pf = hbox()
        pf.addWidget(mk_btn("📂 Ordner", self.open_city_folder, "blue"))
        pf.addWidget(mk_btn("📁 Trip-Ordner", self.make_trip_folder, "blue"))
        pf.addStretch(1); f3.addLayout(pf)
        f3.addWidget(field_label("Unzugeordneter Ordner:"))
        self.cb_unmatched = QComboBox(); f3.addWidget(self.cb_unmatched)
        f3.addWidget(mk_btn("→ gewähltem Trip zuordnen", self.assign_folder, "rust"))
        f3.addStretch(1)
        l3.addWidget(scroll_area(inner3))
        root.addWidget(c3, 1)

    def load(self):
        self.places = load_json(TRAVEL_JSON, [])
        self.lb_places.blockSignals(True)
        self.lb_places.clear()
        for p in self.places:
            t = p.get("city", "?") + (f" ({p['country']})" if p.get("country") else "")
            if p.get("trip"): t += f"  ⟦{p['trip']}⟧"
            self.lb_places.addItem(t)
        self.lb_places.blockSignals(False)

    def on_place_select(self, row):
        if row < 0 or row >= len(self.places): return
        self.sel_place = row; p = self.places[row]
        for e, k in [(self.e_city,"city"),(self.e_country,"country"),(self.e_lat,"lat"),
                     (self.e_lon,"lon"),(self.e_note,"note"),(self.e_cap,"picturecaption"),
                     (self.e_count,"count"),(self.e_trip,"trip")]:
            e.setText(str(p.get(k, "")))
        self.e_route.setText("; ".join(p.get("routeTo") or []))
        self.e_addr.setText(f"{p.get('city','')} {p.get('country','')}".strip())
        self.cb_status.setCurrentText(p.get("status", "visited"))
        self.refresh_trips(); self.refresh_photos()

    def refresh_trips(self):
        self.lb_trips.blockSignals(True)
        self.lb_trips.clear(); self.sel_trip = None
        if self.sel_place is not None:
            for t in self.places[self.sel_place].get("dates", []):
                txt = f"// {t.get('from','??')}" + (f" bis {t['to']}" if t.get("to") else "")
                txt += f" — {len(t.get('images', []))} Foto(s)"
                if t.get("comment"): txt += f" · {t['comment']}"
                self.lb_trips.addItem(txt)
        self.lb_trips.blockSignals(False)

    def on_trip_select(self, row):
        if self.sel_place is None or row < 0: return
        self.sel_trip = row
        t = self.places[self.sel_place]["dates"][row]
        self.e_from.setText(t.get("from","")); self.e_to.setText(t.get("to",""))
        self.e_com.setText(t.get("comment","")); self.refresh_photos()

    def refresh_photos(self):
        self.lb_imgs.blockSignals(True); self.lb_imgs.clear()
        self.lbl_preview.setPixmap(QPixmap()); self.lbl_preview.setText("")
        if self.sel_place is None:
            self.lb_imgs.blockSignals(False); return
        p = self.places[self.sel_place]
        if self.sel_trip is not None:
            imgs = p["dates"][self.sel_trip].get("images", [])
            self.lbl_imginfo.setText(f"Trip-Fotos: {len(imgs)}")
        else:
            imgs = p.get("images", [])
            self.lbl_imginfo.setText(f"Ort-Fotos (ohne Trip): {len(imgs)}")
        for i in imgs: self.lb_imgs.addItem(os.path.basename(i))
        self._imgs_full = imgs
        self.lb_imgs.blockSignals(False)
        _, trip_map = scan_city_folder(p.get("city", ""))
        used = {(t.get("from") or "").strip() for t in p.get("dates", [])}
        rest = [k for k in trip_map if k not in used]
        self.cb_unmatched.clear(); self.cb_unmatched.addItems(rest)

    def preview_image(self, row):
        if not PIL_OK or row < 0 or row >= len(getattr(self, "_imgs_full", [])): return
        path = self._imgs_full[row].lstrip("./")
        pix = QPixmap(path)
        if not pix.isNull():
            self.lbl_preview.setPixmap(pix.scaled(220, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.lbl_preview.setText("(Vorschau fehlgeschlagen)")

    def geocode(self):
        if not GEOPY_OK:
            return QMessageBox.warning(self, "Fehlt", "geopy nicht installiert:\npip install geopy")
        addr = self.e_addr.text().strip()
        if not addr: return QMessageBox.warning(self, "Achtung", "Bitte Adresse eingeben!")
        try:
            loc = self.geolocator.geocode(addr)
            if loc:
                self.e_lat.setText(f"{loc.latitude:.5f}"); self.e_lon.setText(f"{loc.longitude:.5f}")
            else:
                QMessageBox.warning(self, "Nicht gefunden", "Keine Koordinaten gefunden.")
        except Exception as e:
            QMessageBox.critical(self, "API-Fehler", str(e))

    def new_place(self):
        self.sel_place = None; self.lb_places.setCurrentRow(-1)
        for e in (self.e_city, self.e_country, self.e_lat, self.e_lon, self.e_note,
                  self.e_cap, self.e_count, self.e_addr, self.e_trip, self.e_route):
            e.clear()
        self.cb_status.setCurrentText("visited"); self.refresh_trips(); self.refresh_photos()

    def save_place(self):
        city = self.e_city.text().strip()
        if not city: return QMessageBox.warning(self, "Fehler", "Stadt ist Pflicht!")
        try:
            lat, lon = float(self.e_lat.text()), float(self.e_lon.text())
        except ValueError:
            return QMessageBox.warning(self, "Fehler", "lat/lon müssen Zahlen sein!")
        data = dict(city=city, country=self.e_country.text().strip(), lat=lat, lon=lon,
                    status=self.cb_status.currentText(), note=self.e_note.text().strip(),
                    count=self.e_count.text().strip(), picturecaption=self.e_cap.text().strip(),
                    trip=self.e_trip.text().strip())
        routes = [s.strip() for s in self.e_route.text().split(";") if s.strip()]
        if routes:
            data["routeTo"] = routes

        idx = self.sel_place
        if idx is None:
            for i, p in enumerate(self.places):
                if (p.get("city") or "").strip().lower() == city.lower():
                    idx = i; break
        if idx is not None and 0 <= idx < len(self.places):
            old = self.places[idx]
            data["dates"], data["images"] = old.get("dates", []), old.get("images", [])
            self.places[idx] = data; self.sel_place = idx
        else:
            data["dates"], data["images"] = [], []
            self.places.append(data); self.sel_place = len(self.places) - 1

        if save_json(TRAVEL_JSON, self.places):
            self.load()
            if self.sel_place is not None and self.sel_place < self.lb_places.count():
                self.lb_places.setCurrentRow(self.sel_place)
            self.app.status("Ort gespeichert ✔")

    def delete_place(self):
        if self.sel_place is None: return
        if QMessageBox.question(self, "Löschen", "Ort samt Trips löschen?") == QMessageBox.Yes:
            self.places.pop(self.sel_place)
            save_json(TRAVEL_JSON, self.places); self.new_place(); self.load()

    def add_trip(self):
        if self.sel_place is None: return QMessageBox.warning(self, "Achtung", "Erst Ort wählen!")
        self.places[self.sel_place].setdefault("dates", []).append(
            {"from": "01.01.2026", "to": "", "comment": "Neuer Trip", "images": []})
        save_json(TRAVEL_JSON, self.places); self.refresh_trips()

    def update_trip(self):
        if self.sel_place is None or self.sel_trip is None:
            return QMessageBox.warning(self, "Achtung", "Erst Ort + Trip wählen!")
        frm = self.e_from.text().strip()
        if not frm: return QMessageBox.warning(self, "Fehler", "'Von'-Datum ist Pflicht!")
        t = self.places[self.sel_place]["dates"][self.sel_trip]
        t.update({"from": frm, "to": self.e_to.text().strip(), "comment": self.e_com.text().strip()})
        save_json(TRAVEL_JSON, self.places); self.refresh_trips()

    def delete_trip(self):
        if self.sel_place is None or self.sel_trip is None: return
        if QMessageBox.question(self, "Löschen", "Trip wirklich löschen?") == QMessageBox.Yes:
            self.places[self.sel_place]["dates"].pop(self.sel_trip)
            save_json(TRAVEL_JSON, self.places); self.refresh_trips(); self.refresh_photos()

    def open_city_folder(self):
        if self.sel_place is None: return
        open_folder(os.path.join(TRAVEL_IMG, self.places[self.sel_place].get("city", "")))

    def make_trip_folder(self):
        if self.sel_place is None or self.sel_trip is None:
            return QMessageBox.warning(self, "Achtung", "Erst Ort + Trip wählen!")
        city = self.places[self.sel_place]["city"]
        frm = self.places[self.sel_place]["dates"][self.sel_trip].get("from", "").strip()
        open_folder(os.path.join(TRAVEL_IMG, city, frm))

    def assign_folder(self):
        if self.sel_place is None or self.sel_trip is None:
            return QMessageBox.warning(self, "Achtung", "Erst Ort + Trip wählen!")
        folder = self.cb_unmatched.currentText()
        if not folder: return QMessageBox.warning(self, "Achtung", "Kein Ordner gewählt!")
        city = self.places[self.sel_place]["city"]
        frm = self.places[self.sel_place]["dates"][self.sel_trip].get("from", "").strip()
        src = os.path.join(TRAVEL_IMG, city, folder)
        dst = os.path.join(TRAVEL_IMG, city, frm)
        if os.path.exists(dst):
            return QMessageBox.critical(self, "Fehler", f"Zielordner '{frm}' existiert bereits!")
        try:
            os.rename(src, dst); self.run_mapping()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def run_mapping(self):
        updates, log, _ = apply_photo_mapping(self.places)
        save_json(TRAVEL_JSON, self.places)
        self.refresh_trips(); self.refresh_photos()
        QMessageBox.information(self, "Foto-Mapping",
                                f"{updates} Änderung(en).\n\n" + ("\n".join(log) if log else "Alles aktuell."))
        self.app.status(f"Foto-Mapping: {updates} Update(s) ✔")

# ==========================================================================
# TAB: CONFIG (simple-Seite)
# ==========================================================================
class ConfigTab(QWidget):
    FIELDS = [("operatorName","Name (operatorName):"), ("operatorRole","Rolle (operatorRole):"),
              ("discordName","Discord-Name:"), ("discordId","Discord-ID:"),
              ("discordUrl","Discord-URL:"), ("profilePicture","Profilbild-Pfad:")]

    def __init__(self, app):
        super().__init__(); self.app = app
        root = hbox(self, m=8, s=8)
        c1 = card(); l1 = vbox(c1)
        inner = QWidget(); f = vbox(inner, m=0)
        f.addWidget(heading("// PROFIL (simple-Seite)"))
        self.entries = {}
        for k, lbl in self.FIELDS: self.entries[k] = labeled_entry(f, lbl)
        f.addWidget(field_label("About-Text (aboutHtml):"))
        self.txt_about = QTextEdit(); f.addWidget(self.txt_about, 1)
        l1.addWidget(scroll_area(inner)); root.addWidget(c1, 1)

        c2 = card(); l2 = vbox(c2)
        l2.addWidget(heading("// LINKS"))
        self.links = TableEditor([("title","Titel",120),("url","URL",240),("sub","Sub",140)])
        l2.addWidget(self.links, 1)
        l2.addWidget(mk_btn("💾 config.json speichern", self.save))
        root.addWidget(c2, 1)
        self.load()

    def load(self):
        self.data = load_json(CONFIG_JSON, {})
        for k, _ in self.FIELDS: self.entries[k].setText(str(self.data.get(k, "")))
        self.txt_about.setPlainText(self.data.get("aboutHtml", ""))
        self.links.set_rows(self.data.get("links", []))

    def save(self):
        for k, _ in self.FIELDS: self.data[k] = self.entries[k].text().strip()
        self.data["aboutHtml"] = self.txt_about.toPlainText().strip()
        self.data["links"] = self.links.get_rows()
        if save_json(CONFIG_JSON, self.data): self.app.status("config.json gespeichert ✔")

# ==========================================================================
# TAB: MUSIC
# ==========================================================================
class MusicTab(QWidget):
    def __init__(self, app):
        super().__init__(); self.app = app
        root = vbox(self, m=8, s=8)
        c = card(); l = vbox(c)
        inner = QWidget(); f = vbox(inner, m=0)
        f.addWidget(heading("// MUSIC.JSON"))
        f.addWidget(field_label("Intro-Text (introText):"))
        self.txt_intro = QTextEdit(); self.txt_intro.setMaximumHeight(80); f.addWidget(self.txt_intro)
        self.e_fav = labeled_entry(f, "Favoriten-Playlist-ID (PL...):")
        f.addWidget(heading("// PLAYLISTS"))
        self.pl = TableEditor([("name","Name",140),("id","Playlist-ID",240),("note","Notiz",160)])
        f.addWidget(self.pl, 1)
        f.addWidget(mk_btn("💾 music.json speichern", self.save))
        l.addWidget(scroll_area(inner)); root.addWidget(c)
        self.load()

    def load(self):
        self.data = load_json(MUSIC_JSON, {})
        self.txt_intro.setPlainText(self.data.get("introText", ""))
        self.e_fav.setText(self.data.get("favoritesPlaylistId", ""))
        self.pl.set_rows(self.data.get("playlists", []))

    def save(self):
        self.data["introText"] = self.txt_intro.toPlainText().strip()
        self.data["favoritesPlaylistId"] = self.e_fav.text().strip()
        self.data["playlists"] = self.pl.get_rows()
        if save_json(MUSIC_JSON, self.data): self.app.status("music.json gespeichert ✔")

# ==========================================================================
# TAB: BADGES (simple)
# ==========================================================================
class BadgesTab(QWidget):
    def __init__(self, app):
        super().__init__(); self.app = app
        root = vbox(self, m=8, s=8)
        c = card(); l = vbox(c)
        l.addWidget(heading("// BADGES.JSON (88×31)"))
        self.ed = TableEditor([("img","Bild-URL/Pfad",240),("url","Link-URL",240),("alt","Alt-Text",120)])
        l.addWidget(self.ed, 1)
        l.addWidget(mk_btn("💾 badges.json speichern", self.save))
        root.addWidget(c)
        self.ed.set_rows(load_json(BADGES_JSON, []))

    def save(self):
        if save_json(BADGES_JSON, self.ed.get_rows()): self.app.status("badges.json gespeichert ✔")

# ==========================================================================
# TAB: WATCHLIST (CSV) — einzige Quelle
# ==========================================================================
class WatchlistTab(QWidget):
    def __init__(self, app):
        super().__init__(); self.app = app
        root = vbox(self, m=8, s=8)
        c = card(); l = vbox(c)
        l.addWidget(heading("// watchlist.csv (watching|completed|planning|dropped)"))
        self.headers = self._read_headers()
        self.ed = TableEditor([(h, h, 130) for h in self.headers])
        l.addWidget(self.ed, 1)
        l.addWidget(mk_btn("💾 watchlist.csv speichern", self.save))
        root.addWidget(c)
        self.load()

    def _read_headers(self):
        try:
            with open(WATCHLIST_CSV, encoding="utf-8") as fh:
                first = fh.readline().strip()
                if first: return [h.strip() for h in first.split(";")]
        except FileNotFoundError: pass
        return WL_HEADERS

    def load(self):
        rows = []
        try:
            with open(WATCHLIST_CSV, encoding="utf-8") as fh:
                rdr = csv.DictReader(fh, delimiter=";")
                rows = [{k: (v or "").strip() for k, v in r.items()} for r in rdr]
        except FileNotFoundError: pass
        self.ed.set_rows(rows)

    def save(self):
        try:
            backup(WATCHLIST_CSV)
            with open(WATCHLIST_CSV, "w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=self.headers, delimiter=";")
                w.writeheader()
                for r in self.ed.get_rows(): w.writerow(r)
            self.app.status("watchlist.csv gespeichert ✔")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))
# ==========================================================================
# TAB: DESKTOP-CONFIG  (ohne Watchlist-Doppelung)
# ==========================================================================
class DesktopTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app, self.cfg = app, {}
        self.fillers, self.collectors = [], []

        root = vbox(self, m=8, s=6)
        bar = hbox()
        bar.addWidget(heading("// DESKTOP-CONFIG (config.json)"))
        bar.addStretch(1)
        bar.addWidget(mk_btn("↻ Neu laden", self.load, "blue"))
        bar.addWidget(mk_btn("💾 Alles speichern", self.save))
        root.addLayout(bar)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        self._build_profile(); self._build_intel(); self._build_badges()
        self._build_links(); self._build_windows()
        self._build_apps(); self._build_autostart(); self._build_bin()
        self._build_appearance(); self._build_system(); self._build_clippy()
        self.load()

    # ---- Infrastruktur ----
    def _sub(self, title):
        """Erzeugt einen Sub-Tab mit Scrollbereich, gibt das inner-Layout zurück."""
        page = QWidget(); inner = QWidget()
        outer = vbox(page, m=0); outer.addWidget(scroll_area(inner))
        lay = vbox(inner, m=8)
        self.tabs.addTab(page, title)
        return lay

    def _all_win_ids(self):
        ids = [w[0] for w in DT_WINDOWS]
        for w in self.cfg.get("customWindows") or []:
            if w.get("id") and w["id"] not in ids: ids.append(w["id"])
        return ids

    def load(self):
        self.cfg = load_json(DESKTOP_JSON, {})
        for fn in self.fillers: fn()
        self.app.status("Desktop-Config geladen ✔")

    def save(self):
        self.cfg = load_json(DESKTOP_JSON, {})
        self.cfg.pop("watchlist", None)   # Doppelung entfernt – nur CSV ist Quelle
        try:
            for fn in self.collectors: fn()
        except Exception as ex:
            return QMessageBox.critical(self, "Eingabe ungültig", str(ex))
        if save_json(DESKTOP_JSON, self.cfg):
            self.app.status("config.json gespeichert ✔ (.bak angelegt)")

    # ---- Profil ----
    def _build_profile(self):
        lay = self._sub("👤 Profil")
        lay.addWidget(heading("// STAMMDATEN & DISCORD"))
        e = {}
        for k, lbl in [("operatorName","Name:"),("operatorRole","Rolle:"),
                       ("profilePicture","Profilbild:"),("discordId","Discord-ID:"),
                       ("discordName","Discord Fallback-Name:"),("discordUrl","Discord-URL:"),
                       ("nsFirst","Vorname-Größe px:"),("nsLast","Nachname-Größe px:"),
                       ("profileLayout","Ebenen (avatar,badges,text,stats):")]:
            e[k] = labeled_entry(lay, lbl)
        lay.addWidget(heading("// META-FELDER (Aktiv 1)"))
        self.dt_meta = TableEditor([("label","Label",110),("value","Wert",160),("hl","Aktiv",60)])
        lay.addWidget(self.dt_meta)
        lay.addWidget(heading("// STAT-BOXEN"))
        self.dt_stats = TableEditor([("label","Label",140),("value","Wert",140)])
        lay.addWidget(self.dt_stats)

        def fill():
            c = self.cfg
            for k in ("operatorName","operatorRole","profilePicture","discordId","discordName","discordUrl"):
                e[k].setText(str(c.get(k, "")))
            ns = c.get("nameSize") or {}
            e["nsFirst"].setText(str(ns.get("first", 38))); e["nsLast"].setText(str(ns.get("last", 38)))
            e["profileLayout"].setText(",".join(c.get("profileLayout") or ["avatar","badges","text","stats"]))
            self.dt_meta.set_rows([{"label": m.get("label",""), "value": m.get("value",""),
                                    "hl": B(m.get("hl"))} for m in c.get("profileMeta") or []])
            self.dt_stats.set_rows(c.get("stats") or [])

        def collect():
            c = self.cfg
            for k in ("operatorName","operatorRole","profilePicture","discordId","discordName","discordUrl"):
                c[k] = e[k].text().strip()
            c["nameSize"] = {"first": to_i(e["nsFirst"].text(), 38), "last": to_i(e["nsLast"].text(), 38)}
            c["profileLayout"] = [s.strip() for s in e["profileLayout"].text().split(",") if s.strip()]
            c["profileMeta"] = [{"label": r["label"], "value": r["value"], "hl": to_b(r["hl"])}
                                for r in self.dt_meta.get_rows()]
            c["stats"] = [{"label": r["label"], "value": r["value"]} for r in self.dt_stats.get_rows()]
        self.fillers.append(fill); self.collectors.append(collect)

    # ---- Intel ----
    def _build_intel(self):
        lay = self._sub("◉ Intel")
        lay.addWidget(heading("// ABOUT-TEXT (aboutHtml)"))
        self.dt_about = QTextEdit(); self.dt_about.setMinimumHeight(160); lay.addWidget(self.dt_about)
        self.dt_it_bg   = labeled_entry(lay, "Titel 'Background':")
        self.dt_it_spec = labeled_entry(lay, "Titel 'Specializations':")
        self.dt_ilayout = labeled_entry(lay, "Ebenen (intelLayout: text,badges):")

        def fill():
            c = self.cfg
            self.dt_about.setPlainText(c.get("aboutHtml", ""))
            it = c.get("intelTitles") or {}
            self.dt_it_bg.setText(it.get("background", "BACKGROUND"))
            self.dt_it_spec.setText(it.get("specializations", "SPECIALIZATIONS"))
            self.dt_ilayout.setText(",".join(c.get("intelLayout") or ["text","badges"]))

        def collect():
            c = self.cfg
            c["aboutHtml"] = self.dt_about.toPlainText().strip()
            c["intelTitles"] = {"background": self.dt_it_bg.text().strip() or "BACKGROUND",
                                "specializations": self.dt_it_spec.text().strip() or "SPECIALIZATIONS"}
            c["intelLayout"] = [s.strip() for s in self.dt_ilayout.text().split(",") if s.strip()]
        self.fillers.append(fill); self.collectors.append(collect)

    # ---- Badges ----
    def _build_badges(self):
        lay = self._sub("🏷 Badges")
        lay.addWidget(heading("// PROFIL-BADGES (t: o/c/g/p/r/y)"))
        self.dt_pb = TableEditor([("l","Name",160),("t","Farbe",90)])
        lay.addWidget(self.dt_pb)
        lay.addWidget(heading("// SPEZIALISIERUNGS-BADGES (Intel)"))
        self.dt_ib = TableEditor([("l","Name",160),("t","Farbe",90)])
        lay.addWidget(self.dt_ib)

        def fill():
            self.dt_pb.set_rows(self.cfg.get("profileBadges") or [])
            self.dt_ib.set_rows(self.cfg.get("intelBadges") or [])

        def collect():
            self.cfg["profileBadges"] = [{"l": r["l"], "t": r["t"] or "o"} for r in self.dt_pb.get_rows() if r["l"]]
            self.cfg["intelBadges"]  = [{"l": r["l"], "t": r["t"] or "o"} for r in self.dt_ib.get_rows() if r["l"]]
        self.fillers.append(fill); self.collectors.append(collect)

    # ---- Operations / Links ----
    def _build_links(self):
        lay = self._sub("▷ Operations")
        lay.addWidget(heading("// LINKS (dcStatus 1 = Discord-Status)"))
        self.dt_links = TableEditor([("code","Code",70),("title","Titel",110),("sub","Untertitel",140),
                                     ("url","URL",200),("icon","Icon",80),("dcStatus","DC",50)])
        lay.addWidget(self.dt_links)

        def fill():
            self.dt_links.set_rows([{**l, "dcStatus": B(l.get("dcStatus"))} for l in self.cfg.get("links") or []])

        def collect():
            self.cfg["links"] = [{"code": r["code"], "title": r["title"], "sub": r["sub"], "url": r["url"],
                                  "icon": r["icon"] or "link", "dcStatus": to_b(r["dcStatus"])}
                                 for r in self.dt_links.get_rows() if r["title"]]
        self.fillers.append(fill); self.collectors.append(collect)

    # ---- Custom Windows ----
    def _build_windows(self):
        lay = self._sub("⊞ Fenster")
        lay.addWidget(heading("// CUSTOM WINDOWS (content = JSON)"))
        self.dt_cw = TableEditor([("id","ID",90),("title","Titel",110),("subtitle","Sub",110),
                                  ("type","Typ",70),("icon","Icon",50),("initW","Breite",60),
                                  ("showStartMenu","Menü",60),("showDesktopIcon","Desktop",70),
                                  ("content","Content (JSON)",240)])
        lay.addWidget(self.dt_cw)

        def fill():
            rows = []
            for w in self.cfg.get("customWindows") or []:
                rows.append({"id": w.get("id",""), "title": w.get("title",""), "subtitle": w.get("subtitle",""),
                             "type": w.get("type","info"), "icon": w.get("icon","◆"), "initW": w.get("initW",420),
                             "showStartMenu": B(w.get("showStartMenu")), "showDesktopIcon": B(w.get("showDesktopIcon")),
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
                wins.append({"id": r["id"].strip() or f"cw_{int(time.time()*1000)}_{n}", "title": r["title"],
                             "subtitle": r["subtitle"], "type": r["type"] or "info", "icon": r["icon"] or "◆",
                             "initW": to_i(r["initW"], 420), "showStartMenu": to_b(r["showStartMenu"]),
                             "showDesktopIcon": to_b(r["showDesktopIcon"]), "content": content})
            self.cfg["customWindows"] = wins
        self.fillers.append(fill); self.collectors.append(collect)

    # ---- Apps & Layout ----
    def _build_apps(self):
        lay = self._sub("▦ Apps")
        lay.addWidget(heading("// SICHTBARKEIT (appVisibility)"))
        self.dt_av = TableEditor([("id","Fenster-ID",110),("menu","Menü",55),("desktop","Desktop",65),
                                  ("hidden","Versteckt",75),("mobil","Mobil",55)])
        lay.addWidget(self.dt_av)
        lay.addWidget(heading("// CUSTOM-FENSTER: Rahmenlos & Fixiert"))
        self.dt_ff = TableEditor([("id","Fenster-ID",110),("rahmenlos","Rahmenlos",85),("fixiert","Fixiert",70)])
        lay.addWidget(self.dt_ff)

        def fill():
            av = self.cfg.get("appVisibility") or {}; rows = []
            for i in self._all_win_ids():
                v = av.get(i, {})
                rows.append({"id": i, "menu": B(v.get("menu", True)), "desktop": B(v.get("desktop")),
                             "hidden": B(v.get("hidden")), "mobil": B(v.get("mobile", True))})
            self.dt_av.set_rows(rows)
            fl = self.cfg.get("frameless") or {}; fp = self.cfg.get("fixedPos") or {}
            cw = [w.get("id") for w in self.cfg.get("customWindows") or [] if w.get("id")]
            self.dt_ff.set_rows([{"id": i, "rahmenlos": B(fl.get(i)), "fixiert": B(fp.get(i))} for i in cw])

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

    # ---- Autostart ----
    def _build_autostart(self):
        lay = self._sub("▶ Autostart")
        lay.addWidget(heading("// AKTIV 1 = Autostart · Layer 1 = vorne"))
        self.dt_as = TableEditor([("id","Fenster-ID",120),("aktiv","Aktiv",55),("x","X",55),
                                  ("y","Y",55),("w","Breite",70),("layer","Layer",55)])
        lay.addWidget(self.dt_as)

        def fill():
            on = self.cfg.get("autostart") or []; pos = self.cfg.get("autostartPos") or {}
            lay_z = self.cfg.get("windowLayers") or {}; rows = []
            for i in self._all_win_ids():
                p = pos.get(i, {})
                rows.append({"id": i, "aktiv": B(i in on), "x": p.get("x", 100), "y": p.get("y", 60),
                             "w": p.get("w", 440), "layer": lay_z.get(i, "")})
            self.dt_as.set_rows(rows)

        def collect():
            on, pos, lay_z = [], {}, {}
            for r in self.dt_as.get_rows():
                if not r["id"]: continue
                if to_b(r["aktiv"]): on.append(r["id"])
                pos[r["id"]] = {"x": to_i(r["x"], 100), "y": to_i(r["y"], 60), "w": to_i(r["w"], 440)}
                z = to_i(r["layer"], 0)
                if z: lay_z[r["id"]] = z
            self.cfg["autostart"] = on; self.cfg["autostartPos"] = pos; self.cfg["windowLayers"] = lay_z
        self.fillers.append(fill); self.collectors.append(collect)

    # ---- Papierkorb ----
    def _build_bin(self):
        page = QWidget(); root = hbox(page, m=8, s=8)
        c1 = card(); l1 = vbox(c1)
        l1.addWidget(heading("// DATEIEN"))
        self.rb_lb = QListWidget(); self.rb_lb.currentRowChanged.connect(self._rb_select)
        l1.addWidget(self.rb_lb, 1)
        bf = hbox(); bf.addWidget(mk_btn("+ Neu", self._rb_new))
        bf.addWidget(mk_btn("– Löschen", self._rb_del, "rust")); bf.addStretch(1)
        l1.addLayout(bf)
        c2 = card(); l2 = vbox(c2)
        l2.addWidget(heading("// INHALT"))
        self.rb_name = labeled_entry(l2, "Dateiname:")
        l2.addWidget(field_label("Inhalt:"))
        self.rb_txt = QTextEdit(); l2.addWidget(self.rb_txt, 1)
        l2.addWidget(mk_btn("Übernehmen", self._rb_apply, "blue"))
        root.addWidget(c1, 1); root.addWidget(c2, 2)
        self.tabs.addTab(page, "⌦ Papierkorb")
        self.rb_items, self.rb_sel = [], None

        def fill():
            self.rb_items = [dict(x) for x in self.cfg.get("recycleBin") or []]; self._rb_refresh()
        def collect():
            self.cfg["recycleBin"] = self.rb_items
        self.fillers.append(fill); self.collectors.append(collect)

    def _rb_refresh(self):
        self.rb_lb.blockSignals(True); self.rb_lb.clear(); self.rb_sel = None
        for it in self.rb_items:
            self.rb_lb.addItem(f"{it.get('name','?')}  ({it.get('date','')})")
        self.rb_lb.blockSignals(False)

    def _rb_select(self, row):
        if row < 0 or row >= len(self.rb_items): return
        self.rb_sel = row; it = self.rb_items[row]
        self.rb_name.setText(it.get("name", "")); self.rb_txt.setPlainText(it.get("content", ""))

    def _rb_new(self):
        self.rb_items.append({"name": "neu.txt", "content": "", "date": time.strftime("%d.%m.%Y")})
        self._rb_refresh()

    def _rb_apply(self):
        if self.rb_sel is None: return QMessageBox.warning(self, "Achtung", "Erst Datei wählen!")
        self.rb_items[self.rb_sel]["name"] = self.rb_name.text().strip() or "unbenannt.txt"
        self.rb_items[self.rb_sel]["content"] = self.rb_txt.toPlainText().rstrip("\n")
        self._rb_refresh()

    def _rb_del(self):
        if self.rb_sel is None: return
        self.rb_items.pop(self.rb_sel); self._rb_refresh()

    # ---- Appearance ----
    def _build_appearance(self):
        lay = self._sub("◑ Appearance")
        lay.addWidget(heading("// THEME & OS-IDENTITÄT"))
        lay.addWidget(field_label("Aktives Theme (dark/gold/yellow):"))
        self.dt_theme = QComboBox(); self.dt_theme.setEditable(True)
        self.dt_theme.addItems(["dark", "gold", "yellow"]); lay.addWidget(self.dt_theme)
        self.dt_osname = labeled_entry(lay, "OS-Name (osName):")
        self.dt_ossub  = labeled_entry(lay, "Untertitel (osSub):")
        self.dt_oshl   = labeled_entry(lay, "Highlight-Buchstabe:")
        self.dt_bg     = labeled_entry(lay, "Hintergrund (bgImage):")
        self.dt_bgdef  = labeled_entry(lay, "Standard-Hintergrund:")
        lay.addWidget(heading("// THEME-HINTERGRÜNDE (themeBg)"))
        self.dt_tbg = TableEditor([("theme","Theme",100),("url","URL/Pfad",240)])
        lay.addWidget(self.dt_tbg)

        def fill():
            c = self.cfg
            self.dt_theme.setCurrentText(c.get("theme", "dark"))
            self.dt_osname.setText(c.get("osName", "FA|BIAN"))
            self.dt_ossub.setText(c.get("osSub", "ENDFIELD OS // v3.0"))
            self.dt_oshl.setText(c.get("osHighlight", "B"))
            self.dt_bg.setText(c.get("bgImage") or "")
            self.dt_bgdef.setText(c.get("bgImageDefault") or "")
            self.dt_tbg.set_rows([{"theme": k, "url": v} for k, v in (c.get("themeBg") or {}).items()])

        def collect():
            c = self.cfg
            c["theme"] = self.dt_theme.currentText().strip() or "dark"
            c["osName"] = self.dt_osname.text().strip() or "FA|BIAN"
            c["osSub"] = self.dt_ossub.text().strip()
            c["osHighlight"] = (self.dt_oshl.text().strip() or "B")[0]
            c["bgImage"] = self.dt_bg.text().strip() or None
            c["bgImageDefault"] = self.dt_bgdef.text().strip() or None
            c["themeBg"] = {r["theme"]: r["url"] for r in self.dt_tbg.get_rows() if r["theme"] and r["url"]}
        self.fillers.append(fill); self.collectors.append(collect)

    # ---- System ----
    def _build_system(self):
        lay = self._sub("◷ System")
        lay.addWidget(heading("// LADESCREEN"))
        self.dt_lden = QCheckBox("Ladescreen aktiviert (loadingEnabled)"); lay.addWidget(self.dt_lden)
        self.dt_lddur = labeled_entry(lay, "Ladezeit ms (loadingDuration):")
        self.dt_ldtxt = labeled_entry(lay, "Untertitel (loadingText):")
        lay.addWidget(heading("// VERSTECKTE ORDNER (hiddenFolders)"))
        self.dt_hidden = TableEditor([("path","Pfad (rel. data/files)",260)])
        lay.addWidget(self.dt_hidden)
        lay.addWidget(heading("// CUSTOM THEMES (JSON-Liste)"))
        self.dt_ct = QTextEdit(); self.dt_ct.setMinimumHeight(200); lay.addWidget(self.dt_ct)

        def fill():
            c = self.cfg
            self.dt_lden.setChecked(c.get("loadingEnabled", True) is not False)
            self.dt_lddur.setText(str(c.get("loadingDuration", 2800)))
            self.dt_ldtxt.setText(c.get("loadingText", "INITIALIZING DESKTOP"))
            self.dt_hidden.set_rows([{"path": p} for p in c.get("hiddenFolders") or []])
            self.dt_ct.setPlainText(json.dumps(c.get("customThemes") or [], indent=2, ensure_ascii=False))

        def collect():
            c = self.cfg
            c["loadingEnabled"] = bool(self.dt_lden.isChecked())
            c["loadingDuration"] = to_i(self.dt_lddur.text(), 2800)
            c["loadingText"] = self.dt_ldtxt.text().strip()
            c["hiddenFolders"] = [r["path"] for r in self.dt_hidden.get_rows() if r["path"]]
            txt = self.dt_ct.toPlainText().strip()
            if txt:
                try: data = json.loads(txt)
                except Exception as ex: raise ValueError(f"customThemes-JSON ungültig: {ex}")
                if not isinstance(data, list): raise ValueError("customThemes muss eine Liste sein!")
                c["customThemes"] = data
            else:
                c["customThemes"] = []
        self.fillers.append(fill); self.collectors.append(collect)

    # ---- Clippy ----
    def _build_clippy(self):
        lay = self._sub("❖ Clippy")
        lay.addWidget(heading("// Bilder mit ; trennen · Ecke: br/bl/tr/tl"))
        self.dt_cl = TableEditor([("name","Name",100),("enabled","Aktiv",55),("corner","Ecke",55),
                                  ("minSec","Min s",55),("maxSec","Max s",55),("images","Bilder (;)",260)])
        lay.addWidget(self.dt_cl)

        def fill():
            rows = []
            for cl in self.cfg.get("clippys") or []:
                rows.append({"name": cl.get("name",""), "enabled": B(cl.get("enabled")),
                             "corner": cl.get("corner","br"), "minSec": cl.get("minSec",45),
                             "maxSec": cl.get("maxSec",120), "images": ";".join(cl.get("images") or [])})
            self.dt_cl.set_rows(rows)
            self._cl_ids = [cl.get("id") for cl in self.cfg.get("clippys") or []]

        def collect():
            out = []
            for n, r in enumerate(self.dt_cl.get_rows()):
                cid = self._cl_ids[n] if n < len(getattr(self, "_cl_ids", [])) else None
                out.append({"id": cid or f"cl{int(time.time()*1000)}{n}", "name": r["name"] or f"Clippy {n+1}",
                            "enabled": to_b(r["enabled"]), "corner": r["corner"] or "br",
                            "minSec": to_i(r["minSec"], 45), "maxSec": to_i(r["maxSec"], 120),
                            "images": [s.strip() for s in r["images"].split(";") if s.strip()]})
            self.cfg["clippys"] = out
        self.fillers.append(fill); self.collectors.append(collect)

# ==========================================================================
# TAB: RAW JSON
# ==========================================================================
class RawTab(QWidget):
    def __init__(self, app):
        super().__init__(); self.app = app
        self.current, self.paths = None, []
        root = hbox(self, m=8, s=8)
        c1 = card(); l1 = vbox(c1)
        l1.addWidget(heading("// DATEIEN"))
        self.lb = QListWidget(); self.lb.currentRowChanged.connect(self.open_file)
        l1.addWidget(self.lb, 1)
        l1.addWidget(mk_btn("↻ Aktualisieren", self.scan, "blue"))
        c2 = card(); l2 = vbox(c2)
        l2.addWidget(heading("// RAW JSON"))
        self.txt = QTextEdit(); self.txt.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.txt.setFont(QFont("Consolas", 11))
        l2.addWidget(self.txt, 1)
        bf = hbox(); bf.addWidget(mk_btn("✔ Validieren", self.validate, "blue"))
        bf.addStretch(1); bf.addWidget(mk_btn("💾 Speichern", self.save))
        l2.addLayout(bf)
        root.addWidget(c1, 1); root.addWidget(c2, 3)
        self.scan()

    def scan(self):
        self.lb.blockSignals(True); self.lb.clear(); self.paths = []
        if os.path.exists(DESKTOP_JSON):
            self.lb.addItem("config.json (Desktop)"); self.paths.append(DESKTOP_JSON)
        if os.path.isdir(DATA_DIR):
            for fn in sorted(os.listdir(DATA_DIR)):
                if fn.endswith(".json"):
                    self.lb.addItem(fn); self.paths.append(os.path.join(DATA_DIR, fn))
        self.lb.blockSignals(False)

    def open_file(self, row):
        if row < 0 or row >= len(self.paths): return
        self.current = self.paths[row]
        with open(self.current, encoding="utf-8") as fh:
            self.txt.setPlainText(fh.read())
        self.app.status(f"Geöffnet: {self.current}")

    def validate(self):
        try:
            json.loads(self.txt.toPlainText())
            QMessageBox.information(self, "OK", "Gültiges JSON ✔"); return True
        except Exception as e:
            QMessageBox.critical(self, "Ungültig", str(e)); return False

    def save(self):
        if not self.current: return
        try:
            data = json.loads(self.txt.toPlainText())
        except Exception as e:
            return QMessageBox.critical(self, "Ungültiges JSON", str(e))
        if save_json(self.current, data):
            self.app.status(f"{self.current} gespeichert ✔")

# ==========================================================================
# HAUPTFENSTER  (BackgroundWidget + music-bg, Statusleiste ZUERST)
# ==========================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FABIAN.OS – Site Editor")
        self.resize(1480, 900)

        # Hintergrund (music-bg) als Central-Widget; darüber ein transparentes Layout
        bg = BackgroundWidget()
        self.setCentralWidget(bg)
        root = vbox(bg, m=14, s=8)

        # Header
        header = hbox()
        title = QLabel("FA|BIAN.OS"); title.setObjectName("title")
        sub = QLabel("// SITE EDITOR"); sub.setObjectName("subtitle")
        header.addWidget(title); header.addWidget(sub); header.addStretch(1)
        root.addLayout(header)

        # --- Statusleiste ZUERST anlegen (Tabs rufen status() beim Laden auf!) ---
        self.sb = QStatusBar()
        self.setStatusBar(self.sb)
        self.sb.showMessage("Bereit")

        # Tabs erst DANACH
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)
        self.tabs.addTab(DesktopTab(self),   "👤 Config")
        self.tabs.addTab(TravelTab(self),    "🗺 Travelmap")
        self.tabs.addTab(MusicTab(self),     "♫ Music")
        self.tabs.addTab(BadgesTab(self),    "🏷 Badges (simple)")
        self.tabs.addTab(WatchlistTab(self), "📺 Watchlist (CSV)")
        self.tabs.addTab(RawTab(self),       "{} Raw JSON")

    def status(self, msg):
        self.sb.showMessage(msg)

# ==========================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())