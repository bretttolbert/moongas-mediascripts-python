#!/usr/bin/env python
"""
Walks the files in the given directory,
renames files in accordance with various rules.
Rules:
- Strips any square bracket text like '[Official Music Video]'
- Replaces curved apostrophe with straight apostrophe
- Strips stupid little emojis like '🔄'
- etc.
"""

import argparse
import os
import re

from mediascan.utils.path.album_path import AlbumPath, AlbumPathBuilder


# Matches standard emoji ranges, symbols, and variation selectors e.g. '🔄'
emoji_pattern = re.compile(
    r"\s*[\U0001F000-\U0001FFFF\u2600-\u27BF\u2300-\u23FF]\s*"
)

# pattern/substitution
patterns: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\s*\[.*?\]"), ""),
    (re.compile(r"ft_"), "ft"),
    (re.compile(r"ft\."), "ft"),
    (re.compile(r"\.(?!.{3}$)"), "_"),
    (re.compile(r"’"), "'"),
    (re.compile(r"´"), "'"),
    (re.compile(r"“"), '"'),
    (re.compile(r"”"), '"'),
    (re.compile(r"\$"), "_"),
    (re.compile(r"&"), "and"),
    (re.compile(r"＊"), "_"),
    (re.compile(r"\s*\(Official Music Video\)"), ""),
    (re.compile(r"\s*\(Visualizer\)"), ""),
    (re.compile(r"\s*\(\)"), ""),
    (re.compile(r"#"), "no "),
    (re.compile(rf"\s*(?:{emoji_pattern.pattern})\s*"), ""),
]

def prepare_rename_tasks(album_path: AlbumPath) -> list[tuple[str, str]]:
    rename_tasks : list[tuple[str, str]] = []
    for _, _, files in os.walk(album_path.path):
        for filename in files:
            updated_filename = filename
            # Apply all applicable replacements, then add the updated filename
            # to the rename tasks queue (if any updates were made)

            # Add custom patterns

            # Custom pattern #1
            # Remove artist name e.g. " - Lil Wayne"
            # E.g. "03 - Lil Wayne - MegaMan.mp3" -> "03 - MegaMan.mp3"
            patterns.append(
                (
                    re.compile(r"\s*-?\s*" + re.escape(album_path.artist_dirname)),
                    "",
                )
            )

            # Perform regex pattern/sub replacements
            for pattern, replacement in patterns:
                if re.search(pattern, filename):
                    updated_filename = re.sub(pattern, replacement, updated_filename)

            # Finally, append a rename task if any updates were made
            if updated_filename != filename:
                rename_tasks.append((filename, updated_filename))
    return rename_tasks


def perform_rename_tasks(
    album_path: AlbumPath,
    rename_tasks: list[tuple[str, str]],
    dry_run: bool = False,
) -> None:
    for original, updated in rename_tasks:
        if not dry_run:
            os.rename(os.path.join(album_path.path, original), os.path.join(album_path.path, updated))
        print(f'Renamed "{original}" -> "{updated}"')


def rename_album_files(album_path_raw: str, dry_run: bool = False):
    if dry_run:
        print("----BEGIN DRY RUN----")
    album_path = AlbumPathBuilder.of(album_path_raw)
    print("Parsed album path:")
    print(album_path)
    if not album_path.valid:
        print("Album path is invalid, rename operation aborted")
    else:
        print("Album path is valid, proceeding with rename operation")
        rename_tasks = prepare_rename_tasks(album_path)
        if len(rename_tasks):
            perform_rename_tasks(album_path, rename_tasks, dry_run)
        print(f"{len(rename_tasks)} files renamed")
    if dry_run:
        print("----END DRY RUN----")


def main():
    parser = argparse.ArgumentParser(description="Rename album files in a directory.")
    parser.add_argument("directory", help="Path to the directory containing files")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate actions without making actual file changes",
    )
    
    args = parser.parse_args()
    rename_album_files(args.directory, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
