#!/usr/bin/env python3
import json
import logging
import os
import re
import string

import click
import numpy
import untangle
from jinja2 import Template

logging.basicConfig(level="DEBUG")

VALID_EXTENSIONS = ["cod", "dec", "txt"]

OUTPUT_TEMPLATE = Template(
    """
<html>
<head>
<title>Deck Lists</title>

<link
  rel="stylesheet"
  href="https://unpkg.com/purecss@0.6.2/build/pure-min.css"
  integrity="sha384-UQiGfs9ICog+LwheBSRCt1o5cbyKIHbwjWscjemyBMT9YCUMZffs6UqUTd0hObXD"
  crossorigin="anonymous">

<script type="text/javascript">
const decks = {
{% for deck in decks %}
"{{deck.name | e}}": {"mainboard": [
{% for card in deck.mainboard_js %}
{{card}},\
{% endfor %}
],
"sideboard": [
{% for card in deck.sideboard_js %}
{{card}},\
{% endfor %}
]
},
{% endfor %}
}

// mostly from http://stackoverflow.com/a/133997/965648
function tapped_out(name) {
    if (!(name in decks)) {
        alert('Deck name is weird', name);
        return;
    }

    let main_deck_counts = {};
    let side_deck_counts = {};
    decks[name]["mainboard"].forEach(function(card) {
        if (!(card in main_deck_counts)) {
            main_deck_counts[card] = 0;
        }
        main_deck_counts[card] += 1;
    });
    let main_deck_str = "";
    for (let card in main_deck_counts) {
        main_deck_str += main_deck_counts[card] + " " + card + "\\n";
    }

    decks[name]["sideboard"].forEach(function(card) {
        if (!(card in side_deck_counts)) {
            side_deck_counts[card] = 0;
        }
        side_deck_counts[card] += 1;
    });
    let side_deck_str = "";
    for (let card in side_deck_counts) {
        side_deck_str += side_deck_counts[card] + " " + card + "\\n";
    }
    const form = document.createElement("form");

    form.setAttribute("method", "post");
    form.setAttribute(
        "action",
        "https://tappedout.net/mtg-decks/paste/"
    );
    form.setAttribute("target", "_blank");

    let field = document.createElement("input");
    field.setAttribute("type", "hidden");
    field.setAttribute("name", "mainboard");
    field.setAttribute("value", main_deck_str);
    form.appendChild(field);

    field = document.createElement("input");
    field.setAttribute("type", "hidden");
    field.setAttribute("name", "sideboard");
    field.setAttribute("value", side_deck_str);
    form.appendChild(field);

    document.body.appendChild(form);
    form.submit();
}
</script>

<style type="text/css">
body { margin: 20px }
td { padding: 3px 5px }
th { padding: 1px 5px }
.thl { text-align: left }
.colorheader { width: 36px }
.tbnum { text-align: right }
.card-r { color: red }
.card-u { color: blue }
.card-g { color: green }
.card-b { color: black }
.card-w { color: grey }
#footer { margin: 20px 0 }
a { text-decoration: none }

table { border-collapse: collapse; }
tr { border: none; }
</style>
</head>

<body>
<table>
<thead>
<tr>
<th>Main / Side</th>
<th>CMC</th>
<th colspan="5">Colors</th>
<th class="thl">View</th>
<th class="thl">Download</th>
</tr>
</thead>
{% for deck in decks %}
<tr>
<td class="tbnum">{{deck.main | length}} / {{deck.side | length}}</td>
<td class="tbnum"><code>{{ deck.cmc_ascii }}</code></td>
{% for color in "W U B R G".split(" ")%}
<td>
{% if color in deck.color_identity %}
<span class="card-{{color | lower}}">{{color}}</span>
{% endif %}
</td>
{% endfor %}
<td>
<a
  href="javascript: tapped_out('{{deck.name | escape}}')">
  [TO]
</a>
</td>
<td>
<a href="{{deck.path | e}}" download>{{deck.path | e}}</a>
</td>
</tr>
{% endfor %}
</table>

<div id="footer">
<a href="https://github.com/nickgarvey/mtg-dropbox">GitHub</a>
</div>
</html>
"""
)


class CardDatabase:
    def __init__(self, card_json_path):
        with open(card_json_path) as cjf:
            self.card_json = json.load(cjf)

    def __getitem__(self, key):
        return self.card_json["data"][key]

    def __contains__(self, key):
        return key in self.card_json["data"]

    def get(self, key, default=None):
        return self.card_json.get(key, default)


class Deck:
    def __init__(self, path: str, database: CardDatabase):
        self.path = path
        self.database = database
        self.main, self.side = load_cod(path) or load_txt(path) or (None, None)

    @property
    def valid(self):
        return bool(self.main)

    def db_cards(self, include_sideboard):
        cards = self.main + self.side if include_sideboard else self.main
        return [self.database[c][0] for c in cards if c in self.database]

    @property
    def name_js(self):
        return json.dumps(self.name)

    @property
    def mainboard_js(self):
        return [json.dumps(card) for card in self.main]

    @property
    def sideboard_js(self):
        return [json.dumps(card) for card in self.side or []]

    @property
    def all_cards_js(self):
        # had this in prior version, not sure why
        # json.dumps(card.encode("ascii", "replace"))
        return self.mainboard_js + self.sideboard_js

    @property
    def color_identity(self):
        colors = set()
        for db_card in self.db_cards(include_sideboard=True):
            colors |= set(db_card.get("colorIdentity", []))
        return colors

    @property
    def name(self):
        return self.path.split("/")[-1]

    @property
    def cmcs(self):
        return [
            float(card["convertedManaCost"])
            for card in self.db_cards(include_sideboard=False)
            if "Land" not in card["types"] and "convertedManaCost" in card
        ]

    @property
    def cmc_ascii(self):
        if not self.cmcs:
            return "&#xb7;" * 8
        l, m, u = map(numpy.round, numpy.percentile(self.cmcs, [20, 50, 80]))
        result = ""
        for i in range(8):
            if i < l or i > u:
                result += "&#xb7;"
            elif i in [l, m, u]:
                result += str(i)
            else:
                result += "-"
        return result


def find_decks(root_dir):
    return sorted(
        os.path.join(dirpath, filename)
        for (dirpath, dirnames, filenames) in os.walk(root_dir)
        for filename in filenames
        for ext in VALID_EXTENSIONS
        if filename.lower().endswith("." + ext)
    )


def load_cod(deck_path):
    try:
        deck = untangle.parse(deck_path)
    except Exception:
        return None

    main = []
    side_board = []
    for zone in deck.cockatrice_deck.zone:
        for card in zone.card:
            if zone["name"] == "tokens":
                continue
            elif zone["name"] == "side":
                side_board += [card["name"]] * int(card["number"] or 0)
            else:
                main += [card["name"]] * int(card["number"] or 0)
    return main, side_board


def load_txt(deck_path):
    main = []
    side_board = []
    saw_sideboard = False
    with open(deck_path) as deck_file:
        for line in deck_file:
            line = line.strip()
            if not line:
                continue
            if line in ["Companion", "Deck", "Commander"]:
                continue
            if "Sideboard" in line:
                saw_sideboard = True
                continue

            match = re.match(r"(SB: *)?([0-9]*)?\s*([^\n\r(]+)(?: \(.*)?$", line)
            if not match:
                continue
            sb, number, card = match.groups()
            if not set(card) & set(string.ascii_letters):
                continue
            to_add = [card] * int(number or 1)
            if sb or saw_sideboard:
                side_board += to_add
            else:
                main += to_add

    return main, side_board


def write_analysis(decks, output_file):
    logging.debug("Rendering output")
    render = OUTPUT_TEMPLATE.render(decks=decks)
    logging.debug("Rendered output length: %d", len(render))
    output_file.write(render)


@click.command()
@click.argument("root_dir")
@click.argument("card_json")
@click.argument("output_path")
def main(root_dir, card_json, output_path):
    logging.debug("Loading Card DB")
    database = CardDatabase(card_json)

    logging.debug("Loading decks")
    os.chdir(root_dir)
    # find all decks
    deck_paths = find_decks(root_dir)
    # load all decks
    decks = []
    for path in deck_paths:
        logging.debug("Deck path: " + path)
        deck = Deck(os.path.relpath(path, root_dir), database)
        if deck.valid:
            decks.append(deck)
    # write analysis
    logging.debug("Writing output file %s", output_path)
    with open(output_path, "w") as output:
        write_analysis(decks, output)


if __name__ == "__main__":
    main()
