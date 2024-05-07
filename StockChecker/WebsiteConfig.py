class Website:
    def __init__(
        self,
        display_name: str,
        name: str,
        wishlist_link: str = None,
        wishlist_products=None,
        headers: list = None,
    ):
        self.name = name
        self.display_name = display_name
        self.wishlist_link = wishlist_link
        self.wishlist_products = wishlist_products
        self.headers = headers


class Amazon_Wishlist_Item:
    def __init__(self, name, ASIN, max_cost=None):
        self.name = name
        self.ASIN = ASIN
        self.max_cost = max_cost


All_Websites = {
    "amazon": Website(
        display_name="Amazon",
        name="amazon",
        wishlist_products={
            # "RED_DS": Amazon_Wishlist_Item(
            #     name="RED_DS", ASIN="B098439Y2G", max_cost=6500
            # ),
            # "BLACK_DS": Amazon_Wishlist_Item(
            #     name="BLACK_DS", ASIN="B09842ZHNM", max_cost=6000
            # ),
            "PS5": Amazon_Wishlist_Item(
                name="PS5", ASIN="B09V59MD1P"),
            "PS5_DE": Amazon_Wishlist_Item(
                name="PS5_DE", ASIN="B09V58Q6DY"
            ),
            "PS5_GT7_BUNDLE": Amazon_Wishlist_Item(
                name="PS5_GT7_BUNDLE", ASIN="B09YD71MZT"
            ),
            "PS5_HFW_BUNDLE": Amazon_Wishlist_Item(
                name="PS5_HFW_BUNDLE", ASIN="B0B9GH5TTN"
            ),
            "PS5_DE_GT7_BUNDLE": Amazon_Wishlist_Item(
                name="PS5_DE_HFW_BUNDLE", ASIN="B0B9GDVHQQ"
            ),
            # "PS5_DE_REMOTE_BUNDLE": Amazon_Wishlist_Item(
            #     name="PS5_DE_REMOTE_BUNDLE", ASIN="B08NTVH9VG"
            # ),
            # "PS5_DE_PULSE_BUNDLE": Amazon_Wishlist_Item(
            #     name="PS5_DE_PULSE_BUNDLE", ASIN="B08NTV1QDX"
            # ),
            # "PS5_DE_CHARGING_STATION_BUNDLE": Amazon_Wishlist_Item(
            #     name="PS5_DE_CHARGING_STATION_BUNDLE", ASIN="B08NTVHTPT"
            # ),
            # "DS_CHARGING_STATION": Amazon_Wishlist_Item(
            #     name="DS_CHARGING_STATION", ASIN="B08FVMT8QN"
            # ),
            # "WHITE_PULSE_3D": Amazon_Wishlist_Item(
            #     name="WHITE_PULSE_3D", ASIN="B08FVNCYWZ"
            # ),
            # "BLACK_PULSE_3D": Amazon_Wishlist_Item(
            #     name="BLACK_PULSE_3D",
            #     ASIN=""
            # ),
            # "XSS": Amazon_Wishlist_Item(
            #     name="XSS",
            #     ASIN="B08J89D6BW",
            #     max_cost=35000
            # ),
            "XSX": Amazon_Wishlist_Item(
                name="XSX",
                ASIN="B08J7QX1N1",
            ),
            "XSX_HALO_EDITION": Amazon_Wishlist_Item(
                name="XSX_HALO_EDITION",
                ASIN="B09LMY7K1L",
            ),
            # "XSX_20TH_ANNIVERSARY_EDITION_CONTROLLER": Amazon_Wishlist_Item(
            #     name="XSX_20TH_ANNIVERSARY_EDITION_CONTROLLER",
            #     ASIN="B09HTV3Q3T",
            # ),
            # "XBOX_WIRELESS_HEADSET": Amazon_Wishlist_Item(
            #     name="XBOX_WIRELESS_HEADSET",
            #     ASIN="B09HSHXYCR",
            # ),
            "XSX_GEARS_TACTIC_BUNDLE": Amazon_Wishlist_Item(
                name="XSX_GEARS_TACTIC_BUNDLE", ASIN="B08NRLQ294"
            ),
            "XSX_BLUE_CONTROLLER_BUNDLE": Amazon_Wishlist_Item(
                name="XSX_BLUE_CONTROLLER_BUNDLE", ASIN="B08NRBNSPW"
            ),
            "XSX_WHITE_CONTROLLER_BUNDLE": Amazon_Wishlist_Item(
                name="XSX_WHITE_CONTROLLER_BUNDLE", ASIN="B08NRLS39X"
            ),
            "XSX_BLACK_CONTROLLER_BUNDLE": Amazon_Wishlist_Item(
                name="XSX_BLACK_CONTROLLER_BUNDLE", ASIN="B08NQZGSJ2"
            ),
        },
        headers=[
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.5",
                "Content-Type": "application/json",
                "Origin": "https://www.amazon.in/",
                "DNT": "1",
                "Referer": "https://www.amazon.in/",
            },
            {
                "authority": "www.amazon.in",
                "dnt": "1",
                "rtt": "200",
                "sec-ch-ua-mobile": "?0",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
                "accept": "text/html,/",
                "ect": "4g",
                "sec-ch-ua": "^^",
                "origin": "https://www.amazon.in/",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://www.amazon.in/",
                "accept-language": "en-US,en;q=0.9",
            },
            {
                "Connection": "keep-alive",
                "sec-ch-ua": "^^",
                "Accept": "application/json, text/javascript, /; q=0.01",
                "sec-ch-ua-mobile": "?0",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
                "Origin": "https://www.amazon.in/",
                "Referer": "https://www.amazon.in/",
                "DNT": "1",
                "Accept-Language": "en-GB,en;q=0.9",
            },
            {
                "authority": "www.amazon.in",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
                "content-type": "application/x-www-form-urlencoded",
                "accept": "text/html,*/*",
                "ect": "4g",
                "origin": "https://www.amazon.in",
                "referer": "https://www.amazon.in/",
                "DNT": "1",
                "accept-language": "en-US,en;q=0.9",
            },
        ],
    ),
    "flipkart": Website(
        display_name="Flipkart",
        name="flipkart",
        headers=[
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
                "Accept": "*/*",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
                "origin": "https://www.flipkart.com",
                "referer": "https://www.flipkart.com/",
                "accept-language": "en-IN,en;q=0.9",
                "DNT": "1",
                "Referer": "https://www.flipkart.com/",
            },
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
                "accept": "*/*",
                "referer": "https://www.flipkart.com/",
                "accept-language": "en-US,en;q=0.9",
                "origin": "https://www.flipkart.com",
                "DNT": "1",
            },
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
                "referer": "https://www.google.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
                "DNT": "1",
                "origin": "https://www.flipkart.com",
            },
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "origin": "https://www.google.com",
                "referer": "https://www.flipkart.com/",
                "DNT": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            },

            # Below this all random Headers are used.
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "origin": "https://www.google.com",
                "referer": "https://www.flipkart.com/",
                "DNT": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
            }, 
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                "accept-encoding": "gzip, deflate, br",
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                "referer": "https://www.flipkart.com/",
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/97.0.4692.84 Mobile/15E148 Safari/604.1',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                "referer": "https://www.google.in/",
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            },
            
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (iPad; CPU OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/97.0.4692.84 Mobile/15E148 Safari/604.1',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                "referer": "https://www.google.in/",
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.98 Mobile Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                "referer": "https://www.google.com/",
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 10; SM-N960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.98 Mobile Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                "referer": "https://www.flipkart.com/",
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 9; SM-N950F Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.google.com/",
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 7.0; SM-G610M Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/69.0.3497.100 Mobile Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.google.com/",
            },
             {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 7.1.2; AFTMM Build/NS6265; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/70.0.3538.110 Mobile Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.google.com/",
            },
             {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G930F Build/R16NW; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.google.com/",
            },
             {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 7.1.1; SM-T567V Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/70.0.3538.80 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.google.com/",
            },
             {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 9; SM-N950F Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.google.com/",
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G935F Build/R16NW; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.flipkart.com/",
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 7.1.2; AFTMM Build/NS6265; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/70.0.3538.110 Mobile Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-GB',
                "referer": "https://www.google.com/",
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Windows85.0.4183.121 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.google.com/",
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.flipkart.com/",
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-US',
                "referer": "https://www.google.com/",
            },
        ],
    ),
    "shopatsc": Website(
        display_name="ShopAtSC",
        name="shopatsc",
    ),
    "reliance": Website(
        display_name="Reliance Digital",
        name="reliance",
    ),
    "games_the_shop": Website(
        display_name="Games the Shop",
        name="games_the_shop",
    ),
    "e2zstore": Website(
        display_name="E2Zstore",
        name="e2zstore",
    ),
}