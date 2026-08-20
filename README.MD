# WordPress ETL Toolkit

A Python ETL pipeline for migrating WordPress export data into structured records you can clean, review, and load into another system.

## What This Project Does

This tool processes WordPress export files in four stages:

1. **Extract**: Reads WordPress XML export data.
2. **Translate**: Converts raw export fields into Python objects with consistent structure.
3. **Sanitize**: Cleans and normalizes names, text, and author relationships.
4. **Format**: Produces SQL-ready output files for import.

In short: it helps turn messy legacy WordPress data into cleaner, migration-ready data.

## Who This Is For

- Teams migrating from WordPress to another CMS or database.
- Developers or data operators who need repeatable cleanup of historical content.
- Anyone who wants a scripted pipeline instead of manual copy/paste migration.

## Requirements

- Python 3.10+
- WordPress export XML files (posts and related author data)

## How to Export Data from WordPress

Use these steps to download the XML files this pipeline expects:

1. Sign in to your WordPress admin dashboard.
2. Open **Tools -> Export**.
3. Choose **All content** (recommended for full migration) or export specific content types as needed.
4. Click **Download Export File** to get the XML export.
5. If your site uses a guest-author plugin, export that author data too (from the plugin's export screen or plugin data tools).
6. Save all exported XML files in a local folder you will use as ETL input.
7. If the export is very large, WordPress may produce multiple XML files. Keep all of them.

## Quick Start

From the `wordpress-etl` directory:

```bash
python3 main.py
```

### Extracting a Second Site (per-run profiles)

The pipeline was written against `thetriangle.org`, and several of its rules are
facts about that specific site rather than about WordPress. Those are now
environment settings, each defaulting to the historical Triangle behaviour, so
an unset environment runs exactly as before. See `Utils/SiteProfile.py` for the
full reasoning and `profiles/rectangle.env` for a worked example.

| Variable | Default | What it controls |
| --- | --- | --- |
| `LEGACY_MEDIA_HOSTS` | `thetriangle.org,therectangle.org` | Domains whose uploads get pulled onto `MEDIA_BASE_URL`. Only list a host whose files are actually in that media tree — listing a live foreign domain rewrites working URLs into 404s. Empty means "rewrite relative paths only". |
| `MIN_BODY_LENGTH` | `100` | Bodies shorter than this are treated as extraction noise. |
| `KEEP_SHORT_POSTS_WITH_IMAGE` | `false` | Exempt a too-short post from the floor when it has a featured image, for sites where an image-only post is real content. |
| `ID_OFFSET` | `0` | Starting point for the generated id sequences. Ids are a per-run counter, not the WP post id, so a second site loaded into the same tables must start past the first one's high-water mark. |
| `CATEGORY_TERM_SOURCE` | `text` | Record a category's display `text` or its `nicename` slug. Slugs survive a site renaming its sections; display text is what the CMS seeds section names from. |

Usage:

```bash
set -a; source profiles/rectangle.env; set +a
python3 main.py
```

### Optional Modes

Generate article embedding SQL output:

```bash
python3 main.py --generate-embeddings
```

Run without interactive prompts (best-guess matching):

```bash
python3 main.py --best-guess
```

Customize embedding settings:

```bash
python3 main.py \
  --generate-embeddings \
  --embedding-model sentence-transformers/paraphrase-MiniLM-L3-v2 \
  --embedding-batch-size 64 \
  --embedding-max-chars 5000
```

## Input and Output

### Input

- WordPress export XML data.

### Output

- Cleaned, transformed data structures used by the pipeline.
- SQL command files/log output suitable for downstream import.
- Optional embedding SQL output at `logs/sql/article_embeddings.sql`.

## Notes

- `--best-guess` mode resolves ambiguous author matches automatically using similarity scoring.
- Those match decisions are cached so future runs avoid repeating the same prompts.

## Disclaimer

This repository contains migration logic that reflects one real-world WordPress dataset. You may need to adjust sanitization and mapping rules for your own content model.
