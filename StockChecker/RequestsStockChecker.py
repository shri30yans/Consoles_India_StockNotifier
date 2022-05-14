import discord, random, asyncio, aiohttp, logging
from discord.ext import commands
from StockChecker.ScrapperConfig import All_Products, All_Websites

from collections import OrderedDict
import pytz
from datetime import datetime
import StockChecker.ScrapperConfig as ScrapperConfig

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


class RequestsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.count_dict = {}
        self.error_count_dict = {}

    async def get_page_html(self, link, headers_list, product_name, website_name):
        default_headers = [
            # {
            #     "User-Agent": "Mozilla/5.0 (Windows NT 20.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4203.116 Safari/537.36"
            # },
            # {
            #     "User-Agent": "Mozilla/5.0 (Windows NT 20.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
            # },
            # {
            #     "User-Agent": "Mozilla/5.0 (Windows NT 20.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36"
            # },
            # {
            #     "User-Agent": "Mozilla/5.0 (Windows NT 20.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36"
            # },
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.2 Safari/537.36"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.90 Safari/537.36"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.60 Safari/537.17"
            },
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/537.13 (KHTML, like Gecko) Chrome/24.0.1290.1 Safari/537.13"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.0) yi; AppleWebKit/345667.12221 (KHTML, like Gecko) Chrome/23.0.1271.26 Safari/453667.1221"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3"
            },
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
            },
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.45 Safari/535.19"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.66 Safari/535.11"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.0; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.66 Safari/535.11"
            },
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.11 (KHTML, like Gecko) Ubuntu/11.10 Chromium/17.0.963.65 Chrome/17.0.963.65 Safari/535.11"
            },
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Ubuntu/11.04 Chromium/17.0.963.56 Chrome/17.0.963.56 Safari/535.11"
            },
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11"
            },
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) Gecko/20100101 Firefox/73.0"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; rv:68.7) Gecko/20100101 Firefox/68.7"
            },
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.10; rv:62.0) Gecko/20100101 Firefox/62.0"
            },
            {
                "User-Agent": "Mozilla/5.0 (X11;  Ubuntu; Linux i686; rv:52.0) Gecko/20100101 Firefox/52.0"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20130401 Firefox/31.0"
            },
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:28.0) Gecko/20100101  Firefox/28.0"
            },
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:24.0) Gecko/20100101 Firefox/24.0"
            },

        ]
        headers = random.choice(headers_list or default_headers)
        
        #ordered_headers_list = []
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
                        await self.add_count(
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
            await self.add_count(
                dictionary=self.error_count_dict,
                product_name=product_name,
                website_name=website_name,
            )

    async def make_GUI_loading(self, product, website_name):
        GUI = self.bot.get_cog("GUI")
        if GUI is not None:  # if the GUI cog is loaded
            if product.subproducts:
                for x in product.subproducts:
                    await GUI.update_values(x, website_name, None)
            else:
                await GUI.update_values(product.name, website_name, None)

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
            await self.make_GUI_loading(product, website_name)
            page_html = await self.get_page_html(
                link=link,
                headers_list=website.headers,
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

                #random_delay = delay + random.randrange(-5,+6)
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
                error_count = return_count(
                    self.error_count_dict, product_name, website_name
                )

                value += f"\u2800\u2800**{Website_Class.display_name}** \n\u2800\u2800\u2800Success: {str(count)}\n\u2800\u2800\u2800Errored out: {str(error_count)}\n"
            product = ScrapperConfig.All_Products.get(product_name)
            embed.add_field(
                name=f"{product.emoji} {product.display_name}",
                value=value,
                inline=False,
            )

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
