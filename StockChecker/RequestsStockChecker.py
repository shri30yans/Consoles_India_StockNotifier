import random, asyncio, aiohttp, logging
from StockChecker.ScrapperConfig import All_Products, All_Websites
from StockChecker.scrapper import ScrapperObj
from utils.headers import default_headers

# from collections import OrderedDict
import pytz
from datetime import datetime


# Gets or creates a logger
logger = logging.getLogger(__name__)

# define file handler and set formatter
file_handler = logging.FileHandler("StockChecker/logs/RequestsStockChecker.log")
formatter = logging.Formatter(
    f"{datetime.now(tz=pytz.timezone('Asia/Kolkata'))} : %(levelname)s : %(name)s : %(message)s"
)  # logs in Indian Standard Time
file_handler.setFormatter(formatter)
# add file handler to logger
logger.addHandler(file_handler)


class RequestsClass:
    def __init__(self):
        self.count_dict = {}
        self.error_count_dict = {}

    async def get_page_html(self, link, headers_list, product_name, website_name):
        headers = random.choice(headers_list or default_headers)

        # ordered_headers_list = []
        # # Sort headers
        # for x in headers:
        #     h = OrderedDict()
        #     for header,value in headers.items():
        #         h[header]=value
        #         ordered_headers_list.append(h)

        try:
            async with aiohttp.ClientSession(
                headers=headers, trust_env=True
            ) as session:
                async with session.get(url=link) as response:
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
                        if response.status in [404]:
                            await asyncio.sleep(60)
                    else:
                        html = await response.text()
                        return html

        except asyncio.TimeoutError:
            await ScrapperObj.add_count(
                dictionary=self.error_count_dict,
                product_name=product_name,
                website_name=website_name,
            )

    async def requests_scrapper(
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

        while True:
            page_html = await self.get_page_html(
                link=link,
                headers_list=website.headers,
                product_name=product_name,
                website_name=website_name,
            )
            if page_html:
                outcome = await scrapper_function(page_html, product_name)
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

                # random_delay = delay + random.randrange(-5,+6)
                await asyncio.sleep(delay)

