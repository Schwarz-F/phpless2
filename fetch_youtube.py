import urllib.request
import xml.etree.ElementTree as ET
import json
import os

# Namespaces für YouTube-RSS
NAMESPACES = {
    'atom': 'http://w3.org',
    'yt': 'http://youtube.com',
    'media': 'http://yahoo.com'
}

def fetch_and_save_playlist(playlist_id):
    """Lädt eine YouTube-Playlist und speichert sie im neuen Ordner."""
    url = f"https://youtube.com{playlist_id}"
    try:
        response = urllib.request.urlopen(url)
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        
        videos = []
        for entry in root.findall('atom:entry', NAMESPACES):
            video_id = entry.find('yt:videoId', NAMESPACES).text
            title = entry.find('atom:title', NAMESPACES).text
            link = entry.find('atom:link', NAMESPACES).attrib['href']
            
            media_group = entry.find('media:group', NAMESPACES)
            thumbnail_url = media_group.find('media:thumbnail', NAMESPACES).attrib['url'] if media_group is not None else ""

                    # Im Python-Skript beim Erstellen der Liste den Artist-Namen mitspeichern:
            artist_node = entry.find('atom:author/atom:name', NAMESPACES)
            artist = artist_node.text.replace(' - Topic', '') if artist_node is not None else ""

            videos.append({
                "id": video_id,
                "title": title,
                "artist": artist, # Damit befüllen Sie s.artist im JS automatisch sauber!
                "thumbnail": thumbnail_url
            })


        # NEU: Speichern unter data/music/[PLAYLIST_ID].json
        os.makedirs('data/music', exist_ok=True)
        output_path = f'data/music/{playlist_id}.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)
            
        print(f"Erfolgreich aktualisiert: {playlist_id}")

    except Exception as e:
        print(f"Fehler bei Playlist {playlist_id}: {e}")

def main():
    config_path = 'data/config/music.json'
    
    if not os.path.exists(config_path):
        print(f"Fehler: Konfigurationsdatei unter {config_path} nicht gefunden!")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    playlist_ids = set()
    
    if "favoritesPlaylistId" in config and config["favoritesPlaylistId"]:
        playlist_ids.add(config["favoritesPlaylistId"])
        
    if "playlists" in config:
        for pl in config["playlists"]:
            if "id" in pl and pl["id"]:
                playlist_ids.add(pl["id"])

    print(f"{len(playlist_ids)} Playlists gefunden. Starte Download nach data/music/...")
    for pid in playlist_ids:
        fetch_and_save_playlist(pid)

if __name__ == "__main__":
    main()
