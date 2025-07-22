from abc import ABC, abstractmethod
import tls_client




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

class BaseWebScraper(ABC):
    def __init__(self, )
    self.network_manager = NetworkManager()
    self.session: = self.network_manager.create_session()
    
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
    
    # # # # # # # # # # # # # # # # # # # # #
    #                                       #
    #       Universal Failsafe methods      #
    #                                       #
    # # # # # # # # # # # # # # # # # # # # #
    
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
        
        
        # TODO: Add enhanced headers from other web browsers
        # TODO: Use conditonals to match new headers with web browsers
        chrome_enhanced_headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }
        
        self.session.headers.update(chrome_enhanced_headers)
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
   
    def _mark_for_session_rotation(self, reason):
        self.session_needs_rotation = True
        self.rotation_reason = reason
        self.logger.warning(f"Session marked for rotation: {reason}")

    
    # # # # # # # # # # # # # # # # # # # # #
    #                                       #
    #           Abstract methods            #
    #                                       #
    # # # # # # # # # # # # # # # # # # # # #
    
  

    @abstractmethod
    def _check_soft_block(self, response):
        pass    
    
    @abstractmethod
    def parse(self, response):
        pass
    
    @abstractmethod
    def get_response(self, endpoint):
        pass
    
    @abstractmethod
    def extract_article_data(self,data):
        pass
    
    
