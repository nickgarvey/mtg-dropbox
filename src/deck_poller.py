import asyncio
import datetime
import io
import json
import logging
import lzma
from typing import Iterable, List, Set, Tuple, Optional

import aiohttp
import redis
from dropbox.files import FileMetadata

import constants
from mtg_types import AllPrintings
from serializer import s, d
import dropbox_client

# poll for new decks
# if new card data, redo everything
# build data for decks
from deck_parser import DeckParser

ONE_HOUR_SEC = 60 * 60

logger = logging.getLogger(__name__)


META_URL = "https://mtgjson.com/api/v5/Meta.json"
ALL_PRINTINGS_URL = "https://mtgjson.com/api/v5/AllPrintings.json.xz"


class DeckPoller:
    def __init__(self):
        self.dropbox_client = dropbox_client.DropboxDeckClient()
        self.r = redis.Redis()

    async def refresh_cards(
        self, mtg_json_poll_interval_sec: int
    ) -> Tuple[Optional[AllPrintings], bool]:
        last_meta_poll = datetime.datetime.fromisoformat(
            (self.r.get("last_meta_poll") or b"").decode("utf-8") or "1970-01-01"
        )
        need_poll = (
            not last_meta_poll
            or not last_meta_poll
            + datetime.timedelta(seconds=mtg_json_poll_interval_sec)
            > datetime.datetime.now()
        )
        meta = d(self.r.get("mtg_json/meta"))
        all_printings = d(self.r.get("mtg_json/all_printings"))
        if not need_poll and meta and all_printings:
            return all_printings, False

        async with aiohttp.ClientSession() as session:
            async with session.get(META_URL) as resp:
                meta_json = await resp.text()

        self.r["mtg_json/meta"] = s(meta_json)
        self.r["last_meta_poll"] = datetime.datetime.now().isoformat()
        meta_obj = json.loads(meta_json)
        if all_printings and meta_obj:
            all_printings_obj = json.load(all_printings)
            if all_printings_obj["meta"]["date"] == meta_obj["meta"]["date"]:
                return all_printings, False

        logger.debug("Refreshing cards")
        decompressor = lzma.LZMADecompressor()
        buf = io.BytesIO()
        async with aiohttp.ClientSession() as session:
            async with session.get(ALL_PRINTINGS_URL) as resp:
                while resp_bytes := await resp.content.readany():
                    buf.write(decompressor.decompress(resp_bytes))
                buf.seek(0)
        all_printings_bytes = buf.read()
        all_printings = json.loads(all_printings_bytes)
        self.r["mtg_json/all_printings"] = s(all_printings_bytes)
        return all_printings, True

    async def fetch_dropbox_metadata(self):
        loop = asyncio.get_running_loop()
        file_list = await loop.run_in_executor(None, self.dropbox_client.list_files)

        return [
            file
            for file in file_list
            if file.path_lower.endswith(constants.SUPPORTED_DECK_EXTENSIONS)
        ]

    async def fetch_dropbox_decks(
        self, deck_metadatas: Iterable[FileMetadata]
    ) -> List[Tuple[FileMetadata, bytes]]:
        loop = asyncio.get_running_loop()
        coros = [
            loop.run_in_executor(None, self.dropbox_client.fetch_deck, metadata)
            for metadata in deck_metadatas
        ]
        ret = [
            (metadata, file_body)
            for metadata, file_body in await asyncio.gather(*coros)
        ]
        return ret

    async def refresh_decks(self, to_fetch_decks: List[FileMetadata]) -> None:
        logger.info("Decks needing refresh: %s", [d.name for d in to_fetch_decks])
        deck_contents = await self.fetch_dropbox_decks(to_fetch_decks)
        for metadata, deck_body in deck_contents:
            logger.info("Saving %s %s", metadata.name, metadata.content_hash)
            self.r[f"decks/{metadata.content_hash}"] = s(deck_body)

    def recalculate_decks(self, all_printings: AllPrintings):
        redis_deck_paths: Set[bytes] = set(self.r.scan_iter(match="decks/*"))
        deck_parser = DeckParser(all_printings, self.r)
        for path in redis_deck_paths:
            deck = deck_parser.parse_deck(d(self.r.get(path)))
            print(deck)
            break

    async def poll_loop(self, mtg_json_poll_interval_sec: int = ONE_HOUR_SEC):
        card_database_updated_coro = self.refresh_cards(mtg_json_poll_interval_sec)

        deck_metadatas = await self.fetch_dropbox_metadata()
        dropbox_deck_paths: Set[bytes] = {
            f"decks/{metadata.content_hash}".encode("utf-8")
            for metadata in deck_metadatas
        }

        redis_deck_paths: Set[bytes] = set(self.r.scan_iter(match="decks/*"))
        logger.debug("Found existing decks: %d", len(redis_deck_paths))
        deleted_deck_paths = redis_deck_paths - dropbox_deck_paths
        # strip the 6 character "decks/"
        to_fetch_deck_hashs: Set[bytes] = {
            deck[6:] for deck in dropbox_deck_paths - redis_deck_paths
        }
        if deleted_deck_paths:
            self.r.delete(*deleted_deck_paths)

        to_fetch_decks = [
            file
            for file in deck_metadatas
            if file.content_hash.encode("utf-8") in to_fetch_deck_hashs
        ]
        await self.refresh_decks(to_fetch_decks)

        # do a full refresh if the card database has updated
        all_printings, all_needs_refresh = await card_database_updated_coro
        logger.info("All needs refresh: %s", all_needs_refresh)

        if True or all_needs_refresh:
            self.recalculate_decks(all_printings)


def main():
    poller = DeckPoller()
    asyncio.run(poller.poll_loop())


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    main()
