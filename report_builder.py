from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from jinja2 import Template

import click
import os
import re
import untangle

VALID_EXTENSIONS = ['cod', 'dec', 'txt']

OUTPUT_TEMPLATE = Template('''
<html>
<head>
<title>Deck Lists</title>''' +
#<link rel="stylesheet" type="text/css" href="http://hongyanh.github.io/open-style/css/style.css">
'''
<link rel="stylesheet" href="https://unpkg.com/purecss@0.6.2/build/pure-min.css" integrity="sha384-UQiGfs9ICog+LwheBSRCt1o5cbyKIHbwjWscjemyBMT9YCUMZffs6UqUTd0hObXD" crossorigin="anonymous">
</head>
<body>
{% for deck in decks %}
<div>
<h2>{{deck.deck_path}}</h2>
<ol>
{% for card in deck.main %}
    <li>{{ card }}
{% endfor %}
</ol>
</div>
{% endfor %}
</html>
''')

class Deck(object):
    def __init__(self, deck_path, card_database):
        self.deck_path = deck_path
        self.main, self.side = \
                load_cod(deck_path) or load_dec(deck_path) or (None, None)

    @property
    def valid(self):
        return bool(self.main)


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
            match = re.match(r'(SB: *)?([0-9]* )?(.*)$', line)
            sb, number, card = match.groups()
            if not card:
                continue
            if sb:
                side_board += [card] * int(number)
            else:
                main += [card] * int(number or 1)
    return (main, side_board)


def write_analysis(decks, output_file):
    for deck in decks:
        pass
        # print(deck.deck_path, len(deck.main), len(deck.side))
    output_file.write(OUTPUT_TEMPLATE.render(decks=decks).encode('utf-8'))


@click.command()
@click.argument('root_dir')
@click.argument('output_path')
def main(root_dir, output_path):
    os.chdir(root_dir)
    # find all decks
    deck_paths = find_decks(root_dir)
    # load all decks
    decks = []
    for path in deck_paths:
        deck = Deck(os.path.relpath(path, root_dir), None)
        if deck.valid:
            decks.append(deck)
    # write analysis
    with open(output_path, 'w') as output:
        write_analysis(decks, output)

if __name__ == "__main__":
    main()
