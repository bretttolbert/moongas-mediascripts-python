"""
Usage: python scripts/artist_yaml_llm_auto_populate.py [options]

It expects the environment variable MOONGAS_COLLECTION_ROOTDIR to be set,
pointing to the root directory of the Moongas collection.

MOONGAS_COLLECTION_ROOTDIR=$MOONGAS_COLLECTION_DEMO python artist_yaml_llm_auto_populate.py

MOONGAS_COLLECTION_ROOTDIR=$MOONGAS_COLLECTION_DEMO python artist_yaml_llm_auto_populate.py --clean

Command line options:
  --clean    Remove all backup files before processing.
  --sleep    Pause execution for a short period before processing.
  --help     Show this help message and exit.

"""

import argparse
import logging
import os
import random
import re
import shutil
import tempfile
import time
from pathlib import Path

from dataclass_wizard.v0.errors import MissingFields
from openai import APIStatusError, OpenAI
from tqdm import tqdm

from mediascripts.artist_yaml_file import ArtistYamlFile
from mediascripts.artist_yaml_file_validator import (
    validate_artist_yaml_content,
    validate_artist_yaml_file,
)

# Configure with LOG_LEVEL=DEBUG for additional diagnostic detail.
logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

LETTER_DIRS_FOR_REFERENCE_EXAMPLES = ["A"]

LETTER_DIRS_NEEDING_WORK = [
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
]

assert not (
    set(LETTER_DIRS_FOR_REFERENCE_EXAMPLES) & set(LETTER_DIRS_NEEDING_WORK)
), "Reference examples and needing work arrays intersect!"

# Configure an OpenAI-compatible provider. LLM_* variables take precedence;
# the GITHUB_* variables remain supported for existing GitHub Models setups.
BASE_URL = os.environ.get(
    "LLM_BASE_URL",
    os.environ.get("GITHUB_MODELS_BASE_URL", "https://models.github.ai/inference"),
)
MODEL_NAME = os.environ.get(
    "LLM_MODEL", os.environ.get("GITHUB_MODEL", "openai/gpt-4o-mini")
)
api_key = os.environ.get(
    "LLM_API_KEY", os.environ.get("GITHUB_TOKEN", os.environ.get("OPENAI_API_KEY"))
)
client = OpenAI(base_url=BASE_URL, api_key=api_key)

# Train on all existing artist.yaml files.
MOONGAS_COLLECTION_ROOTDIR = os.environ.get(
    "MOONGAS_COLLECTION_ROOTDIR", "../../moongas-collection-demo/data"
)

# Define strict system instructions to prevent conversational text in the response
SYSTEM_PROMPT = """You are an automated data-filling assistant. 
Your job is to read the provided incomplete YAML file and fill in the missing values or inferred fields.
Maintain the exact schema. Return ONLY the valid YAML content. 
Do not include markdown code blocks (like ```yaml), explanations, or opening/closing text."""


def parse_boolean(value: str) -> bool:
    """Parse a command-line boolean value."""
    normalized_value = value.lower()
    if normalized_value == "true":
        return True
    if normalized_value == "false":
        return False
    raise argparse.ArgumentTypeError("expected true or false")


def load_reference_examples(letters_dirs_to_work: list[str]) -> str:
    """Load complete YAML files that demonstrate the desired output format.
    Currently it recursively loads all artist.yaml files under the EXAMPLES_ROOTDIR
    Only files named "artist.yml" in directories starting with "A" are considered.
    This avoids maximum context length issues by limiting the number of examples loaded.
    Also the ones starting with the letter 'A' are considered the primary examples
    because I tagged them semi-manually using Copilot Chat first.
    """
    if not os.path.isdir(MOONGAS_COLLECTION_ROOTDIR):
        logger.warning(
            "Reference examples directory not found: %s", MOONGAS_COLLECTION_ROOTDIR
        )
        return ""

    example_paths = [
        os.path.join(root, filename)
        for root, _, filenames in os.walk(MOONGAS_COLLECTION_ROOTDIR)
        for filename in filenames
        if filename == "artist.yml"
        and os.path.basename(root)[0] in letters_dirs_to_work
    ]

    examples: list[str] = []
    for example_path in sorted(example_paths):
        filename = os.path.relpath(example_path, MOONGAS_COLLECTION_ROOTDIR)
        with open(example_path, "r", encoding="utf-8") as f:
            examples.append(f"Example: {filename}\n{f.read()}")

    logger.info(
        "Loaded %d reference example(s) from %s",
        len(examples),
        MOONGAS_COLLECTION_ROOTDIR,
    )
    reference_text = "\n\n".join(examples)
    logger.info("Reference example content size: %d characters", len(reference_text))
    return reference_text


def load_input_files(letters_dirs_to_work: list[str]) -> list[Path]:
    """Find artist.yml files in directories selected by their first letter."""
    input_paths = [
        Path(root) / filename
        for root, _, filenames in os.walk(MOONGAS_COLLECTION_ROOTDIR)
        for filename in filenames
        if filename == "artist.yml"
        and os.path.basename(root)[0] in letters_dirs_to_work
    ]

    input_paths = sorted(input_paths)
    logger.info("Found %d YAML input file(s)", len(input_paths))
    for input_path in input_paths:
        logger.debug("Queued input file: %s", input_path)
    return input_paths


def clean_backup_files(root_dir: Path) -> int:
    """Delete all backup files beneath the collection root directory."""
    deleted_count = 0
    for backup_path in root_dir.rglob("*.bak"):
        if not backup_path.is_file():
            continue
        backup_path.unlink()
        deleted_count += 1
        logger.info("Deleted backup file: %s", backup_path)

    logger.info("Deleted %d backup file(s) beneath %s", deleted_count, root_dir)
    return deleted_count


def try_load_artist_yaml_for_skip(input_path: Path) -> bool:
    """Return whether strict loading succeeds before deciding to skip a file."""
    try:
        getattr(ArtistYamlFile, "from_yaml")(input_path.read_text(encoding="utf-8"))
        return True
    except MissingFields as exception:
        logger.warning(
            "Artist YAML requires LLM processing: %s is missing fields %s; "
            "rescued raw data: %s",
            input_path,
            exception.missing_fields,
            exception.obj,
        )
    except Exception as exception:
        logger.warning(
            "Artist YAML requires LLM processing: could not strictly load %s: %s",
            input_path,
            exception,
        )
    return False


def validate_llm_yaml_content(content: str, filename: str) -> None:
    """Validate LLM YAML syntax while allowing incomplete schema fields to be saved."""
    try:
        validate_artist_yaml_content(content)
    except ValueError as exception:
        logger.warning(
            "[%s] LLM YAML has validation warnings; saving response for further processing: %s",
            filename,
            exception,
        )
    else:
        logger.info("[%s] YAML validation passed", filename)


def remove_duplicate_members_lists(content: str) -> str:
    """Merge duplicate direct ``members`` lists under ``artistData``."""
    artist_data_match = re.search(
        r"^(?P<indent>[ \t]*)artistData:[ \t]*$", content, re.MULTILINE
    )
    if artist_data_match is None:
        return content

    artist_data_indent = artist_data_match.group("indent")
    first_member_match = re.search(
        rf"^(?P<indent>{re.escape(artist_data_indent)}[ \t]+)members:(?:[ \t]+[^#]*)?[ \t]*$",
        content[artist_data_match.end() :],
        re.MULTILINE,
    )
    if first_member_match is None:
        return content

    member_indent = first_member_match.group("indent")
    member_key = re.compile(
        rf"^{re.escape(member_indent)}members:(?:[ \t]+[^#]*)?[ \t]*$"
    )
    lines = content.splitlines(keepends=True)
    artist_data_line = content[: artist_data_match.start()].count("\n")
    found_members = False
    cleaned_lines: list[str] = []
    line_number = 0

    while line_number < len(lines):
        line = lines[line_number]
        if line_number <= artist_data_line or not member_key.match(line):
            cleaned_lines.append(line)
            line_number += 1
            continue

        if not found_members:
            found_members = True
            cleaned_lines.append(line)
            line_number += 1
            continue

        line_number += 1

    return "".join(cleaned_lines)


def remove_duplicate_members_lists_from_root(root_dir: Path) -> int:
    """Remove duplicate ``members`` lists from every artist YAML under a root."""
    artist_yaml_paths = sorted(root_dir.rglob("artist.yml"))
    logger.info(
        "Scanning %d artist YAML file(s) under %s for duplicate members lists",
        len(artist_yaml_paths),
        root_dir,
    )
    cleaned_count = 0
    for artist_yaml_path in artist_yaml_paths:
        logger.debug("Checking %s for duplicate members lists", artist_yaml_path)
        raw_yaml = artist_yaml_path.read_text(encoding="utf-8")
        normalized_yaml = remove_duplicate_members_lists(raw_yaml)
        if normalized_yaml == raw_yaml:
            logger.debug("No duplicate members lists found in %s", artist_yaml_path)
            continue
        artist_yaml_path.write_text(normalized_yaml, encoding="utf-8")
        cleaned_count += 1
        logger.info(
            "Merged duplicate members lists and overwrote %s (%d -> %d characters)",
            artist_yaml_path,
            len(raw_yaml),
            len(normalized_yaml),
        )
    logger.info(
        "Completed duplicate members scan: %d modified, %d unchanged",
        cleaned_count,
        len(artist_yaml_paths) - cleaned_count,
    )
    return cleaned_count


def process_artist_yaml_file(
    input_path: Path,
    reference_examples: str,
    file_number: int,
    total_files: int,
    llm_enabled: bool = True,
) -> bool:
    filename = input_path.name
    started_at = time.monotonic()
    temporary_path: Path | None = None

    logger.info("[%d/%d] Processing %s", file_number, total_files, input_path)

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            raw_yaml = f.read()
        logger.debug("Read %d characters from %s", len(raw_yaml), input_path)
        logger.info("[%s] YAML before modification:\n%s", filename, raw_yaml)

        if not llm_enabled:
            logger.info("[%s] LLM lookup disabled; leaving file unchanged", filename)
            return True

        # Call the LLM to fill in the info
        prompt = (
            "Use these completed YAML files as reference examples.\n\n"
            f"{reference_examples}\n\n"
            "Fill in this YAML file:\n\n"
            f"{raw_yaml}"
            if reference_examples
            else f"Fill in this YAML file:\n\n{raw_yaml}"
        )
        logger.info(
            "[%s] Sending request to model %s (%d prompt characters)",
            filename,
            MODEL_NAME,
            len(prompt),
        )
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            model=MODEL_NAME,
            temperature=0.2,
        )
        logger.info("[%s] Received model response", filename)

        content = response.choices[0].message.content
        if content is None:
            raise ValueError("Model response did not contain YAML content")
        completed_yaml = remove_duplicate_members_lists(content.strip())
        if not completed_yaml:
            raise ValueError("Model response contained empty YAML content")
        logger.info(
            "[%s] Model response contains %d characters", filename, len(completed_yaml)
        )

        validate_llm_yaml_content(completed_yaml, filename)
        logger.info("[%s] YAML after modification:\n%s", filename, completed_yaml)

        backup_path = input_path.with_name(f"{input_path.name}.bak")
        if completed_yaml == raw_yaml.strip():
            logger.info(
                "[%s] LLM result is unchanged; leaving source file untouched", filename
            )
            if backup_path.exists():
                backup_path.unlink()
                logger.info("[%s] Removed stale backup file %s", filename, backup_path)
            return True

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=input_path.parent,
            prefix=f".{input_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_file.write(completed_yaml)
            temporary_path = Path(temporary_file.name)
        logger.debug("[%s] Staged generated YAML at %s", filename, temporary_path)

        shutil.copy2(input_path, backup_path)
        logger.info("[%s] Backed up original file to %s", filename, backup_path)

        os.replace(temporary_path, input_path)
        temporary_path = None
        logger.debug("[%s] Wrote generated YAML to %s", filename, input_path)

        duration = time.monotonic() - started_at
        logger.info(
            "[%s] Saved %d characters to %s in %.2f seconds",
            filename,
            len(completed_yaml),
            input_path,
            duration,
        )
        logger.info(
            "Diff tool command to compare the original YAML with the generated YAML: \n\n"
            'meld "%s" "%s"\n\n',
            backup_path,
            input_path,
        )
        logger.info("[%s] Processing completed successfully", filename)
        return True

    except APIStatusError as e:
        duration = time.monotonic() - started_at
        if e.status_code == 410:
            logger.error(
                "[%s] Provider returned HTTP 410 after %.2f seconds: "
                "the service is unavailable or retired. Set LLM_BASE_URL, "
                "LLM_API_KEY, and LLM_MODEL to use another provider.",
                filename,
                duration,
            )
        else:
            logger.exception(
                "[%s] API request failed after %.2f seconds (HTTP %s): %s",
                filename,
                duration,
                e.status_code,
                e,
            )
    except Exception as e:
        duration = time.monotonic() - started_at
        logger.exception(
            "[%s] Failed after %.2f seconds (%s): %s",
            filename,
            duration,
            type(e).__name__,
            e,
        )
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
            logger.debug("[%s] Removed staged temporary file", filename)
    return False


def process_artist_yaml_files(
    path: Path,
    letters_dirs_to_work: list[str],
    processed_files: set[Path],
    llm_enabled: bool = True,
) -> bool | None:
    logger.info("Starting YAML processing")
    logger.info("Input directory: %s", path.resolve())
    logger.info("Output directory: %s", path.resolve())
    logger.info("API endpoint: %s", BASE_URL)
    logger.info("Model: %s", MODEL_NAME)

    if not api_key:
        logger.warning("GITHUB_TOKEN is not set; the API request will likely fail")

    if not path.is_dir():
        logger.error("Input directory does not exist: %s", path.resolve())
        return False

    input_files = [
        input_file
        for input_file in load_input_files(letters_dirs_to_work)
        if input_file not in processed_files
    ]
    if not input_files:
        logger.warning(
            "No unprocessed input files remain for letter directories: %s",
            letters_dirs_to_work,
        )
        return None

    for input_file in input_files:
        if not try_load_artist_yaml_for_skip(input_file):
            continue
        artists_missing: list[str] = []
        exceptions: list[tuple[Path, Exception]] = []
        validate_artist_yaml_file(
            input_file.parent.name,
            input_file.parent,
            [str(input_file)],
            artists_missing,
            exceptions,
        )
        if not artists_missing and not exceptions:
            processed_files.add(input_file)
            logger.info("Skipping already-valid artist YAML file: %s", input_file)
        else:
            if artists_missing:
                logger.warning(
                    "Artist YAML validation failed for %s: artist.yml is missing",
                    input_file,
                )
            for exception_path, exception in exceptions:
                logger.warning(
                    "Artist YAML validation failed for %s: %s",
                    exception_path,
                    exception,
                )

    input_files = [
        input_file for input_file in input_files if input_file not in processed_files
    ]
    if not input_files:
        logger.info("All matching files are already valid; exiting loop")
        return None

    reference_examples = load_reference_examples(LETTER_DIRS_FOR_REFERENCE_EXAMPLES)

    logger.info(
        "Selecting 1 random file from %d available file(s) with %d reference characters",
        len(input_files),
        len(reference_examples),
    )
    selected_file = random.choice(input_files)
    processed_files.add(selected_file)
    logger.info("Selected random input file: %s", selected_file)
    results = [
        process_artist_yaml_file(
            selected_file, reference_examples, 1, 1, llm_enabled=llm_enabled
        )
    ]
    succeeded = sum(results)
    failed = len(results) - succeeded
    logger.info("Batch complete: %d succeeded, %d failed", succeeded, failed)
    return succeeded > 0 and failed == 0


def clean():
    logger.info(
        "Cleaning up backup files in the collection root directory: %s",
        MOONGAS_COLLECTION_ROOTDIR,
    )
    count_removed = 0
    for backup_file in Path(MOONGAS_COLLECTION_ROOTDIR).rglob("*.bak"):
        try:
            backup_file.unlink()
            count_removed += 1
            logger.info("Removed backup file: %s", backup_file)
        except Exception as e:
            logger.warning("Failed to remove backup file %s: %s", backup_file, e)
    logger.info("Removed a total of %d backup file(s)", count_removed)


def main_loop(sleep_between_files: int, llm_enabled: bool = True):
    processed_files: set[Path] = set()
    letter_dirs = LETTER_DIRS_NEEDING_WORK
    collection_root = Path(MOONGAS_COLLECTION_ROOTDIR)
    cleaned_count = remove_duplicate_members_lists_from_root(collection_root)
    logger.info(
        "Pre-pass removed duplicate members lists from %d artist YAML file(s)",
        cleaned_count,
    )
    if not llm_enabled:
        logger.info("LLM lookup disabled; exiting after duplicate members pre-pass")
        return
    total_files = len(load_input_files(letter_dirs))
    with tqdm(total=total_files, desc="Processing files", unit="file") as progress:
        while True:
            processed_count = len(processed_files)
            logger.info(
                "Starting processing loop for letter directories: %s", letter_dirs
            )
            result = process_artist_yaml_files(
                collection_root, letter_dirs, processed_files, llm_enabled=llm_enabled
            )
            progress.update(len(processed_files) - processed_count)
            if result is None:
                logger.info("All matching files have been processed; exiting loop")
                return
            logger.info(
                "Processing loop complete; sleeping for %d seconds",
                sleep_between_files,
            )
            for _ in tqdm(
                range(sleep_between_files),
                desc="Sleeping",
                bar_format="{desc}: |{bar}| {remaining} remaining",
                leave=False,
            ):
                time.sleep(1)


def main():
    parser = argparse.ArgumentParser(
        description="Process artist YAML files or clean up backup files."
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean backup files and exit instead of starting the processing loop.",
    )
    parser.add_argument(
        "--sleep",
        type=int,
        default=30,
        help="Seconds to sleep between processing loops (default: 30).",
    )
    parser.add_argument(
        "--llm",
        type=parse_boolean,
        default=True,
        metavar="true|false",
        help="Enable LLM lookups (default: true). Use --llm=false for pre-pass only.",
    )
    args = parser.parse_args()

    if args.clean:
        clean()
    else:
        try:
            main_loop(args.sleep, args.llm)
        except KeyboardInterrupt:
            logger.info("Interrupted by user; exiting")


if __name__ == "__main__":
    main()
