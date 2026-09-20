<img src="https://raw.githubusercontent.com/bretttolbert/moongas-mediatunes-web-vue/refs/heads/main/client/public/moongas.svg" width="128" height="128">

# moongas-mediascripts-python  

> 🚧 **Status: Work in Progress (WIP)**  
> This project is currently under active development. Features, APIs, and documentation are subject to change.

---

## Overview

**Python scripts for working with Moongas media collections.**

### A component of the `moongas` ecosystem of media library tools

- [moongas-collection-demo](https://github.com/bretttolbert/moongas-collection-demo) [![CI](https://github.com/bretttolbert/moongas-collection-demo/actions/workflows/ci.yml/badge.svg)](https://github.com/bretttolbert/moongas-collection-demo/actions/workflows/ci.yml) - Example Moongas media collection (metadata only)
- [moongas-mediatunes-web-vue](https://github.com/bretttolbert/moongas-mediatunes-web-vue) [![CI](https://github.com/bretttolbert/moongas-mediatunes-web-vue/actions/workflows/ci.yml/badge.svg)](https://github.com/bretttolbert/moongas-mediatunes-web-vue/actions/workflows/ci.yml) - A Deno-tooled TypeScript/Vue SPA for Moongas hybrid media collections, pairing with the separate moongas-mediatunes-svc-python-blacksheep backend to seemlessly blend offline and streaming playback
- [moongas-mediatunes-svc-python-blacksheep](https://github.com/bretttolbert/moongas-mediatunes-svc-python-blacksheep) [![CI](https://github.com/bretttolbert/moongas-mediatunes-svc-python-blacksheep/actions/workflows/ci.yml/badge.svg)](https://github.com/bretttolbert/moongas-mediatunes-svc-python-blacksheep/actions/workflows/ci.yml) - Python+BlackSheep API service for Moongas hybrid media collections—backend for Moongas mediatunes web application (moongas-mediatunes-web-vue)
- [moongas-mediascan-go](https://github.com/bretttolbert/moongas-mediascan-go) [![CI](https://github.com/bretttolbert/moongas-mediascan-go/actions/workflows/ci.yml/badge.svg)](https://github.com/bretttolbert/moongas-mediascan-go/actions/workflows/ci.yml) - Golang module to scan media collections and Moongas Yaml metatadata, outputs Moongas database
- [moongas-mediascan-python](https://github.com/bretttolbert/moongas-mediascan-python) [![CI](https://github.com/bretttolbert/moongas-mediascan-python/actions/workflows/ci.yml/badge.svg)](https://github.com/bretttolbert/moongas-mediascan-python/actions/workflows/ci.yml) - Python package for loading Moongas database and Yaml
- [moongas-mediatest-python-pytest](https://github.com/bretttolbert/moongas-mediatest-python-pytest) [![CI](https://github.com/bretttolbert/moongas-mediatest-python-pytest/actions/workflows/ci.yml/badge.svg)](https://github.com/bretttolbert/moongas-mediatest-python-pytest/actions/workflows/ci.yml) - Python tool for enforcing media collection rules (implemented with `pytest`)

## Live Demos
- [Live Demo (hosted on bretttolbert.com)](https://bretttolbert.com/mediaserver)
- [Live Demo (hosted on moongas.org)](https://moongas.org/mediaserver)

# Quick Start

```bash
pip install "git+https://github.com/bretttolbert/moongas-mediascan-python.git[stats]"
```

### (Developer) Clone GitHub repo and install (editable)

```bash
git clone git@github.com:bretttolbert/moongas-mediascan-python.git
cd moongas-mediascan-python
python -m pip install -e ".[dev,llm,stats]"
```

### Optional dependency groups

- `[dev]` - development dependencies (includes `pytest` and `ruff`)
- `[stats]` - statistics script dependencies (includes `matplotlib` and `numpy`)

## Scripts

This Python package includes various console scripts for working with Moongas media collections. The included script `mediascripts` can be used to list them. All scripts accept the `-h` (_help_) command-line argument to display usage information.


```bash
$ mediascripts --h
usage: mediascripts [-h] [--list] [--create-script-symlinks]

Utility for media* console script entry points.

options:
  -h, --help            show this help message and exit
  --list                list all media* console script entry points, grouped by scripts subdirectory
  --create-script-symlinks
                        create hyphenated symlinks in the current directory to every console entry script and every shell script in
                        scripts/shell
$ mediascripts --list
artist:
  artist-countries-to-mapgraph-json
  artist-csv-to-artist-yaml
  artist-yaml-auto-populate
  artist-yaml-reformat-with-files-yaml
  artist-yaml-test-with-files-yaml
  list-missing-region-names
convert:
  convert-covers
  convert-videos
  make-covers-video
copy:
  copy-medialib
dev:
  generate-dataclasses
media_files_yaml:
  list-artists-from-files-yaml
  play-rand-file-from-files-yaml
rename:
  rename-album-files
stats:
  genre-clusters
  mediastats
```
