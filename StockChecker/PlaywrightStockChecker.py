import random, asyncio, logging, pytz
from StockChecker.ScrapperConfig import All_Products
from StockChecker.WebsiteConfig import All_Websites
from datetime import datetime
from playwright.async_api import async_playwright
from StockChecker.scrapper import ScrapperObj


# Gets or creates a logger
logger = logging.getLogger(__name__)
# define file handler and set formatter
file_handler = logging.FileHandler("StockChecker/logs/PlaywrightStockChecker.log")
formatter = logging.Formatter(
    f"{datetime.now(tz=pytz.timezone('Asia/Kolkata'))} : %(levelname)s : %(name)s : %(message)s"
)  # logs in Indian Standard Time
file_handler.setFormatter(formatter)
# add file handler to logger
logger.addHandler(file_handler)


class PlaywrightClass:
    def __init__(self):
        self.count_dict = {}
        self.error_count_dict = {}

    async def start_playwright(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={"width": 1980, "height": 2080}
        )

    async def get_page_html(self, link, page, headers_list, product_name, website_name):
        default_headers = [
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 20.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4203.116 Safari/537.36"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 20.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 20.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 20.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36"
            },
        ]
        headers = random.choice(headers_list or default_headers)
        try:
            await page.set_extra_http_headers(headers)
            response = await page.goto(link, timeout=300000)
            html = await page.content()
            # 200 - OK , 304 - Sending cached data because data didn't change
            if response.status not in [200, 304]:
                logger.error(
                    f"get_page_html() Error | Product: {product_name} | Website: {website_name} | Status: {response.status} | URL: {link}"
                )
                await ScrapperObj.add_count(
                    dictionary=self.error_count_dict,
                    product_name=product_name,
                    website_name=website_name,
                )
                if response.status == 404:
                    await asyncio.sleep(60)
            else:
                html = await page.content()
                return html
        except asyncio.TimeoutError:
            await ScrapperObj.add_count(
                dictionary=self.error_count_dict,
                product_name=product_name,
                website_name=website_name,
            )

    async def playwright_scrapper(
        self, product_name, website_name, scrapper_function, headers_list=None, delay=30
    ):
        product = All_Products.get(product_name)
        if product is None:
            print(f"{product_name} does not exist in All_Products dict")
            return
        link = product.links.get(website_name)
        if link is None:
            print(f"{product_name} link does not exist in All_Products dict")
            return

        website = All_Websites.get(website_name)
        if website is None:
            print(f"{website_name} does not exist in All_Websites dict")
            return

        page = await self.context.new_page()
        while True:
            page_html = await self.get_page_html(
                link=link,
                page=page,
                headers_list=website.headers,
                product_name=product_name,
                website_name=website_name,
            )
            if page_html:
                outcome = await scrapper_function(page_html, product_name, page)
                if outcome:
                    await ScrapperObj.add_count(
                        dictionary=self.count_dict,
                        website_name=website_name,
                        product_name=product_name,
                    )

                else:
                    await ScrapperObj.add_count(
                        dictionary=self.error_count_dict,
                        product_name=product_name,
                        website_name=website_name,
                    )
                    logger.error(f"{website_name} Error: {product_name} ")

                await asyncio.sleep(delay)
