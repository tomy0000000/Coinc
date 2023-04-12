import json
import os
import pathlib
import plistlib
import re
import shutil
import sys
from uuid import uuid4

from coinc.alfred import persisted_data

UUID_MATCHER = re.compile(
    r"^[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[0-9a-f]{12}$"
)
NORMAL_KEYWORDS = ["coinc", "cur-ref", "cur-index"] + list(map(str, range(10)))
BEGIN_YPOS = 1540
GAP = 130


def load() -> tuple[dict, dict, dict]:
    with open("info.plist", "rb") as f:
        content = plistlib.load(f)
    aliases = persisted_data("alias")
    with open("currencies.json", "rb") as f:
        currencies = json.load(f)
    return content, aliases, currencies


def save(content):
    with open("info.plist", "wb") as f:
        plistlib.dump(content, f)


def clear_icons():
    for file in pathlib.Path(".").glob("*.png"):
        if UUID_MATCHER.match(file.stem):
            os.remove(file)


def copy_icon(currency: str, uid: str):
    try:
        shutil.copyfile(f"flags/{currency}.png", f"{uid}.png")
    except FileNotFoundError:
        pass


def add_alias_entry(
    blocks, ui_blocks, connections, currencies, alias, currency, ypos, junction_uid
):
    argvar_uid = str(uuid4())
    keyword_uid = str(uuid4())

    # Arg and Var Block
    blocks.append(
        {
            "config": {
                "argument": f"{alias}{{query}}",
                "passthroughargument": False,
                "variables": {},
            },
            "type": "alfred.workflow.utility.argument",
            "uid": argvar_uid,
            "version": 1,
        }
    )
    ui_blocks[argvar_uid] = {"xpos": 265.0, "ypos": ypos + 30}
    connections[argvar_uid] = [
        {
            "destinationuid": junction_uid,
            "modifiers": 0,
            "modifiersubtext": "",
            "vitoclose": False,
        }
    ]

    # Keyword Block
    blocks.append(
        {
            "config": {
                "argumenttype": 0,
                "keyword": alias,
                "subtext": "Convert {query} to your favorite currencies with Coinc",
                "text": currencies[currency],
                "withspace": False,
            },
            "type": "alfred.workflow.input.keyword",
            "uid": keyword_uid,
            "version": 1,
        }
    )
    ui_blocks[keyword_uid] = {"xpos": 30.0, "ypos": ypos}
    connections[keyword_uid] = [
        {
            "destinationuid": argvar_uid,
            "modifiers": 0,
            "modifiersubtext": "",
            "vitoclose": True,
        }
    ]
    copy_icon(currency, keyword_uid)


def main():
    content, aliases, currencies = load()
    blocks = content["objects"]
    ui_blocks = content["uidata"]
    connections = content["connections"]

    remove_block_indexes = []
    remove_blocks = []
    junction_uid = None
    for i, block in enumerate(blocks):
        if (
            block["type"] == "alfred.workflow.input.keyword"
            and block["config"]["keyword"] not in NORMAL_KEYWORDS
        ) or (
            block["type"] == "alfred.workflow.utility.argument"
            and not re.match(r"^\d\{query\}$", block["config"]["argument"])
        ):
            remove_block_indexes.append(i)
            remove_blocks.append(block["uid"])
        if block["type"] == "alfred.workflow.utility.junction":
            junction_uid = block["uid"]

    if not junction_uid:
        raise Exception("Junction block not found")

    # Remove blocks and connections
    for remove_index in remove_block_indexes[::-1]:
        blocks.pop(remove_index)
    for block_uid in remove_blocks:
        ui_blocks.pop(block_uid)
        connections.pop(block_uid)

    # Remove icons
    clear_icons()

    # Add blocks and connections
    ypos = BEGIN_YPOS
    for alias, currency in aliases.items():
        add_alias_entry(
            blocks,
            ui_blocks,
            connections,
            currencies,
            alias,
            currency,
            ypos,
            junction_uid,
        )
        ypos += GAP

    # Write back to info.plist
    save(content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
