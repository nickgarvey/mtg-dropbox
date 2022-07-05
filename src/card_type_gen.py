from typing import List, TypedDict


_Root = TypedDict('_Root', {
    # required
    'artist': str,
    # required
    'availability': List[str],
    # required
    'boosterTypes': List[str],
    # required
    'borderColor': str,
    # required
    'colorIdentity': List[str],
    # required
    'colors': List[str],
    # required
    'convertedManaCost': int,
    # required
    'edhrecRank': int,
    # required
    'finishes': List[str],
    # required
    'flavorText': str,
    # required
    'foreignData': List["_RootForeigndataItem"],
    # required
    'frameVersion': str,
    # required
    'hasFoil': bool,
    # required
    'hasNonFoil': bool,
    # WARNING: The required are not correctly taken in account,
    # See: https://github.com/camptocamp/jsonschema-gentypes/issues/6
    # 
    # required
    'identifiers': "_RootIdentifiers",
    # required
    'language': str,
    # required
    'layout': str,
    # WARNING: The required are not correctly taken in account,
    # See: https://github.com/camptocamp/jsonschema-gentypes/issues/6
    # 
    # required
    'legalities': "_RootLegalities",
    # required
    'manaCost': str,
    # required
    'manaValue': int,
    # required
    'name': str,
    # required
    'number': str,
    # required
    'power': str,
    # required
    'printings': List[str],
    # WARNING: The required are not correctly taken in account,
    # See: https://github.com/camptocamp/jsonschema-gentypes/issues/6
    # 
    # required
    'purchaseUrls': "_RootPurchaseurls",
    # required
    'rarity': str,
    # WARNING: we get an array without any items
    # 
    # required
    'rulings': None,
    # required
    'setCode': str,
    # required
    'subtypes': List[str],
    # WARNING: we get an array without any items
    # 
    # required
    'supertypes': None,
    # required
    'text': str,
    # required
    'toughness': str,
    # required
    'type': str,
    # required
    'types': List[str],
    # required
    'uuid': str,
}, total=False)


_RootForeigndataItem = TypedDict('_RootForeigndataItem', {
    # required
    'flavorText': str,
    # required
    'language': str,
    # required
    'multiverseId': int,
    # required
    'name': str,
    # required
    'text': str,
    # required
    'type': str,
}, total=False)


_RootIdentifiers = TypedDict('_RootIdentifiers', {
    # required
    'cardKingdomFoilId': str,
    # required
    'cardKingdomId': str,
    # required
    'cardsphereId': str,
    # required
    'mcmId': str,
    # required
    'mcmMetaId': str,
    # required
    'mtgjsonV4Id': str,
    # required
    'mtgoFoilId': str,
    # required
    'mtgoId': str,
    # required
    'multiverseId': str,
    # required
    'scryfallId': str,
    # required
    'scryfallIllustrationId': str,
    # required
    'scryfallOracleId': str,
    # required
    'tcgplayerProductId': str,
}, total=False)


_RootLegalities = TypedDict('_RootLegalities', {
    # required
    'commander': str,
    # required
    'duel': str,
    # required
    'legacy': str,
    # required
    'modern': str,
    # required
    'penny': str,
    # required
    'vintage': str,
}, total=False)


_RootPurchaseurls = TypedDict('_RootPurchaseurls', {
    # required
    'cardKingdom': str,
    # required
    'cardKingdomFoil': str,
    # required
    'cardmarket': str,
    # required
    'tcgplayer': str,
}, total=False)
