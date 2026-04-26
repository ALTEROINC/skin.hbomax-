#!/usr/bin/env python3

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


SKIN_ID = "skin.hbomax"
REPO_ID = "repository.hbomax"
XML_DECLARATION = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'


def fail(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_addon_version(addon_xml_path: Path) -> str:
    try:
        tree = ET.parse(addon_xml_path)
    except ET.ParseError as exc:
        fail(f"failed to parse {addon_xml_path}: {exc}")
    root = tree.getroot()
    version = root.attrib.get("version", "").strip()
    if not version:
        fail(f"missing version attribute in {addon_xml_path}")
    return version


def package_skin(root_dir: Path, skin_dir: Path, repo_dir: Path) -> tuple[Path, str]:
    addon_xml_path = skin_dir / "addon.xml"
    if not addon_xml_path.is_file():
        fail(f"missing {addon_xml_path}")

    version = read_addon_version(addon_xml_path)
    zip_output_dir = repo_dir / SKIN_ID
    zip_output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = zip_output_dir / f"{SKIN_ID}-{version}.zip"

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        staged_skin_dir = temp_dir / SKIN_ID
        staged_skin_dir.mkdir(parents=True, exist_ok=True)

        rsync_cmd = [
            "rsync",
            "-av",
            "--exclude=.git",
            "--exclude=.github",
            "--exclude=tools",
            "--exclude=*.md",
            "--exclude=*.py",
            "--exclude=*.txt",
            f"{skin_dir}/",
            f"{staged_skin_dir}/",
        ]
        zip_cmd = ["zip", "-r", str(archive_path), SKIN_ID]

        try:
            subprocess.run(rsync_cmd, check=True, cwd=temp_dir)
            subprocess.run(zip_cmd, check=True, cwd=temp_dir)
        except subprocess.CalledProcessError as exc:
            fail(f"failed to package {SKIN_ID}: {exc}")

    return archive_path, version


def collect_addon_xml_strings(root_dir: Path) -> list[str]:
    addon_xml_strings: list[str] = []

    for child in sorted(root_dir.iterdir(), key=lambda path: path.name):
        if not child.is_dir():
            continue
        if child.name == REPO_ID:
            continue

        addon_xml_path = child / "addon.xml"
        if not addon_xml_path.is_file():
            continue

        text = addon_xml_path.read_text(encoding="utf-8").strip()
        if text.startswith("<?xml"):
            text = text.split("?>", 1)[1].strip()
        addon_xml_strings.append(text)

    if not addon_xml_strings:
        fail(f"no addon.xml files found in {root_dir}")

    return addon_xml_strings


def write_addons_xml(root_dir: Path, repo_dir: Path) -> Path:
    addon_xml_strings = collect_addon_xml_strings(root_dir)
    addons_xml_path = repo_dir / "addons.xml"
    addons_xml = XML_DECLARATION + "<addons>\n" + "\n".join(addon_xml_strings) + "\n</addons>\n"
    addons_xml_path.write_text(addons_xml, encoding="utf-8")
    return addons_xml_path


def write_md5(addons_xml_path: Path) -> Path:
    md5_path = addons_xml_path.with_suffix(addons_xml_path.suffix + ".md5")
    digest = hashlib.md5(addons_xml_path.read_bytes()).hexdigest()
    md5_path.write_text(digest, encoding="utf-8")
    return md5_path


def main() -> None:
    root_dir = Path.cwd()
    skin_dir = root_dir / SKIN_ID
    repo_dir = root_dir / REPO_ID

    if not skin_dir.is_dir():
        fail(f"expected {skin_dir} to exist")
    if not repo_dir.is_dir():
        fail(f"expected {repo_dir} to exist")

    archive_path, version = package_skin(root_dir, skin_dir, repo_dir)
    addons_xml_path = write_addons_xml(root_dir, repo_dir)
    md5_path = write_md5(addons_xml_path)

    packaged_addons = [
        child.name
        for child in sorted(root_dir.iterdir(), key=lambda path: path.name)
        if child.is_dir() and child.name != REPO_ID and (child / "addon.xml").is_file()
    ]

    print("Repository build complete")
    print(f"Packaged skin: {SKIN_ID} v{version}")
    print(f"Zip file: {archive_path}")
    print(f"addons.xml: {addons_xml_path}")
    print(f"addons.xml.md5: {md5_path}")
    print(f"Addons indexed: {', '.join(packaged_addons)}")


if __name__ == "__main__":
    main()
