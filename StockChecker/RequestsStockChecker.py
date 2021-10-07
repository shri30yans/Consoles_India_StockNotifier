import discord,random,asyncio,aiohttp,re,logging
from discord.ext import commands
import lxml.html
import config
from StockChecker.ScrapperConfig import All_Websites
from collections import OrderedDict
from bs4 import BeautifulSoup
import pytz
from datetime import datetime 
# Gets or creates a logger
logger = logging.getLogger(__name__)  

# define file handler and set formatter
file_handler = logging.FileHandler('logs/StockChecker.log')
formatter    = logging.Formatter(f"{datetime.now(tz=pytz.timezone('Asia/Kolkata'))} : %(levelname)s : %(name)s : %(message)s")#logs in Indian Standard Time
file_handler.setFormatter(formatter)
# add file handler to logger
logger.addHandler(file_handler)



# How the bot checks for Stock availability?
# Instead of using selenium to replicate a browser experience it uses the requests library to fetch the HTML code of a URL. The Bot then uses another library to scour the HTML code to and looks for certain keywords in a specified location.
# Logic:
# Amazon: Amazon has a seperate divison in it's HTML page called Availabilty which allows me to check if a product is "Currently unavailable." or "In Stock"
# Flipkart: Flipkart has a seperate element to display Out of Stock. In case the product is available that element gives no value. The bot checks if that element is not displayed and double checks if the Add to Cart Button Exists.
# ShopatSC: The Notify button has a property that makes it invisble if stock is present
#  Games the Shop: Games the Shop shows the Add to Cart Button when the product is available.
# Prepaid Gamer Card: Prepaid Gamer Card shows the Add to Cart Button when the product is available.



class RequestsCog(commands.Cog): 
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.startup())
        self.scrapper = self.bot.get_cog("Scrapper")


        self.count_dict={   
                        "WISHLIST":{"amazon":0},
                        "PS5":{"amazon":0,"flipkart":0,"games_the_shop":0,"ppgc":0,"shopatsc":0},
                        "PS5_DE":{"amazon":0,"flipkart":0,"games_the_shop":0,"ppgc":0,"shopatsc":0},
                        "XSX":{"amazon":0,"flipkart":0},
                        "XSS":{"amazon":0,"flipkart":0},
                        "RED_DS":{"amazon":0,"flipkart":0,"shopatsc":0},
                        "BLACK_DS":{"amazon":0,"flipkart":0,"shopatsc":0},}
       
        self.error_count_dict={   
                            "WISHLIST":{"amazon":0},
                            "PS5":{"amazon":0,"flipkart":0,"games_the_shop":0,"ppgc":0,"shopatsc":0},
                            "PS5_DE":{"amazon":0,"flipkart":0,"games_the_shop":0,"ppgc":0,"shopatsc":0},
                            "XSX":{"amazon":0,"flipkart":0},
                            "XSS":{"amazon":0,"flipkart":0},
                            "RED_DS":{"amazon":0,"shopatsc":0},
                            "BLACK_DS":{"amazon":0,"shopatsc":0},}
   
    #async def get_page_html(self,link,headers_list=[{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}]):
    async def get_page_html(self,link,headers_list,product,website_name):
        default_headers = [{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"},{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"},{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36"},{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36"}]
        headers=random.choice(headers_list or default_headers)
        #ordered_headers_list = []
        # for headers in headers_list:
        #     h = OrderedDict()
        #     for header,value in headers.items():
        #         h[header]=value
        #         ordered_headers_list.append(h)
        try:
            async with aiohttp.ClientSession(headers=headers,trust_env=True) as session:
                async with session.get(url=link) as response:
                    if response.status not in [200,304]:#200 > OK , 304 > Sending cached data because data didn't change
                        logger.error(f'Server returned {response.status} URL:{link}')
                        if response.status == 404:
                            await self.add_error(product=product,website_name=website_name)
                            await asyncio.sleep(30)
                    else:
                        html = await response.text()
                        return html
        except asyncio.TimeoutError:
            await self.add_error(product=product,website_name=website_name)


   
    async def startup(self): 
        await self.bot.wait_until_ready()  
        self.bot.loop.create_task(self.scrape_amazon_wishlist(amazon_wishlist_link=All_Websites["amazon"].wishlist_link,delay=30,headers_list=All_Websites["amazon"].headers)) 
        #self.bot.loop.create_task(self.scrape_amazon(product="PS5",delay=30,headers_list=All_Websites["amazon"].headers)) 
        # self.bot.loop.create_task(self.scrape_amazon(product="PS5_DE",delay=30,headers_list=All_Websites["amazon"].headers)) 
        # self.bot.loop.create_task(self.scrape_amazon(product="XSX",delay=30,headers_list=All_Websites["amazon"].headers))
        # self.bot.loop.create_task(self.scrape_amazon(product="XSS",delay=45,headers_list=All_Websites["amazon"].headers))
        # self.bot.loop.create_task(self.scrape_amazon(product="RED_DS",delay = 60,headers_list=All_Websites["amazon"].headers))
        # self.bot.loop.create_task(self.scrape_amazon(product="BLACK_DS",delay = 60,headers_list=All_Websites["amazon"].headers))

        self.bot.loop.create_task(self.scrape_flipkart(product="PS5",delay=20))
        self.bot.loop.create_task(self.scrape_flipkart(product="PS5_DE",delay=20))
        self.bot.loop.create_task(self.scrape_flipkart(product="XSX",delay=20))
        self.bot.loop.create_task(self.scrape_flipkart(product="XSS",delay=20))

        # self.bot.loop.create_task(self.scrape_shopatsc(product="PS5",delay=20))
        # self.bot.loop.create_task(self.scrape_shopatsc(product="PS5_DE",delay=20))
        # self.bot.loop.create_task(self.scrape_shopatsc(product="RED_DS",delay = 60))
        # self.bot.loop.create_task(self.scrape_shopatsc(product="BLACK_DS",delay = 60))

        # self.bot.loop.create_task(self.scrape_games_the_shop(product="PS5",delay=20))
        # self.bot.loop.create_task(self.scrape_ppgc(product="PS5",delay=20))
        

    async def scrape_amazon_wishlist(self,amazon_wishlist_link,headers_list=None,delay=30):
        product="WISHLIST"
        while True:
            page_html = await self.get_page_html(link=amazon_wishlist_link,headers_list=headers_list,product="WISHLIST",website_name="amazon")
            if page_html:
                outcome = await self.scrapper.scrape_amazon_wishlist(page_html)
                if outcome:
                    pass
                    await self.add_count(website_name="amazon",product='WISHLIST')
                    
                else:
                    await self.add_error(product=product,website_name="amazon")
                    logger.error(f'Amazon Error Wishlist: Both attributes do not exist.')
                await asyncio.sleep(delay)

    
    async def scrape_amazon(self,product,headers_list=None,delay=30):  
        while True:
            page_html = await self.get_page_html(link=All_Websites["amazon"].links.get(product),headers_list=headers_list,product=product,website_name="amazon")
            if page_html == False:
                await self.add_error(product=product,website_name="amazon")
                
            else:
                outcome = await self.scrapper.scrape_amazon(page_html,product)
                
                if outcome:
                    await self.add_count(website_name="amazon",product=product)
                    
                else:
                    logger.error(f'Amazon Error Product: {product}')
            await asyncio.sleep(delay)

    async def scrape_flipkart(self,product,headers_list=None,delay=30):
        while True:
            page_html = await self.get_page_html(All_Websites["flipkart"].links.get(product),headers_list = headers_list,product=product,website_name="flipkart")
            if page_html == False:
                await self.add_error(product=product,website_name="flipkart")
                await asyncio.sleep(delay)
            else:
                outcome = await self.scrapper.scrape_flipkart(page_html,product)
                
                if outcome:
                    await self.add_count(website_name="flipkart",product=product)
                    
                else:
                    logger.error(f'Flipkart Error Product: {product}')
            await asyncio.sleep(delay)
        
    async def scrape_shopatsc(self,product,headers_list=None,delay=30):
        while True:
            page_html = await self.get_page_html(link=All_Websites["shopatsc"].links.get(product),headers_list = headers_list,product=product,website_name="shopatsc")
            if page_html == False:
                await self.add_error(product=product,website_name="shopatsc")
                
            else:
                outcome = await self.scrapper.scrape_shopatsc(page_html,product)
                
                if outcome:
                    await self.add_count(website_name="shopatsc",product=product)
                    
                else:
                    logger.error(f'ShopAtSC Error Product: {product}')
            await asyncio.sleep(delay)


    async def scrape_games_the_shop(self,product,headers_list=None,delay=30):
        while True:
            page_html = await self.get_page_html(link=All_Websites["games_the_shop"].links.get(product),headers_list = headers_list,product=product,website_name="games_the_shop")
            if page_html == False:
                await self.add_error(product=product,website_name="games_the_shop")
            else:
                outcome = await self.scrapper.scrape_games_the_shop(page_html,product)
                
                if outcome:
                    await self.add_count(website_name="games_the_shop",product=product)
                    
                else:
                    logger.error(f'Games the shop Error Product: {product}')
            await asyncio.sleep(delay)


    async def scrape_ppgc(self,product,headers_list=None,delay=30):
        while True:
            page_html = await self.get_page_html(link=All_Websites["ppgc"].links.get(product),headers_list = headers_list,product=product,website_name="ppgc")
            if page_html == False:
                await self.add_error(product=product,website_name="ppgc")
                continue
            else:
                outcome = await self.scrapper.scrape_ppgc(page_html,product)
                
                if outcome:
                    await self.add_count(website_name="ppgc",product=product)
                    
                else:
                    logger.error(f'PPGC Error Product: {product}')
            await asyncio.sleep(delay)
    
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command(name="RunCount",aliases=["rc"], help=f'Shows how many times the RequestsStockChecker has ran successfully. \n{config.prefix}runcount')
    async def runcount(self,ctx):
        embed=discord.Embed(Title="Run Count",description="Showing number of times RequestsStockChecker has run succesfully on each site.",colour=0x0000FF)
        embed.add_field(name = "Amazon wishlist",value = f"\u2800📜  **Wishlist**:\n\u2800\u2800{self.count_dict['WISHLIST']['amazon']} times.\
                        \n\u2800\u2800Errored out: {self.error_count_dict['WISHLIST']['amazon']} times.")
        embed.add_field(name="Amazon",value=f"""\u2800{config.PS5_emoji}  **PS5**:\n\u2800\u2800{self.count_dict['PS5']['amazon']} times.\
                                                \n\u2800\u2800Errored out: {self.error_count_dict['PS5']['amazon']} times.\
                                                \n\u2800{config.PS5_emoji}  **PS5 DE**:\n\u2800\u2800{self.count_dict['PS5_DE']['amazon']} times.\
                                                \n\u2800\u2800Errored out: {self.error_count_dict['PS5_DE']['amazon']} times.\
                                                \n\u2800{config.XSX_emoji}  **XSX**:\n\u2800\u2800{self.count_dict['XSX']['amazon']} times.\
                                                \n\u2800\u2800Errored out: {self.error_count_dict['XSX']['amazon']} times.\
                                                \n\u2800{config.XSS_emoji}  **XSS**:\n\u2800\u2800{self.count_dict['XSS']['amazon']} times.\
                                                \n\u2800\u2800Errored out: {self.error_count_dict['XSS']['amazon']} times.\
                                                \n\u2800{config.RED_DS_emoji}  **RED DS**:\n\u2800\u2800{self.count_dict['RED_DS']['amazon']} times.\
                                                \n\u2800\u2800Errored out: {self.error_count_dict['RED_DS']['amazon']} times.\
                                                \n\u2800{config.BLACK_DS_emoji}  **BLACK DS**:\n\u2800\u2800{self.count_dict['BLACK_DS']['amazon']} times.\
                                                \n\u2800\u2800Errored out: {self.error_count_dict['BLACK_DS']['amazon']} times.""",inline=False)

        embed.add_field(name="Flipkart",value=f"""\u2800{config.PS5_emoji}  **PS5**:\n\u2800\u2800{self.count_dict['PS5']['flipkart']} times.\
                                                \n\u2800\u2800Errored out: {self.error_count_dict['PS5']['flipkart']} times.\
                                                \n\u2800{config.PS5_emoji}  **PS5 DE**:\n\u2800\u2800{self.count_dict['PS5_DE']['flipkart']} times.\
                                                \n\u2800\u2800Errored out: {self.error_count_dict['PS5_DE']['flipkart']} times.\
                                                \n\u2800{config.XSX_emoji}  **XSX**:\n\u2800\u2800{self.count_dict['XSX']['flipkart']} times.\
                                                \n\u2800\u2800Errored out: {self.error_count_dict['XSX']['flipkart']} times.\
                                                \n\u2800{config.XSS_emoji}  **XSS**:\n\u2800\u2800{self.count_dict['XSS']['flipkart']} times. \
                                                \n\u2800\u2800Errored out: {self.error_count_dict['XSS']['flipkart']} times.""",inline=False)

        embed.add_field(name="ShopAtSC",value=f"""\u2800{config.PS5_emoji}  **PS5**:\n\u2800\u2800{self.count_dict['PS5']['shopatsc']} times.\
                                                \n\u2800\u2800Errored out: {self.error_count_dict['PS5']['shopatsc']} times.\n\u2800{config.PS5_emoji}  **PS5 DE**:\
                                                \n\u2800\u2800{self.count_dict['PS5_DE']['shopatsc']} times. \n\u2800\u2800Errored out: {self.error_count_dict['PS5_DE']['shopatsc']} times.\
                                                \n\u2800{config.RED_DS_emoji}  **RED DS**:\n\u2800\u2800{self.count_dict['RED_DS']['shopatsc']} times. \
                                                \n\u2800\u2800Errored out: {self.error_count_dict['RED_DS']['shopatsc']} times.\
                                                \n\u2800{config.BLACK_DS_emoji}  **BLACK DS**:\n\u2800\u2800{self.count_dict['BLACK_DS']['shopatsc']} times. \
                                                \n\u2800\u2800Errored out: {self.error_count_dict['BLACK_DS']['shopatsc']} times.""",inline=False)

        embed.add_field(name="Games the Shop",value=f"""\u2800{config.PS5_emoji}  **PS5**:\n\u2800\u2800{self.count_dict['PS5']['games_the_shop']} times.\
                                                \n\u2800\u2800Errored out: {self.error_count_dict['PS5']['games_the_shop']} times.""",inline=False)
                                                
        embed.add_field(name="Prepaid Gamer Card",value=f"""\u2800{config.PS5_emoji}  **PS5**:\n\u2800\u2800{self.count_dict['PS5']['ppgc']} times. \
                                                \n\u2800\u2800Errored out: {self.error_count_dict['PS5']['ppgc']} times.""",inline=False)
        await ctx.send(embed=embed) 
    
                

    async def add_count(self,product,website_name):
        if  self.count_dict[product][website_name] > 10000:
            self.count_dict[product][website_name] = 0
        try:
            self.count_dict[product][website_name]+=1
        except:
            print("Add count exception")

    async def add_error(self,product,website_name):
        if  self.error_count_dict[product][website_name] > 10000:
            self.error_count_dict[product][website_name] = 0
        try:
            self.error_count_dict[product][website_name]+=1
        except:
            print("Add error exception")
  


def setup(bot):
    bot.add_cog(RequestsCog(bot))