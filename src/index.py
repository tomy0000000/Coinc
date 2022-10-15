import json
import plistlib
import sys
from uuid import uuid4

NORMAL_KEYWORDS = ["coinc", "cur-ref", "cur-index"]
BEGIN_YPOS = 1250
GAP = 130


def load():
    with open("info.plist", "rb") as f:
        content = plistlib.load(f)
    with open("alias.json") as f:
        aliases = json.load(f)
    with open("currencies.json") as f:
        currencies = json.load(f)
    return content, aliases, currencies


def save(content):
    with open("info.plist", "wb") as f:
        plistlib.dump(content, f)


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
        ) or (block["type"] == "alfred.workflow.utility.argument"):
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
