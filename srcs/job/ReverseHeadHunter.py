from typing import Iterator, Dict, Any
import time
from oauthlib.oauth2.rfc6749.clients.backend_application import BackendApplicationClient
from requests_oauthlib.oauth2_session import OAuth2Session
from loguru import logger

class ReverseHeadHunter:

    client: BackendApplicationClient
    oauth: OAuth2Session
    token: Any

    def __init__(self, config: dict):
        self.client = BackendApplicationClient(client_id=config["RH_CLIENT_ID"])
        self.oauth = OAuth2Session(client=self.client)
        self.token = self.oauth.fetch_token(
            token_url=config["RH_TOKEN_URL"],
            client_id=config["RH_CLIENT_ID"],
            client_secret=config["RH_CLIENT_SECRET"]
        )

    def fetch_offer_by_id(self, offers_url: str, offer_id: int) -> dict:

        url = offers_url + "/" + str(offer_id)
        response = self.oauth.get(url)
        #use of response.raise_for_status() would be better
        if response.status_code != 200:
            print(f"Error GET: {url}")
        return response.json()

    def fetch_offers_by_range(self, offers_url: str, start_page: int, end_page: int) -> Iterator[dict]:

        page_query = "?page="
        for page in range(start_page, end_page + 1):
            url = offers_url + page_query + str(page)
            response = self.oauth.get(url)
            if (response.status_code != 200):
                print(f"Error GET: {url}")
                continue
            time.sleep(1)
            yield response.json()

    def fetch_offers_by_page(self, offers_url: str, page_id: int):

        page_query = "?page="
        url = offers_url + page_query + str(page_id)
        response = self.oauth.get(url)
        return response.json()
