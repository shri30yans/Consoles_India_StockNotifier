import discord, random, asyncio, aiohttp, logging
from discord.ext import commands
from StockChecker.ScrapperConfig import All_Products
#from collections import OrderedDict
import pytz
from datetime import datetime
import StockChecker.ScrapperConfig as ScrapperConfig

# Gets or creates a logger
logger = logging.getLogger(__name__)

# define file handler and set formatter
file_handler = logging.FileHandler("logs/StockChecker.log")
formatter = logging.Formatter(
    f"{datetime.now(tz=pytz.timezone('Asia/Kolkata'))} : %(levelname)s : %(name)s : %(message)s"
)  # logs in Indian Standard Time
file_handler.setFormatter(formatter)
# add file handler to logger
logger.addHandler(file_handler)


class RequestsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.startup_scrapping())
        self.ScrapperCog = self.bot.get_cog("Scrapper")
        self.count_dict = {}
        self.error_count_dict = {}

    async def get_page_html(self, link, headers_list, product_name, website_name):
        default_headers = [
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36"
            },
        ]
        headers = random.choice(headers_list or default_headers)
        # ordered_headers_list = []
        # for headers in headers_list:
        #     h = OrderedDict()
        #     for header,value in headers.items():
        #         h[header]=value
        #         ordered_headers_list.append(h)
        try:
            async with aiohttp.ClientSession(
                headers=headers, trust_env=True
            ) as session:
                async with session.get(url=link) as response:
                    if response.status not in [
                        200,
                        304,
                    ]:  # 200 > OK , 304 > Sending cached data because data didn't change
                        logger.error(f"Server returned {response.status} URL:{link}")
                        await self.add_count(
                            dictionary=self.error_count_dict,
                            product_name=product_name,
                            website_name=website_name,
                        )
                        if response.status == 404:
                            await asyncio.sleep(60)
                    else:
                        html = await response.text()
                        return html
        except asyncio.TimeoutError:
            await self.add_count(
                dictionary=self.error_count_dict,
                product_name=product_name,
                website_name=website_name,
            )

    async def startup_scrapping(self):
        await self.bot.wait_until_ready()
        self.bot.loop.create_task(
            self.requests_scrapper(
                product_name="WISHLIST",
                website_name="amazon",
                scrapper_function=self.ScrapperCog.scrape_amazon_wishlist,
                delay=20,
            )
        )

        self.bot.loop.create_task(
            self.requests_scrapper(
                product_name="PS5",
                website_name="flipkart",
                scrapper_function=self.ScrapperCog.scrape_flipkart,
                delay=20,
            )
        )
        self.bot.loop.create_task(
            self.requests_scrapper(
                product_name="PS5_DE",
                website_name="flipkart",
                scrapper_function=self.ScrapperCog.scrape_flipkart,
                delay=20,
            )
        )
        self.bot.loop.create_task(
            self.requests_scrapper(
                product_name="XSX",
                website_name="flipkart",
                scrapper_function=self.ScrapperCog.scrape_flipkart,
                delay=20,
            )
        )
        # self.bot.loop.create_task(
        #     self.requests_scrapper(
        #         product_name="XSS",
        #         website_name="flipkart",
        #         scrapper_function=self.ScrapperCog.scrape_flipkart,
        #         delay=20,
        #     )
        # )

        self.bot.loop.create_task(
            self.requests_scrapper(
                product_name="PS5",
                website_name="shopatsc",
                scrapper_function=self.ScrapperCog.scrape_shopatsc,
                delay=20,
            )
        )
        self.bot.loop.create_task(
            self.requests_scrapper(
                product_name="PS5_DE",
                website_name="shopatsc",
                scrapper_function=self.ScrapperCog.scrape_shopatsc,
                delay=20,
            )
        )
        # self.bot.loop.create_task(
        #     self.requests_scrapper(
        #         product_name="RED_DS",
        #         website_name="shopatsc",
        #         scrapper_function=self.ScrapperCog.scrape_shopatsc,
        #         delay=20,
        #     )
        # )
        # self.bot.loop.create_task(
        #     self.requests_scrapper(
        #         product_name="BLACK_DS",
        #         website_name="shopatsc",
        #         scrapper_function=self.ScrapperCog.scrape_shopatsc,
        #         delay=20,
        #     )
        # )
        self.bot.loop.create_task(
            self.requests_scrapper(
                product_name="PS5",
                website_name="reliance",
                scrapper_function=self.ScrapperCog.scrape_reliance,
                delay=20,
            )
        )
        self.bot.loop.create_task(
            self.requests_scrapper(
                product_name="PS5_DE",
                website_name="reliance",
                scrapper_function=self.ScrapperCog.scrape_reliance,
                delay=20,
            )
        )
        self.bot.loop.create_task(
            self.requests_scrapper(
                product_name="XSX",
                website_name="reliance",
                scrapper_function=self.ScrapperCog.scrape_reliance,
                delay=20,
            )
        )

        self.bot.loop.create_task(
            self.requests_scrapper(
                product_name="PS5",
                website_name="ppgc",
                scrapper_function=self.ScrapperCog.scrape_ppgc,
                delay=20,
            )
        )
        self.bot.loop.create_task(
            self.requests_scrapper(
                product_name="PS5_DE",
                website_name="ppgc",
                scrapper_function=self.ScrapperCog.scrape_ppgc,
                delay=20,
            )
        )
        self.bot.loop.create_task(
            self.requests_scrapper(
                product_name="XSX",
                website_name="ppgc",
                scrapper_function=self.ScrapperCog.scrape_ppgc,
                delay=20,
            )
        )

        # self.bot.loop.create_task(
        #     self.requests_scrapper(
        #         product_name="PS5",
        #         website_name="games_the_shop",
        #         scrapper_function=self.ScrapperCog.scrape_games_the_shop,
        #         delay=20,
        #     )
        # )
        # self.bot.loop.create_task(
        #     self.requests_scrapper(
        #         pproduct_name="PS5_DE",
        #         website_name="games_the_shop",
        #         scrapper_function=self.ScrapperCog.scrape_games_the_shop,
        #         delay=20,
        #     )
        # )

    async def requests_scrapper(
        self, product_name, website_name, scrapper_function, headers_list=None, delay=30):
        product = All_Products.get(product_name)
        if product is None:
            print(f"{product_name} does not exist in All_Products dict")
            return
        link = product.links.get(website_name)
        if link is None:
            print(f"{product_name} link does not exist in All_Products dict")
            return
        while True:
            page_html = await self.get_page_html(
                link=link,
                headers_list=headers_list,
                product_name=product_name,
                website_name=website_name,
            )
            if page_html:
                outcome = await scrapper_function(page_html, product_name)
                if outcome:
                    await self.add_count(
                        dictionary=self.count_dict,
                        website_name=website_name,
                        product_name=product_name,
                    )

                else:
                    await self.add_count(
                        dictionary=self.error_count_dict,
                        product_name=product_name,
                        website_name=website_name,
                    )
                    logger.error(f"{website_name} Error: {product_name} ")
                await asyncio.sleep(delay)

    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command(
        name="RunCount",
        aliases=["rc"],
        help=f"Shows how many times the RequestsStockChecker has ran successfully.",
    )
    async def runcount(self, ctx):
        embed = discord.Embed(
            Title="Run Count",
            description="Showing number of times RequestsStockChecker has run succesfully on each site.",
            colour=0x0000FF,
        )
        for product_name in self.count_dict:
            value = ""
            for website_name in self.count_dict.get(product_name):
                Website_Class = ScrapperConfig.All_Websites.get(website_name)
                def return_count(dict, product_name, website_name):
                    product_count_dict = dict.get(product_name)
                    if product_count_dict is not None:
                        website_count = product_count_dict.get(website_name)
                        if website_count is not None:
                            return website_count

                count = return_count(self.count_dict, product_name, website_name)
                error_count = return_count(self.error_count_dict, product_name, website_name)

                value += f"\u2800\u2800**{Website_Class.display_name}** \n\u2800\u2800\u2800Count: {str(count)}\n\u2800\u2800\u2800Errored out: {str(error_count)}\n"
            product = ScrapperConfig.All_Products.get(product_name)
            embed.add_field(name=f"{product.emoji} {product.display_name}",value=value,inline=False,)

        await ctx.send(embed=embed)

    async def add_count(self, dictionary, product_name, website_name):
        product_value = dictionary.get(product_name)
        if product_value is None:
            dictionary[product_name] = {}
            dictionary[product_name][website_name] = 1
        else:
            count = product_value.get(website_name)
            if count is None:
                dictionary[product_name][website_name] = 1
            else:
                if dictionary[product_name][website_name] > 10000:
                    dictionary[product_name][website_name] = 0
                else:
                    dictionary[product_name][website_name] += 1

def setup(bot):
    bot.add_cog(RequestsCog(bot))
