import os
import re
import sys
import json
import time
import requests
from bs4 import BeautifulSoup

VIDEOS_FOLDER = "TikTokVideos"
IMAGES_FOLDER = "TikTokImages"
FAILED_FILE = "failed_downloads.txt"
API_URL = "https://tikdownloader.io/api/ajaxSearch"
DELAY = 10


def extract_tiktok_id(url):
    match = re.search(r'/(\d{10,})', url)
    return match.group(1) if match else None


def get_downloaded_ids():
    """Scan output folders and return set of already-downloaded TikTok IDs."""
    downloaded = set()
    id_pattern = re.compile(r'^(\d{10,})')
    for folder in (VIDEOS_FOLDER, IMAGES_FOLDER):
        if not os.path.isdir(folder):
            continue
        for fname in os.listdir(folder):
            m = id_pattern.match(fname)
            if m:
                downloaded.add(m.group(1))
    return downloaded


def download_content(url, session, tiktok_id):
    payload = {"q": url, "lang": "en"}

    try:
        response = session.post(API_URL, data=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            print(f"  API error: status={data.get('status')}")
            return False

        html = data.get("data", "")

        # Try video (MP4 HD)
        video_link = None
        for part in html.split('<p><a href="'):
            if "Download MP4 HD" in part:
                video_link = part.split('"')[0]
                break

        if video_link:
            r = session.get(video_link, stream=True, timeout=60)
            r.raise_for_status()
            out_path = os.path.join(VIDEOS_FOLDER, f"{tiktok_id}.mp4")
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    f.write(chunk)
            print(f"  Saved video: {tiktok_id}.mp4")
            return True

        # Try slideshow/images
        soup = BeautifulSoup(html, "html.parser")
        image_links = soup.find_all(
            "a", class_="abutton is-success is-fullwidth btn-premium mt-3"
        )

        if image_links:
            for i, link in enumerate(image_links, start=1):
                file_url = link.get("href")
                if not file_url:
                    continue
                r = session.get(file_url, stream=True, timeout=60)
                r.raise_for_status()
                suffix = f"_{i}" if len(image_links) > 1 else ""
                out_path = os.path.join(IMAGES_FOLDER, f"{tiktok_id}{suffix}.jpg")
                with open(out_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        f.write(chunk)
                print(f"  Saved image: {tiktok_id}{suffix}.jpg")
            return True

        print("  No downloadable content found")
        return False

    except requests.exceptions.RequestException as e:
        print(f"  Request failed: {e}")
        return False


def reconstruct_url(raw_url):
    """Convert tiktokv.com/share/video/ID -> tiktok.com/@/video/ID."""
    return raw_url.replace("tiktokv", "tiktok").replace("share", "@")


def load_urls_from_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Primary TikTok data export path (structure varies by export version)
    for path in [
        ("Likes and Favorites", "Favorite Videos", "FavoriteVideoList"),  # 2024+ export
        ("Ads and data", "Favorite Videos", "FavoriteVideoList"),          # older export
        ("Activity", "Favorite Videos", "FavoriteVideoList"),              # oldest export
    ]:
        try:
            node = data
            for key in path:
                node = node[key]
            urls = [reconstruct_url(item["Link"]) for item in node if "Link" in item]
            if urls:
                return urls
        except (KeyError, TypeError):
            continue

    # Fallback: recursively search for any list of dicts with "Link" keys
    def find_links(obj):
        if isinstance(obj, list):
            links = [item["Link"] for item in obj if isinstance(item, dict) and "Link" in item]
            if links:
                return [reconstruct_url(u) for u in links]
            for item in obj:
                result = find_links(item)
                if result:
                    return result
        elif isinstance(obj, dict):
            for val in obj.values():
                result = find_links(val)
                if result:
                    return result
        return []

    urls = find_links(data)
    if urls:
        return urls

    print("Could not find bookmark URLs in JSON. Expected structure:")
    print('  data["Ads and data"]["Favorite Videos"]["FavoriteVideoList"][n]["Link"]')
    sys.exit(1)


def main():
    json_file = input("Enter JSON filename: ").strip()
    if not os.path.exists(json_file):
        print(f"File not found: {json_file}")
        sys.exit(1)

    os.makedirs(VIDEOS_FOLDER, exist_ok=True)
    os.makedirs(IMAGES_FOLDER, exist_ok=True)

    downloaded_ids = get_downloaded_ids()

    urls = load_urls_from_json(json_file)
    total = len(urls)

    pending = []
    for url in urls:
        tiktok_id = extract_tiktok_id(url)
        if tiktok_id and tiktok_id in downloaded_ids:
            continue
        pending.append((url, tiktok_id))

    skipped = total - len(pending)
    print(f"Bookmarks in JSON : {total}")
    print(f"Already downloaded: {skipped}")
    print(f"To download       : {len(pending)}\n")

    if not pending:
        print("Nothing new to download.")
        return

    failed = []

    with requests.Session() as session:
        for i, (url, tiktok_id) in enumerate(pending, start=1):
            print(f"[{i}/{len(pending)}] {url}")
            if not tiktok_id:
                print("  Could not extract ID from URL, skipping")
                failed.append(url)
                continue

            success = download_content(url, session, tiktok_id)
            if not success:
                failed.append(url)

            if i < len(pending):
                time.sleep(DELAY)

    print()
    if failed:
        with open(FAILED_FILE, "w") as f:
            f.write("\n".join(failed))
        print(f"{len(failed)} failed - written to {FAILED_FILE}")
    else:
        print("All downloads successful!")

    print(f"Videos -> {VIDEOS_FOLDER}/")
    print(f"Images -> {IMAGES_FOLDER}/")


if __name__ == "__main__":
    main()
