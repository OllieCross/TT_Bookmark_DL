# TikTok Bookmark Downloader

Downloads all bookmarked TikTok videos and photo slideshows from a TikTok data export JSON file or a plain `.txt` list of links.

## What it does

- Parses your TikTok data export JSON (supports all known export formats)
- Or reads a `.txt` file with one link per line - any TikTok link type works: `vm.tiktok.com/...`, `vt.tiktok.com/...`, `tiktok.com/t/...`, `tiktok.com/@user/video/ID`, `tiktok.com/@user/photo/ID`. Short links are resolved via redirect; blank lines and duplicates are ignored
- Reconstructs valid TikTok URLs from raw export links
- Downloads videos as `{id}.mp4` and slideshow images as `{id}.jpg` / `{id}_1.jpg`, `{id}_2.jpg`, ...
- **Stateful** - scans existing output folders on each run and skips already-downloaded content; safe to re-run with an updated JSON export
- Saves any failed URLs to `failed_downloads.txt` for retry

## Requirements

- Python 3.12+
- Or Docker

## Setup

### Run locally

```bash
pip install -r requirements.txt
```

### Dev (linting + pre-commit hooks)

```bash
make install-dev
```

## Usage

### Local

```bash
python downloader.py
# Enter JSON or TXT filename: user_data_tiktok.json   (or links.txt)
```

### Docker

Place your JSON file in the project root, then:

```bash
make docker-run
# Enter JSON filename: user_data_tiktok.json
```

Or directly:

```bash
docker compose run --rm downloader
```

## Output

``` text
TikTokVideos/
    7479393419521969463.mp4
    7485107329533365546.mp4
    ...
TikTokImages/
    7490205924745940229.jpg        # single image
    7490301471850843423_1.jpg      # slideshow slide 1
    7490301471850843423_2.jpg      # slideshow slide 2
    ...
failed_downloads.txt               # URLs that failed, one per line
```

## Getting your TikTok data export

1. Open TikTok app -> Profile -> Settings -> Account -> Download your data
2. Select **JSON** format
3. Wait for the email (can take up to 4 days)
4. Download and extract - use `user_data_tiktok.json`

Expected JSON path the script reads from:

``` text
data["Ads and data"]["Favorite Videos"]["FavoriteVideoList"][n]["Link"]
```

## Retrying failed downloads

After a run, `failed_downloads.txt` contains all URLs that could not be downloaded. Re-run the script and point it at a copy of your JSON that only contains those entries, or handle them manually.

## Make targets

| Command             | Description                          |
|---------------------|--------------------------------------|
| `make install`      | Install runtime deps                 |
| `make install-dev`  | Install dev deps + pre-commit hooks  |
| `make run`          | Run downloader locally               |
| `make lint`         | Run flake8, black check, isort check |
| `make format`       | Auto-format with black + isort       |
| `make type-check`   | Run mypy                             |
| `make check`        | lint + type-check                    |
| `make docker-build` | Build Docker image                   |
| `make docker-run`   | Run in Docker                        |
| `make clean`        | Remove cache dirs and .pyc files.    |

## Notes

- Script waits 10 seconds between requests to avoid rate limiting
- Files are named by TikTok video ID, not sequential numbers
- Personal data files (`*.json`, output folders) are excluded from git via `.gitignore`
