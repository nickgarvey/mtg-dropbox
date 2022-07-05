from typing import TypedDict, List, Dict
import card_type_gen


Card = card_type_gen._Root


class SetData(TypedDict):
    cards: List[Card]


class AllPrintings(TypedDict):
    data: Dict[str, SetData]
