import dropbox
import logging
import pickle
import requests
import yaml

from typing import List, Tuple

from dropbox.files import ListFolderResult, FileMetadata

OAUTH_PATH = "data/oauth.pickle"
CONFIG_PATH = "data/dropbox.yaml"

logger = logging.getLogger(__name__)


class DropboxDeckClient:
    def __init__(
        self,
    ):
        key, secret = load_key_secret()
        refresh_token = load_refresh_token()
        self.client = dropbox.Dropbox(
            app_key=key,
            app_secret=secret,
            oauth2_refresh_token=refresh_token,
        )

    def list_files(self) -> List[FileMetadata]:
        files = []
        res: ListFolderResult = self.client.files_list_folder(
            "/MTG Decks", recursive=True
        )
        entry: FileMetadata
        for entry in res.entries:
            if getattr(entry, "is_downloadable", None):
                files.append(entry)

        while res.has_more:
            res = self.client.files_list_folder_continue(res.cursor)
            for entry in res.entries:
                if getattr(entry, "is_downloadable", None):
                    files.append(entry)
        return files

    def fetch_deck(self, file_metadata: FileMetadata) -> Tuple[FileMetadata, bytes]:
        resp: requests.models.Response
        metadata, resp = self.client.files_download(file_metadata.path_display)
        body = resp.content
        logger.info("Fetched %s with length %d", metadata.path_display, len(body))
        return metadata, body


def load_refresh_token():
    with open(OAUTH_PATH, "rb") as f:
        oauth_result: dropbox.oauth.OAuth2FlowNoRedirectResult = pickle.load(f)
        if type(oauth_result) == dropbox.oauth.OAuth2FlowNoRedirectResult:
            return oauth_result.refresh_token


def oauth_flow(key: str, secret: str) -> str:
    flow = dropbox.DropboxOAuth2FlowNoRedirect(key, secret, token_access_type="offline")

    print(flow.start())
    code = input("Enter auth code: ").strip()
    oauth_result = flow.finish(code)
    with open("data/oauth.pickle", mode="wb") as f:
        pickle.dump(oauth_result, f)
    return oauth_result.refresh_token


def _file_list(key: str, secret: str, refresh_token):
    with dropbox.Dropbox(
        app_key=key, app_secret=secret, oauth2_refresh_token=refresh_token
    ) as client:
        res = client.files_list_folder("/MTG Decks", recursive=True)
        for entry in res.entries:
            print(entry)
        while res.has_more:
            res = client.files_list_folder_continue(res.cursor)
            for entry in res.entries:
                print(entry)


def load_key_secret():
    with open("data/dropbox.yaml") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config["key"], config["secret"]


def setup_auth():
    key, secret = load_key_secret()
    try:
        refresh_token = load_refresh_token()
        _file_list(key, secret, refresh_token)
    except Exception:
        refresh_token = oauth_flow(key, secret)
    _file_list(key, secret, refresh_token)


if __name__ == "__main__":
    setup_auth()
