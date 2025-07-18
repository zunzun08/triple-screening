import scrapy
import requests
import asyncio
from scrapy.crawler import Crawler
import json
from urllib.parse import quote, urlparse
import re
import datetime
import numpy as np
import pandas as pd
from collections import deque, defaultdict
from datetime import datetime
import tls_client
import time


class NetworkManager:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        self.proxies = {"http": "108.161.135.118"}

    def create_session(self) -> requests.Session:
        if not self.proxies:
            raise ValueError("no proxy available")
        if self.headers is None:
            raise ValueError("headers are not valid")

        client = requests.Session()
        client.proxies.update(self.proxies)
        client.headers.update(self.headers)
        return client

    def check_status(self, urls: list, session) -> None:
        for url in urls:
            response = session.get(url)
            print(f"{url} | Status code: {response.status_code}")
            return response.status_code

    def _format_proxy_for_client(self, client_type="requests"):
        if not self.proxies:
            return {}

        formatted = {}
        for protocol, proxy_value in self.proxies.items():
            if isinstance(proxy_value, list):
                proxy_ip = proxy_value[0]
            else:
                proxy_ip = proxy_value

            if client_type == "tls_client" and not proxy_ip.startswith("http"):
                formatted[protocol] = f"http://{proxy_ip}:8080"
            elif not proxy_ip.startswith("http"):
                formatted[protocol] = f"http://{proxy_ip}:8080"
            else:
                formatted[protocol] = proxy_ip

        return formatted

    def tls_client_session(self) -> tls_client.Session:
        if not self.proxies:
            raise ValueError("no proxy available")
        if self.headers is None:
            raise ValueError("headers are not valid")

        client = tls_client.Session(
            client_identifier="chrome_120", random_tls_extension_order=True
        )
        client.headers.update(self.headers)
        return client


class NYTimesSpider(scrapy.Spider):
    def __init__(self, pages_to_parse, section_url,*args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = NetworkManager()
        self.session: requests.Session = self.config.create_session()

        self.section_url = section_url
        self.start_urls = [self.section_url]


        self.pages_to_parse = pages_to_parse
        self.pages_left_to_parse = pages_to_parse
        self.pages_parsed = 0

        self.fetched_articles = []
        self.all_parsed_data = defaultdict(list)

        self.headers = self.config.headers.copy()
        self.session_needs_rotation = False
        self.rotation_reason = None

        self.current_session_metrics = {
            "start_time": datetime.now(),
            "requests_made": 0,
            "avg_response_time": 0,
            "success_rate": 0,
        }
        self.site_metrics = {
            "total_requests": 0,
            "historical_avg_response": 0,
            "successful_sessions": 0,
            "failed_sessions": 0,
        }
        self.session_transitions = {
            "reasons_for_change": [],
            "time_between_changes": [],
            "success_after_change": [],
        }

    # Scarapy configs
    name = "nytimesspider"
    allowed_domains = ["https://www.nytimes.com"]
    start_urls = ["https://www.nytimes.com/section/business/media"]

    def _try_standard_session(self):
        return self.session.get("https://www.nytimes.com")

    def _try_tls_session(self):
        tls_client = self.config.tls_client_session()
        response = tls_client.get("https://www.nytimes.com")
        return self._normalize_response(response)

    def _normalize_response(self, response):
        """Normalize response objects from different client types"""

        if hasattr(response, "status_code"):
            return response
        elif hasattr(response, "status"):
            response.status_code = response.status
            return response
        else:
            raise ValueError("Unknown response type")

    # Updating headers
    def _get_tokens(self) -> None:
        strategies = [
            ("standard_session", self._try_standard_session),
            ("tls_session", self._try_tls_session),
        ]

        for strategy_name, get_response in strategies:
            try:
                self.logger.info(f"Attempting to get tokens using {strategy_name}")
                r = get_response()

                if self._is_valid_response(r) and self._content_validation(r):
                    return self._extract_tokens(r)
                else:
                    if getattr(self, "session_needs_rotation", False):
                        self.logger.info(
                            f"{strategy_name} failed. Starting TLS session in 3 seconds..."
                        )
                        time.sleep(3)

            except requests.exceptions.RequestException as e:
                self.logger.error(f"{strategy_name} failed: {e}")
                continue

        return None

    def _extract_tokens(self, response):
        # variables needed

        html_page = response.text

        vars_dict = dict.fromkeys(["nyt-token", "nyt-app-type", "nyt-app-version"])
        for variables in vars_dict:

            # Search
            filtered_value = f"[\"']{variables}[\"']\s*:\s*[\"']([^\"']+)[\"']"
            val = re.search(rf"{filtered_value}", html_page)

            if val:
                self.logger.info("Token found")
                token = val.group(1)
                token = token.strip()

            else:
                token = ""

            vars_dict[variables] = token

        return vars_dict

    def _header_update(self):
        header_extension = self._get_tokens()
        if header_extension:
            self.headers.update(header_extension)

            # Update session headers
            self.session.headers.update(self.headers)
        else:
            return None

    # Connection and 403 handling
    def _is_valid_response(self, response):
        if 200 <= response.status_code < 300:
            return True
        if 400 <= response.status_code < 500 and response.status_code > 300:
            # Can try alternate headers here
            self.logger.info("Got 403 error - attempting failsafe measure")
            return self._403_failsafe(response)

        self.logger.error(f"Invalid response: {response.status_code}")
        return False

    def _content_validation(self, response):
        if not response.text:
            return False
        if "text/html" not in response.headers.get("content-type", ""):
            return False
        else:
            return True

    def _403_failsafe(self, response):
        """Strategies to overcome 403 error"""
        if self._try_enhanced_headers():
            return True
        if self._try_rotate_user_agent():
            return True
        if self._try_rotate_proxy():
            return True
        if self._check_soft_block(response):
            self.logger.info(
                "Status code 403 but content available - proceed with caution"
            )
            return True

        self._mark_for_session_rotation("403_block")
        return False

    def _try_enhanced_headers(self):
        enhanced_headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.nytimes.com/section/business/media",
            "Origin": "https://www.nytimes.com",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }
        self.session.headers.update(enhanced_headers)
        self.logger.info(f"Added enhanced errors for 403 recovery")
        return True

    def _try_rotate_user_agent(self):
        alternate_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        ]
        current_agent = self.session.headers.get("User-Agent")
        for agent in alternate_agents:
            if agent != current_agent:
                self.session.headers["User-Agent"] = agent
                self.logger.info(f"Rotated to agent: {agent}")
                return True
        return False

    def _try_rotate_proxy(self):
        if len(self.proxies) > 1:
            current_proxy = self.session.proxies.get("http")

            for proxy in self.proxies["http"]:
                if proxy != current_proxy:
                    self.session.proxies["http"] = proxy
                    self.logger.info(f"Rotated to proxy: {proxy}")
                    return True
            return False
        else:
            self.logger.info(f"No more proxies available")
            return False

    def _check_soft_block(self, response):
        if not response.text:
            return False

        soft_block_indicators = ["nyt_token", "graphql", "samizdat"]

        content_lower = response.text.lower()
        indicator_search = [
            indicators
            for indicators in soft_block_indicators
            if indicators in response.text
        ]

        if indicator_search:
            self.logger.info(f"Soft block detected - found {indicator_search}")
            return True
        else:
            return False

    def _mark_for_session_rotation(self, reason):
        self.session_needs_rotation = True
        self.rotation_reason = reason
        self.logger.warning(f"Session marked for rotation: {reason}")

    # Request and API validation
    def _get_id_var(self, url: str):
        """Extract the path from a URL to use as the ID variable."""
        if not url:
            raise ValueError("URL cannot be empty")

        try:
            id_path = urlparse(url).path
            if not id_path or id_path == "/":
                raise ValueError("URL must contain a valid path")
            return id_path
        except Exception as e:
            raise ValueError(f"Invalid URL format: {e}")

    def _request_generator(
        self, url: str, cursor=None, operation_name: str = "CollectionsQuery"
    ) -> str:
        """Generate API endpoint URL for GraphQL requests."""
        if url:
            id_path = self._get_id_var(url)
        else:
            self.logger.info("Invalid URL!")
            return None

        variables = {
            "id": id_path,
            "first": 10,
            "exclusionMode": "HIGHLIGHTS_AND_EMBEDDED",
            "isFetchMore": False,
            "isTranslatable": False,
            "isEspanol": False,
            "highlightsListUri": "nyt://per/personalized-list/__null__",
            "highlightsListFirst": 0,
            "hasHighlightsList": False,
            "cursor": cursor,
        }
        extensions = {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "8334262659d77fc2166184bf897e6d139e437af3a9b84d0c020d3dfcb0f177b8",
            }
        }

        # formatting
        var_query = quote(json.dumps(variables, separators=(",", ":")))
        extension_query = quote(json.dumps(extensions, separators=(",", ":")))

        api_endpoint = f"https://samizdat-graphql.nytimes.com/graphql/v2?operationName={operation_name}&variables={var_query}&extensions={extension_query}"

        return api_endpoint

    def _check_api_connection(self, endpoint):
        try:
            r = self.session.get(endpoint)
            request_time = r.elapsed.total_seconds()

            if 200 <= r.status_code < 300:
                self.logger.info("API connection: healthy")
                self.logger.info(f"Status code: {r.status_code}")
                return True
            elif 400 <= r.status_code < 500:
                self.logger.info("API connection interrupted")
                self.logger.info(f"Status code: {r.status_code}")
                return False
        except requests.exceptions.RequestException:
            self.logger.error("API Conncection Dead!")
            return None
        
    def start_scraping(self):

        initial_endpoint= self._request_generator(self.section_url, cursor=None)
        if initial_endpoint:
            initial_response = self._get_response(initial_endpoint)
            if initial_response:
                self.parse(initial_response)
        else:
            self.logger.error("Failed to generate initial endpoint")
            return None
        return self.all_parsed_data


    # Scrapy config
    def _get_response(self, endpoint):
        if self._check_api_connection(endpoint):
            response = self.session.get(endpoint)
            return response


    def parse(self, response):
        """Main parser method"""
        try:
            data = response.json()

            # Now we need to parse through the pages
            # The end paramater will be the new start parameter
            article_data, next_cursor = self._extract_article_data(data)

            page_key = f"Page {self.pages_parsed}"
            self.pages_parsed += 1
            self.all_parsed_data[page_key] = article_data
            self.fetched_articles.append(len(article_data))
            self.pages_left_to_parse -= 1


            if (
                next_cursor
                and self.pages_left_to_parse > 0
                and self.pages_parsed < self.pages_to_parse
            ):
                self.logger.info("Cursor found for next page, starting new request.")
                print("Starting new page")
                next_endpoint = self._request_generator(self.section_url, next_cursor)

                if next_endpoint:
                    next_response = self._get_response(next_endpoint)
                    if next_response:
                        time.sleep(2)
                        self.parse(next_response)
                    else:
                        self.logger.error("Failed to get response for next page.")
                else:
                    self.logger.error("Failed to generate next endpoint.")
            else:
                print(self.all_parsed_data)
                self.logger.info("Pagination complete")

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
        except Exception as e:
            self.logger.error(f"Error in parse method: {e}")

        return self.all_parsed_data





    def _extract_article_data(self, data):
        collection = data["data"]["legacyCollection"]["collectionsPage"]
        articles = collection["stream"]["edges"]
        self.logger.info(f"Processing page, got {len(articles)} artcicles.")

        results = []
        for article in articles:
            article_data = article["node"]
            extracted_data = {
                "headline": article_data["headline"][
                    "default"
                ],  # Need to get text which is in default="headline"
                "summary": article_data["summary"],
                "Published Date": article_data["firstPublished"],
                "url": article_data["url"],
                "News Source": article_data["__typename"],
            }
            results.append(extracted_data)

        next_cursor = collection["stream"]["pageInfo"]["endCursor"]

        return results, next_cursor


class SpiderMetrics:
    def __init__(self):
        self.response_times = deque(maxlen=100)
        self.timestamps = deque(maxlen=100)
        self.success_rates = deque(maxlen=50)

    def add_response_time(self, time_ms: float):
        self.response_times.append(time_ms)
        self.timestamps.append(datetime.now())

    def get_moving_average(self, window: int = 20) -> float:
        if len(self.response_times) < window:
            return sum(self.response_times) / len(self.response_times)

        recent = list(self.response_times)[-window:]
        return sum(recent) / len(recent)

    def get_moving_std(self, window: int = 20):
        if len(self.response_times) <= 1:
            return None

        elif 1 < len(self.response_times) < window:
            arr = np.array(self.response_times)
            return np.std(arr)

        arr = list(self.response_times)[-window:]
        arr = np.array(arr)
        return np.std(arr)

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "response_time": list(self.response_times),
                "timestamp": list(self.timestamps),
            }
        )

class SpiderBehavior:


    ###Spiders need to crawl randomly to not get caught by anti-bot measures###


    def __init__(self, placeholder):
            self.placeholder = placeholder



    def sleep_time(self):

     """Give the spiders random behavior when calling requests."""
        
        rate = 5
        beta = 3.5
        sleep_time = rate * np.random.weibull(3.5, size=1) + np.random.normal()
        return sleep_time




# Running the file:
def test_components():
    business_url = "https://www.nytimes.com/section/business"

    spider = NYTimesSpider(pages_to_parse=3, section_url=business_url)

    # Test token extraction
    print("Getting tokens...")
    spider._header_update()

    # Test endpoint generation
    url = spider.start_urls[0]
    endpoint = spider._request_generator(url)
    print(f"Generated endpoint: {endpoint}")

    # Test API connection
    connection_ok = spider._check_api_connection(endpoint)
    print(f"API connection: {connection_ok}")

    # Test direct API call (bypassing Scrapy)
    if connection_ok:
        results = spider.start_scraping()

    if results:
        total_articles = sum(len(articles) for articles in results.values())
        print(f"Succesfully scraped {len(total_articles)} articles from {len(results)} pages")
    else:
        print("scraping failed")

if __name__ == "__main__":
    test_components()
