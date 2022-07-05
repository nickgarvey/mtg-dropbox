import json
from mtg_types import Card, AllPrintings
from typing import List, Optional

import redis
from serializer import d


class Deck:
    commander: Optional[str]
    mainboard: List[Card]
    sideboard: List[Card]


class DeckParser:
    def __init__(self, all_printings: AllPrintings, r: redis.Redis):
        self.all_printings = all_printings
        self.r = r

    def parse_deck(self, deck_contents: bytes) -> Deck:
        print(deck_contents)
        return Deck()
