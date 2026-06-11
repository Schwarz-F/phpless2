#!/usr/bin/env python3
import os
import json

DATA_DIR = os.path.join("data", "config")
TRAVEL_JSON_PATH = os.path.join(DATA_DIR, "travel.json")
IMAGES_BASE_DIR = os.path.join("data", "files", "Travel")
VALID_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif")

def main():
    print("=== Starte FABIAN.OS Advanced Static Build ===")

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    
    if not os.path.exists(IMAGES_BASE_DIR):
        os.makedirs(IMAGES_BASE_DIR, exist_ok=True)

    places = []
    if os.path.exists(TRAVEL_JSON_PATH):
        try:
            with open(TRAVEL_JSON_PATH, "r", encoding="utf-8") as f:
                places = json.load(f)
        except Exception as e:
            print(f" /!\\ Fehler beim Laden der travel.json: {e}")
            return

    updated_count = 0

    for place in places:
        city_name = place.get("city")
        if not city_name:
            continue

        city_folder_path = os.path.join(IMAGES_BASE_DIR, city_name)
        
        global_images = []
        trip_folders_found = {}

        if os.path.exists(city_folder_path):
            try:
                for item in sorted(os.listdir(city_folder_path)):
                    item_path = os.path.join(city_folder_path, item)
                    
                    # Fall A: Direkt eine Bilddatei -> Globales Foto für den Ort
                    if os.path.isfile(item_path) and item.lower().endswith(VALID_EXTENSIONS):
                        web_path = f"./data/files/Travel/{city_name}/{item}"
                        global_images.append(web_path)
                    
                    # Fall B: Ein Unterordner -> Gehört zu einer Reise (z.B. Ordnername "02.01.2026")
                    elif os.path.isdir(item_path):
                        sub_images = []
                        for sub_item in sorted(os.listdir(item_path)):
                            if sub_item.lower().endswith(VALID_EXTENSIONS):
                                sub_images.append(f"./data/files/Travel/{city_name}/{item}/{sub_item}")
                        if sub_images:
                            trip_folders_found[item] = sub_images
            except Exception as e:
                print(f" /!\\ Fehler beim Scannen von {city_name}: {e}")

        # Globale Bilder abgleichen
        old_global = place.get("images", [])
        if old_global != global_images:
            place["images"] = global_images
            updated_count += 1

        # Trip-spezifische Bilder abgleichen (sucht nach Ordnername == 'from'-Datum)
        trips = place.get("dates", [])
        for trip in trips:
            trip_from = trip.get("from", "")
            if trip_from in trip_folders_found:
                old_trip_imgs = trip.get("images", [])
                new_trip_imgs = trip_folders_found[trip_from]
                if old_trip_imgs != new_trip_imgs:
                    trip["images"] = new_trip_imgs
                    updated_count += 1
            else:
                if "images" not in trip:
                    trip["images"] = []

    try:
        with open(TRAVEL_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(places, f, indent=2, ensure_ascii=False)
        print(f"-> Build abgeschlossen. {updated_count} Änderung(en) in travel.json gesichert.")
    except Exception as e:
        print(f" /!\\ Fehler beim Schreiben der travel.json: {e}")

if __name__ == "__main__":
    main()