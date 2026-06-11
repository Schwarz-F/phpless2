#!/usr/bin/env python3
import os
import json
import tkinter as tk
from tkinter import messagebox, ttk
from geopy.geocoders import Nominatim

try:
    import build
    BUILD_AVAILABLE = True
except ImportError:
    BUILD_AVAILABLE = False

JSON_PATH = os.path.join("data", "config", "travel.json")

class TravelEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FABIAN.OS // Travelmap Editor (Advanced Mode)")
        self.root.geometry("1150x760")
        self.root.configure(bg="#1e1e1e")

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TLabel", background="#1e1e1e", foreground="#ffffff")
        self.style.configure("TFrame", background="#1e1e1e")

        self.places = []
        self.selected_place_index = None
        self.selected_trip_index = None

        self.geolocator = Nominatim(user_agent="fabian_os_travelmap_editor")

        self.create_widgets()
        self.load_json()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # ---------------------------------------------------------------------
        # LINKER BEREICH: Orte-Liste & Build
        # ---------------------------------------------------------------------
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        lbl_list = tk.Label(left_frame, text="// Vorhandene Orte", bg="#1e1e1e", fg="#4fc7ad", font=("Courier", 12, "bold"))
        lbl_list.pack(anchor=tk.W, pady=(0, 5))

        self.places_listbox = tk.Listbox(left_frame, bg="#2d2d2d", fg="#ffffff", selectbackground="#4fc7ad", selectforeground="#1e1e1e", font=("Arial", 10), bd=0, highlightthickness=1, highlightbackground="#444444")
        self.places_listbox.pack(fill=tk.BOTH, expand=True)
        self.places_listbox.bind("<<ListboxSelect>>", self.on_place_select)

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        self.btn_new = tk.Button(btn_frame, text="+ Ort Neu", bg="#4fc7ad", fg="#1e1e1e", command=self.clear_form_for_new_place, font=("Arial", 10, "bold"), bd=0, padx=10, pady=5)
        self.btn_new.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_delete = tk.Button(btn_frame, text="- Ort Löschen", bg="#e08358", fg="#ffffff", command=self.delete_place, font=("Arial", 10, "bold"), bd=0, padx=10, pady=5)
        self.btn_delete.pack(side=tk.LEFT, padx=5)

        self.btn_run_build = tk.Button(left_frame, text="Build ausführen 🛠️", bg="#2d44c4", fg="#ffffff", font=("Arial", 11, "bold"), command=self.trigger_build, bd=0, pady=8)
        self.btn_run_build.pack(fill=tk.X, pady=(10, 0))

        # ---------------------------------------------------------------------
        # MITTLERER BEREICH: Orts-Details & Globale Fotos
        # ---------------------------------------------------------------------
        mid_frame = ttk.Frame(main_frame)
        mid_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        lbl_edit = tk.Label(mid_frame, text="// Ort-Stammdaten", bg="#1e1e1e", fg="#4fc7ad", font=("Courier", 12, "bold"))
        lbl_edit.pack(anchor=tk.W, pady=(0, 10))

        self.entry_city = self.create_label_entry(mid_frame, "Stadt (city):")
        self.entry_country = self.create_label_entry(mid_frame, "Land (country):")

        # Geocoding
        geo_box = tk.LabelFrame(mid_frame, text=" Geocoding ", bg="#2d2d2d", fg="#ffffff", padx=10, pady=10, font=("Arial", 9, "italic"))
        geo_box.pack(fill=tk.X, pady=10)
        tk.Label(geo_box, text="Adresse / Sehenswürdigkeit:", bg="#2d2d2d", fg="#fff").pack(anchor=tk.W)
        self.entry_search_address = tk.Entry(geo_box, bg="#1e1e1e", fg="#fff", bd=1, insertbackground="white")
        self.entry_search_address.pack(fill=tk.X, pady=5)
        btn_geo = tk.Button(geo_box, text="Koordinaten suchen 🔍", bg="#2d44c4", fg="#fff", bd=0, padx=6, pady=4, command=self.search_coordinates)
        btn_geo.pack(anchor=tk.E, pady=2)

        self.entry_lat = self.create_label_entry(mid_frame, "Breitengrad (lat):")
        self.entry_lon = self.create_label_entry(mid_frame, "Längengrad (lon):")

        tk.Label(mid_frame, text="Status:", bg="#1e1e1e", fg="#fff").pack(anchor=tk.W, pady=(5, 2))
        self.combo_status = ttk.Combobox(mid_frame, values=["visited", "want", "home"], state="readonly")
        self.combo_status.pack(fill=tk.X, pady=(0, 5))
        self.combo_status.set("visited")

        self.entry_note = self.create_label_entry(mid_frame, "Notiz (note):")
        self.picturecaption = self.create_label_entry(mid_frame, "Caption (picture caption):")
        self.count = self.create_label_entry(mid_frame, "Anzahl Besuche (alternativer wert):")
        # NEU: Anzeige für globale Bilder (ohne Trip)
        img_box = tk.LabelFrame(mid_frame, text=" Ort-Fotos (ohne Trip) ", bg="#2d2d2d", fg="#ffffff", padx=10, pady=8)
        img_box.pack(fill=tk.X, pady=10)
        self.lbl_global_images = tk.Label(img_box, text="0 globale Bilder gefunden", bg="#2d2d2d", fg="#4fc7ad", font=("Arial", 9, "italic"))
        self.lbl_global_images.pack(anchor=tk.W)

        self.btn_save_place = tk.Button(mid_frame, text="Ort & Stammdaten speichern", bg="#4fc7ad", fg="#1e1e1e", font=("Arial", 11, "bold"), command=self.save_place, bd=0, pady=8)
        self.btn_save_place.pack(fill=tk.X, pady=(10, 0))

        # ---------------------------------------------------------------------
        # RECHTER BEREICH: Trip-Manager
        # ---------------------------------------------------------------------
        right_frame = tk.LabelFrame(main_frame, text=" Trips für diesen Ort verwalten ", bg="#232323", fg="#4fc7ad", padx=10, pady=10, font=("Courier", 11, "bold"))
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        self.trips_listbox = tk.Listbox(right_frame, bg="#2d2d2d", fg="#ffffff", selectbackground="#2d44c4", font=("Arial", 9), bd=0, height=6)
        self.trips_listbox.pack(fill=tk.X, pady=(0, 5))
        self.trips_listbox.bind("<<ListboxSelect>>", self.on_trip_select)

        trip_btn_frame = ttk.Frame(right_frame)
        trip_btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_new_trip = tk.Button(trip_btn_frame, text="+ Trip hinzufügen", bg="#2d44c4", fg="#fff", bd=0, padx=6, pady=3, command=self.add_trip_field)
        self.btn_new_trip.pack(side=tk.LEFT)
        
        self.btn_del_trip = tk.Button(trip_btn_frame, text="- Trip entfernen", bg="#e08358", fg="#fff", bd=0, padx=6, pady=3, command=self.delete_trip_field)
        self.btn_del_trip.pack(side=tk.LEFT, padx=5)

        tk.Label(right_frame, text="Von (from) (z.B. 15.05.2024):", bg="#232323", fg="#fff").pack(anchor=tk.W, pady=(5,0))
        self.entry_trip_from = tk.Entry(right_frame, bg="#2d2d2d", fg="#fff", bd=1, insertbackground="white")
        self.entry_trip_from.pack(fill=tk.X, pady=2)

        tk.Label(right_frame, text="Bis (to) (optional):", bg="#232323", fg="#fff").pack(anchor=tk.W, pady=(5,0))
        self.entry_trip_to = tk.Entry(right_frame, bg="#2d2d2d", fg="#fff", bd=1, insertbackground="white")
        self.entry_trip_to.pack(fill=tk.X, pady=2)

        tk.Label(right_frame, text="Beschreibung (comment):", bg="#232323", fg="#fff").pack(anchor=tk.W, pady=(5,0))
        self.entry_trip_comment = tk.Entry(right_frame, bg="#2d2d2d", fg="#fff", bd=1, insertbackground="white")
        self.entry_trip_comment.pack(fill=tk.X, pady=2)

        tk.Label(right_frame, text="Bilder in diesem Trip (images):", bg="#232323", fg="#4fc7ad").pack(anchor=tk.W, pady=(10,0))
        self.lbl_trip_images_count = tk.Label(right_frame, text="Kein Trip gewählt", bg="#232323", fg="#bbb", font=("Arial", 9, "italic"))
        self.lbl_trip_images_count.pack(anchor=tk.W)

        self.btn_save_trip_changes = tk.Button(right_frame, text="Ausgewählten Trip aktualisieren", bg="#2d44c4", fg="#ffffff", font=("Arial", 10, "bold"), command=self.update_current_trip, bd=0, pady=5)
        self.btn_save_trip_changes.pack(fill=tk.X, pady=(15, 0))

    def create_label_entry(self, parent, label_text):
        tk.Label(parent, text=label_text, bg="#1e1e1e", fg="#fff").pack(anchor=tk.W, pady=(5, 2))
        entry = tk.Entry(parent, bg="#2d2d2d", fg="#ffffff", bd=1, insertbackground="white")
        entry.pack(fill=tk.X, pady=(0, 5))
        return entry

    def load_json(self):
        if os.path.exists(JSON_PATH):
            try:
                with open(JSON_PATH, "r", encoding="utf-8") as f:
                    self.places = json.load(f)
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Laden der JSON-Datei: {e}")
                self.places = []
        else:
            self.places = []
        self.update_places_listbox()

    def write_json(self):
        try:
            os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
            with open(JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(self.places, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Schreiben der JSON-Datei: {e}")
            return False

    def update_places_listbox(self):
        self.places_listbox.delete(0, tk.END)
        for p in self.places:
            city = p.get("city", "Unbekannt")
            country = p.get("country", "")
            display_text = f"{city} ({country})" if country else city
            self.places_listbox.insert(tk.END, display_text)

    def on_place_select(self, event):
        selection = self.places_listbox.curselection()
        if not selection:
            return

        self.selected_place_index = selection[0]
        place = self.places[self.selected_place_index]

        self.set_entry_text(self.entry_city, place.get("city", ""))
        self.set_entry_text(self.entry_country, place.get("country", ""))
        self.set_entry_text(self.entry_lat, str(place.get("lat", "")))
        self.set_entry_text(self.entry_lon, str(place.get("lon", "")))
        self.combo_status.set(place.get("status", "visited"))
        self.set_entry_text(self.entry_note, place.get("note", ""))
        self.set_entry_text(self.count, place.get("count", ""))
        self.set_entry_text(self.picturecaption, place.get("picturecaption", ""))
        self.set_entry_text(self.entry_search_address, f"{place.get('city', '')} {place.get('country', '')}")

        # Update globale Bilder-Anzeige
        global_imgs = len(place.get("images", []))
        self.lbl_global_images.config(text=f"{global_imgs} Bild(er) direkt dem Ort zugewiesen.")

        self.update_trips_listbox()
        self.clear_trip_form()

    def update_trips_listbox(self):
        self.trips_listbox.delete(0, tk.END)
        if self.selected_place_index is None:
            return
        place = self.places[self.selected_place_index]
        trips = place.get("dates", [])
        for t in trips:
            from_d = t.get("from", "??")
            to_d = f" bis {t.get('to')}" if t.get('to') else ""
            comment = f" - {t.get('comment')}" if t.get('comment') else ""
            self.trips_listbox.insert(tk.END, f"// {from_d}{to_d}{comment}")

    def on_trip_select(self, event):
        selection = self.trips_listbox.curselection()
        if not selection:
            return
        self.selected_trip_index = selection[0]
        place = self.places[self.selected_place_index]
        trip = place.get("dates", [])[self.selected_trip_index]

        self.set_entry_text(self.entry_trip_from, trip.get("from", ""))
        self.set_entry_text(self.entry_trip_to, trip.get("to", ""))
        self.set_entry_text(self.entry_trip_comment, trip.get("comment", ""))
        
        imgs_count = len(trip.get("images", []))
        self.lbl_trip_images_count.config(text=f"{imgs_count} Bild(er) diesem Trip zugewiesen.", fg="#4fc7ad")

    def clear_trip_form(self):
        self.selected_trip_index = None
        self.set_entry_text(self.entry_trip_from, "")
        self.set_entry_text(self.entry_trip_to, "")
        self.set_entry_text(self.entry_trip_comment, "")
        self.lbl_trip_images_count.config(text="Kein Trip ausgewählt", fg="#bbb")

    def set_entry_text(self, entry_widget, text):
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, text)

    def clear_form_for_new_place(self):
        self.selected_place_index = None
        self.places_listbox.selection_clear(0, tk.END)
        self.set_entry_text(self.entry_city, "")
        self.set_entry_text(self.entry_country, "")
        self.set_entry_text(self.entry_lat, "")
        self.set_entry_text(self.entry_lon, "")
        self.combo_status.set("visited")
        self.set_entry_text(self.entry_note, "")
        self.set_entry_text(self.count, "")
        self.set_entry_text(self.picturecaption, "")
        self.set_entry_text(self.entry_search_address, "")
        self.lbl_global_images.config(text="0 globale Bilder gefunden")
        self.update_trips_listbox()
        self.clear_trip_form()

    def search_coordinates(self):
        address = self.entry_search_address.get().strip()
        if not address:
            messagebox.showwarning("Achtung", "Bitte gib zuerst eine Adresse ein!")
            return
        try:
            location = self.geolocator.geocode(address)
            if location:
                self.set_entry_text(self.entry_lat, f"{location.latitude:.5f}")
                self.set_entry_text(self.entry_lon, f"{location.longitude:.5f}")
            else:
                messagebox.showwarning("Nicht gefunden", "Es konnten keine Koordinaten für diese Adresse gefunden werden.")
        except Exception as e:
            messagebox.showerror("API Fehler", f"Fehler bei der Verbindung zum Geodienst: {e}")

    def save_place(self):
        city = self.entry_city.get().strip()
        if not city:
            messagebox.showwarning("Fehler", "Das Feld 'Stadt' ist Pflicht!")
            return
        try:
            lat = float(self.entry_lat.get().strip())
            lon = float(self.entry_lon.get().strip())
        except ValueError:
            messagebox.showwarning("Fehler", "Breiten- und Längengrad müssen gültige Nummern sein!")
            return

        place_data = {
            "city": city,
            "country": self.entry_country.get().strip(),
            "lat": lat,
            "lon": lon,
            "status": self.combo_status.get(),
            "note": self.entry_note.get().strip(),
            "count": self.count.get().strip(),
            "picturecaption": self.picturecaption.get().strip()
        }

        if self.selected_place_index is not None:
            place_data["dates"] = self.places[self.selected_place_index].get("dates", [])
            place_data["images"] = self.places[self.selected_place_index].get("images", []) # Globale Fotos schützen
            self.places[self.selected_place_index] = place_data
        else:
            place_data["dates"] = []
            place_data["images"] = []
            self.places.append(place_data)

        if self.write_json():
            self.update_places_listbox()
            self.clear_form_for_new_place()
            messagebox.showinfo("Erfolg", "Ort-Stammdaten erfolgreich gespeichert!")

    def add_trip_field(self):
        if self.selected_place_index is None:
            messagebox.showwarning("Achtung", "Bitte wähle zuerst links einen Ort aus!")
            return
        new_trip = {"from": "01.01.2026", "to": "", "comment": "Neuer Trip Eintrag", "images": []}
        self.places[self.selected_place_index]["dates"].append(new_trip)
        self.write_json()
        self.update_trips_listbox()
        last_idx = len(self.places[self.selected_place_index]["dates"]) - 1
        self.trips_listbox.selection_set(last_idx)
        self.trips_listbox.event_generate("<<ListboxSelect>>")

    def update_current_trip(self):
        if self.selected_place_index is None or self.selected_trip_index is None:
            messagebox.showwarning("Achtung", "Bitte wähle zuerst einen Ort und einen Trip aus!")
            return
        frm = self.entry_trip_from.get().strip()
        if not frm:
            messagebox.showwarning("Fehler", "Das 'From'-Datum darf nicht leer sein!")
            return

        trip_list = self.places[self.selected_place_index]["dates"]
        current_images = trip_list[self.selected_trip_index].get("images", [])

        updated_trip = {
            "from": frm,
            "to": self.entry_trip_to.get().strip(),
            "comment": self.entry_trip_comment.get().strip(),
            "images": current_images
        }

        trip_list[self.selected_trip_index] = updated_trip
        if self.write_json():
            self.update_trips_listbox()
            messagebox.showinfo("Erfolg", "Trip-Details aktualisiert!")

    def delete_trip_field(self):
        if self.selected_place_index is None or self.selected_trip_index is None:
            messagebox.showwarning("Achtung", "Bitte wähle den Trip aus, den du löschen möchtest!")
            return
        if messagebox.askyesno("Trip löschen", "Möchtest du diesen Reisezeitraum wirklich löschen?"):
            self.places[self.selected_place_index]["dates"].pop(self.selected_trip_index)
            self.write_json()
            self.update_trips_listbox()
            self.clear_trip_form()

    def delete_place(self):
        if self.selected_place_index is None:
            messagebox.showwarning("Achtung", "Bitte wähle zuerst einen Ort aus!")
            return
        city = self.places[self.selected_place_index].get("city")
        if messagebox.askyesno("Löschen bestätigen", f"Möchtest du '{city}' samt aller zugehörigen Trips löschen?"):
            self.places.pop(self.selected_place_index)
            if self.write_json():
                self.update_places_listbox()
                self.clear_form_for_new_place()

    def trigger_build(self):
        if not BUILD_AVAILABLE:
            messagebox.showerror("Fehler", "Die Datei 'build.py' wurde im selben Verzeichnis nicht gefunden!")
            return
        try:
            build.main()
            self.load_json()
            # Ausgewählten Index neu triggern um GUI zu refreshen
            if self.selected_place_index is not None:
                self.places_listbox.selection_set(self.selected_place_index)
                self.on_place_select(None)
            messagebox.showinfo("Build erfolgreich", "Der statische Build wurde ausgeführt!\nBilder auf Orts- und Trip-Ebene wurden aktualisiert.")
        except Exception as e:
            messagebox.showerror("Build Fehler", f"Fehler beim Ausführen des Builds:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TravelEditorApp(root)
    root.mainloop()