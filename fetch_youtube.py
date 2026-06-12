import urllib.request
import xml.etree.ElementTree as ET
import json
import os

# Korrekte Namespace-URIs aus dem echten YouTube-RSS-Format
NAMESPACES = {
    'atom':  'http://www.w3.org/2005/Atom',
    'yt':    'http://www.youtube.com/xml/schemas/2015',
    'media': 'http://search.yahoo.com/mrss/'
}

def fetch_and_save_playlist(playlist_id):
    # Korrekte YouTube RSS-Feed URL für Playlists
    url = f"https://www.youtube.com/feeds/videos.xml?playlist_id={playlist_id}"    
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        response = urllib.request.urlopen(req, timeout=15)
        xml_data = response.read()
        root = ET.fromstring(xml_data)

        videos = []
        for entry in root.findall('atom:entry', NAMESPACES):
            vid_node   = entry.find('yt:videoId', NAMESPACES)
            title_node = entry.find('atom:title', NAMESPACES)
            author_node = entry.find('atom:author/atom:name', NAMESPACES)
            media_group = entry.find('media:group', NAMESPACES)

            video_id = vid_node.text if vid_node is not None else ""
            title    = title_node.text if title_node is not None else ""
            artist   = author_node.text.replace(' - Topic', '') if author_node is not None else ""

            thumbnail_url = ""
            if media_group is not None:
                thumb = media_group.find('media:thumbnail', NAMESPACES)
                if thumb is not None:
                    thumbnail_url = thumb.attrib.get('url', '')

            videos.append({
                "id":        video_id,
                "title":     title,
                "artist":    artist,
                "thumbnail": thumbnail_url
            })

        os.makedirs('data/music', exist_ok=True)
        output_path = f'data/music/{playlist_id}.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)

        print(f"Erfolgreich aktualisiert: {playlist_id} ({len(videos)} Videos)")

    except Exception as e:
        print(f"Fehler bei Playlist {playlist_id}: {e}")
        os.makedirs('data/music', exist_ok=True)
        output_path = f'data/music/{playlist_id}.json'
        if not os.path.exists(output_path):
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

def main():
    config_path = 'data/config/music.json'

    if not os.path.exists(config_path):
        print(f"Fehler: Konfigurationsdatei unter {config_path} nicht gefunden!")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    playlist_ids = set()

    if config.get("favoritesPlaylistId"):
        playlist_ids.add(config["favoritesPlaylistId"])

    for pl in config.get("playlists", []):
        if pl.get("id"):
            playlist_ids.add(pl["id"])

    print(f"{len(playlist_ids)} Playlists gefunden. Starte Download nach data/music/...")
    for pid in playlist_ids:
        fetch_and_save_playlist(pid)

if __name__ == "__main__":
    main()