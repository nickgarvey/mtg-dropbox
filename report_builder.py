from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from jinja2 import Template

import click
import json
import string
import os
import re
import untangle

VALID_EXTENSIONS = ['cod', 'dec', 'txt']

OUTPUT_TEMPLATE = Template('''
<html>
<head>
<title>Deck Lists</title>

<link rel="stylesheet" href="https://unpkg.com/purecss@0.6.2/build/pure-min.css" integrity="sha384-UQiGfs9ICog+LwheBSRCt1o5cbyKIHbwjWscjemyBMT9YCUMZffs6UqUTd0hObXD" crossorigin="anonymous">

<style type="text/css">
body { margin: 20px }
td { padding: 1px 5px }
th { padding: 1px 5px }
.colorheader { width: 36px }
.tbnum { text-align: right }
.card-red { color: red }
.card-blue { color: blue }
.card-green { color: green }
.card-black { color: black }
.card-white { color: grey }
#footer { margin: 20px 0 }

table { border-collapse: collapse; }
tr { border: none; }
</style>
</head>

<body>
<table>
<thead>
<tr>
<th />
<th />
<th />
<th />
<th />
<th>Name</th>
<th>Card Counts</th>
</tr>
</thead>
{% for deck in decks %}
<tr>
{% for color in "White Blue Black Red Green".split(" ")%}
<td>
{% if color in deck.color_identity %}
<span class="card-{{color | lower}}">&#x2714;</span>
{% endif %}
</td>
{% endfor %}
<td><a href="{{deck.path}}">{{deck.path}}</a></td>
<td class="tbnum">{{deck.main | length}} / {{deck.side | length}}</td>
</tr>
{% endfor %}
</table>

<div id="footer">
<a href="https://github.com/nickgarvey/mtg-dropbox">GitHub</a>
</div>
</html>
''')


class CardDatabase(object):
    def __init__(self, card_json_path, set_json_path):
        with open(card_json_path) as cjf:
            self.card_json = json.load(cjf)
        with open(set_json_path) as sjf:
            pass
            # self.set_json = json.load(sjf)

    def __getitem__(self, key):
        return self.card_json[key]

    def get(self, key, default=None):
        return self.card_json.get(key, default)


class Deck(object):
    def __init__(self, path, database):
        self.path = path
        self.database = database
        self.main, self.side = \
                load_cod(path) or load_dec(path) or (None, None)

    @property
    def valid(self):
        return bool(self.main)

    @property
    def color_identity(self):
        colors = set()
        for card in set(self.main) | set(self.side):
            db_card = self.database.get(card)
            if not db_card:
                continue
            colors |= set(db_card.get('colorIdentity', []))
        color_strs = [
                {'U': 'Blue',
                 'G': 'Green',
                 'R': 'Red',
                 'W': 'White',
                 'B': 'Black'}[color] for color in colors]
        return color_strs
    
    @property
    def name(self):
        return self.path.split('/')[-1]


def find_decks(root_dir):
    return [
            os.path.join(dirpath, filename)
            for (dirpath, dirnames, filenames) in os.walk(root_dir)
            for filename in filenames
            for ext in VALID_EXTENSIONS
            if filename.lower().endswith('.' + ext)
    ]


def load_cod(deck_path):
    try:
        deck = untangle.parse(deck_path)
    except Exception:
        return None
    
    main = []
    side_board = []
    for zone in deck.cockatrice_deck.zone:
        for card in zone.card:
            if zone['name'] == "side":
                side_board += [card['name']] * int(card['number'] or 0)
            else:
                main += [card['name']] * int(card['number'] or 0)
    return (main, side_board)


def load_dec(deck_path):
    main = []
    side_board = []
    with open(deck_path) as deck_file:
        for line in deck_file:
            if not line:
                continue
            match = re.match(r'(SB: *)?([0-9]* )?([^\n\r]+)(?:\r|\n)?$', line)
            if not match:
                continue
            sb, number, card = match.groups()
            if not set(card) & set(string.ascii_letters):
                continue
            if sb:
                side_board += [card] * int(number)
            else:
                main += [card] * int(number or 1)
    return (main, side_board)


def write_analysis(decks, output_file):
    output_file.write(OUTPUT_TEMPLATE.render(decks=decks).encode('utf-8'))


@click.command()
@click.argument('root_dir')
@click.argument('card_json')
@click.argument('set_json')
@click.argument('output_path')
def main(root_dir, card_json, set_json, output_path):
    os.chdir(root_dir)

    database = CardDatabase(card_json, set_json)
    # find all decks
    deck_paths = find_decks(root_dir)
    # load all decks
    decks = []
    for path in deck_paths:
        deck = Deck(os.path.relpath(path, root_dir), database)
        if deck.valid:
            decks.append(deck)
    # write analysis
    with open(output_path, 'w') as output:
        write_analysis(decks, output)

if __name__ == "__main__":
    main()
