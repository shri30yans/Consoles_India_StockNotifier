import re
import discord,random,asyncio,time,aiohttp
from discord.ext import commands,tasks
import lxml.html
import config
from utils.links import All_Websites
from collections import OrderedDict
from bs4 import BeautifulSoup


# How the bot checks for Stock availability?
# Instead of using selenium to replicate a browser experience it uses the requests library to fetch the HTML code of a URL. The Bot then uses another library to scour the HTML code to and looks for certain keywords in a specified location.
# Logic:
# Amazon: Amazon has a seperate divison in it's HTML page called Availabilty which allows me to check if a product is "Currently unavailable." or "In Stock"
# Flipkart: Flipkart has a seperate element to display Out of Stock. In case the product is available that element gives no value. The bot checks if that element is not displayed and double checks if the Add to Cart Button Exists.
# Games the Shop: Games the Shop shows the Add to Cart Button when the product is available.
# Prepaid Gamer Card: Prepaid Gamer Card shows the Add to Cart Button when the product is available.



class StockChecker(commands.Cog): 
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.startup())

        self.count_dict={   
                        "PS5":{"amazon":0,"flipkart":0,"games_the_shop":0,"ppgc":0,"shopatsc":0},
                        "PS5_DE":{"amazon":0,"flipkart":0,"games_the_shop":0,"ppgc":0,"shopatsc":0},
                        "XSX":{"amazon":0,"flipkart":0},
                        "XSS":{"amazon":0,"flipkart":0}}
       
        self.error_count_dict={   
                            "PS5":{"amazon":0,"flipkart":0,"games_the_shop":0,"ppgc":0,"shopatsc":0},
                            "PS5_DE":{"amazon":0,"flipkart":0,"games_the_shop":0,"ppgc":0,"shopatsc":0},
                            "XSX":{"amazon":0,"flipkart":0},
                            "XSS":{"amazon":0,"flipkart":0}}

        
        self.last_website_notifications=None

    def add_count(self,product,website_name):
        if  self.count_dict[product][website_name] > 10000:
            self.count_dict[product][website_name] = 0
        try:
            self.count_dict[product][website_name]+=1
        except:
            print("Add count exception")

    def add_error(self,product,website_name):
        if  self.error_count_dict[product][website_name] > 10000:
            self.error_count_dict[product][website_name] = 0
        try:
            self.error_count_dict[product][website_name]+=1
        except:
            print("Add error exception")

    async def run_notifications(self,website_name,product,method):
        if self.last_website_notifications == website_name+product:#checks whether already notified about availabilty
            self.last_website_notifications = None
            print(f"Already notified about {website_name}")
            await asyncio.sleep(30)
            
        else:
            Notifications = self.bot.get_cog('Notifications')
            await Notifications.notify(website_name=website_name,product=product,method=method)
            self.last_website_notifications=website_name+product#makes the last_website that has been notified about this one


    #Discord bot command
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command(name="RunCount",aliases=["rc"], help=f'Shows how many times the StockChecker has ran successfully. \n{config.prefix}runcount')
    async def runcount(self,ctx):
        embed=discord.Embed(Title="Run Count",description="Showing number of times StockChecker has run succesfully on each site.",colour=0x0000FF)
        embed.add_field(name="Amazon",value=f"""\u2800{config.PS5_emoji}  **PS5**:\n\u2800\u2800{self.count_dict['PS5']['amazon']} times. \n\u2800\u2800Errored out: {self.error_count_dict['PS5']['amazon']} times.\n\u2800{config.PS5_emoji}  **PS5 DE**:\n\u2800\u2800{self.count_dict['PS5_DE']['amazon']} times. \n\u2800\u2800Errored out: {self.error_count_dict['PS5_DE']['amazon']} times.\n\u2800{config.XSX_emoji}  **XSX**:\n\u2800\u2800{self.count_dict['XSX']['amazon']} times. \n\u2800\u2800Errored out: {self.error_count_dict['XSX']['amazon']} times. \n\u2800{config.XSS_emoji}  **XSS**:\n\u2800\u2800{self.count_dict['XSS']['amazon']} times. \n\u2800\u2800Errored out: {self.error_count_dict['XSS']['amazon']} times.""",inline=False)
        embed.add_field(name="Flipkart",value=f"""\u2800{config.PS5_emoji}  **PS5**:\n\u2800\u2800{self.count_dict['PS5']['flipkart']} times. \n\u2800\u2800Errored out: {self.error_count_dict['PS5']['flipkart']} times.\n\u2800{config.PS5_emoji}  **PS5 DE**:\n\u2800\u2800{self.count_dict['PS5_DE']['flipkart']} times. \n\u2800\u2800Errored out: {self.error_count_dict['PS5_DE']['flipkart']} times.\n\u2800{config.XSX_emoji}  **XSX**:\n\u2800\u2800{self.count_dict['XSX']['flipkart']} times. \n\u2800\u2800Errored out: {self.error_count_dict['XSX']['flipkart']} times. \n\u2800{config.XSS_emoji}  **XSS**:\n\u2800\u2800{self.count_dict['XSS']['flipkart']} times. \n\u2800\u2800Errored out: {self.error_count_dict['XSS']['flipkart']} times.""",inline=False)
        embed.add_field(name="ShopAtSC",value=f"""\u2800{config.PS5_emoji}  **PS5**:\n\u2800\u2800{self.count_dict['PS5']['shopatsc']} times. \n\u2800\u2800Errored out: {self.error_count_dict['PS5']['shopatsc']} times.\n\u2800{config.PS5_emoji}  **PS5 DE**:\n\u2800\u2800{self.count_dict['PS5_DE']['shopatsc']} times. \n\u2800\u2800Errored out: {self.error_count_dict['PS5_DE']['shopatsc']} times.""",inline=False)
        embed.add_field(name="Games the Shop",value=f"""\u2800{config.PS5_emoji}  **PS5**:\n\u2800\u2800{self.count_dict['PS5']['games_the_shop']} times. \n\u2800\u2800Errored out: {self.error_count_dict['PS5']['games_the_shop']} times.""",inline=False)
        embed.add_field(name="Prepaid Gamer Card",value=f"""\u2800{config.PS5_emoji}  **PS5**:\n\u2800\u2800{self.count_dict['PS5']['ppgc']} times. \n\u2800\u2800Errored out: {self.error_count_dict['PS5']['ppgc']} times.""",inline=False)
        await ctx.send(embed=embed)

    
   
    
    async def startup(self): 
        await self.bot.wait_until_ready()   
        self.bot.loop.create_task(self.scrape_amazon(amazon_link=All_Websites["amazon"].PS5_link,product="PS5")) 
        self.bot.loop.create_task(self.scrape_amazon(amazon_link=All_Websites["amazon"].PS5_DE_link,product="PS5_DE")) 
        self.bot.loop.create_task(self.scrape_amazon(amazon_link=All_Websites["amazon"].XSX_link,product="XSX"))
        self.bot.loop.create_task(self.scrape_amazon(amazon_link=All_Websites["amazon"].XSS_link,product="XSS"))

        self.bot.loop.create_task(self.scrape_flipkart(flipkart_link=All_Websites["flipkart"].PS5_link,product="PS5"))
        self.bot.loop.create_task(self.scrape_flipkart(flipkart_link=All_Websites["flipkart"].PS5_DE_link,product="PS5_DE"))
        self.bot.loop.create_task(self.scrape_flipkart(flipkart_link=All_Websites["flipkart"].XSX_link,product="XSX"))
        self.bot.loop.create_task(self.scrape_flipkart(flipkart_link=All_Websites["flipkart"].XSS_link,product="XSS"))

        self.bot.loop.create_task(self.scrape_shopatsc(shopatsc_link=All_Websites["shopatsc"].PS5_link,product="PS5"))
        self.bot.loop.create_task(self.scrape_shopatsc(shopatsc_link=All_Websites["shopatsc"].PS5_DE_link,product="PS5_DE"))

        self.bot.loop.create_task(self.scrape_games_the_shop(games_the_shop_link=All_Websites["games_the_shop"].PS5_link,product="PS5"))
        self.bot.loop.create_task(self.scrape_ppgc(ppgc_link=All_Websites["ppgc"].PS5_link,product="PS5"))
        

    #async def get_page_html(self,link,headers_list=[{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}]):
    async def get_page_html(self,link,headers_list=[{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"},{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"},{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36"},{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36"}]):
        ordered_headers_list = []
        for headers in headers_list:
            h = OrderedDict()
            for header,value in headers.items():
                h[header]=value
                ordered_headers_list.append(h)
        headers = random.choice(headers_list)
        async with aiohttp.ClientSession(headers=headers,trust_env=True) as session:
            async with session.get(url=link) as response:
                html = await response.text()
                return html

    
    async def scrape_amazon(self,amazon_link,product):
        #print("amazon",product)
        #these are a list of headers that makes  amazon to think that the requests are coming from real users
        headers_list = [{       
            'sec-ch-ua': '^\\^',
            'Accept': 'application/json',
            'DNT': '1',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
            'Content-Type': 'application/json',
            'Origin': 'https://www.amazon.in',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://www.amazon.in/',
            'Accept-Language': 'en-IN,en;q=0.9',
            },      
            {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/json',
            'Origin': 'https://www.amazon.in/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://www.amazon.in/',
            },
            {
            'authority': 'www.amazon.in',
            'dnt': '1',
            'rtt': '200',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
            'accept': 'text/html,/',
            'ect': '4g',
            'sec-ch-ua': '^^',
            'origin': 'https://www.amazon.in/',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.amazon.in/',
            'accept-language': 'en-US,en;q=0.9',
           
            },
            {
            'Connection': 'keep-alive',
            'sec-ch-ua': '^^',
            'Accept': 'application/json, text/javascript, /; q=0.01',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
            'Origin': 'https://www.amazon.in/',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://www.amazon.in/',
            'Accept-Language': 'en-GB,en;q=0.9',
            },
            {
            'authority': 'www.amazon.in',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
            'content-type': 'application/x-www-form-urlencoded',
            'accept': 'text/html,*/*',
            'ect': '4g',
            'origin': 'https://www.amazon.in',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.amazon.in/dp/B08FV5GC28',
            'accept-language': 'en-US,en;q=0.9',         
            },
            {
            'sec-ch-ua': '^^',
            'Referer': 'https://www.amazon.in/',
            'sec-ch-ua-mobile': '?1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/537.36',
            }       
            ]
        while True:
            page_html = await self.get_page_html(link=amazon_link,headers_list=headers_list)
            doc = lxml.html.fromstring(str(page_html))
            try:
                stock=doc.xpath('//*[@id="availability"]/span')#Fetches Stock element
                add_to_cart_button=doc.xpath('//*[@id="add-to-cart-button"]')#Fetches the Add to Cart Button
                all_buying_options=doc.xpath('//*[@id="buybox-see-all-buying-choices"]/span/a')#Fetches the button with All Buying Options
                pre_order_button=doc.xpath('//*[@id="buy-now-button"]')#Fetches Pre Order button
            except:
                print("Amazon Error")
                self.add_error(website_name="amazon",product=product)
                await asyncio.sleep(15)
                continue
            
            if len(stock) > 0:
                stock=stock[0].text
            else:
                continue
            
            if "Currently unavailable." in stock or "We don't know when or if this item will be back in stock." in stock:
                status="Out of Stock"
            
            elif "In stock" in stock:
                status="In Stock"
                await self.run_notifications(website_name="amazon",product=product,method="In stock throught availabilty element")                 
            
            # elif "This item will be released on" in stock:
            #     status="In Stock"
            #     #print("This item will be released on")
            #     await self.run_notifications(website_name="amazon",method="This item will be released on")

            elif len(add_to_cart_button) != 0: 
                status="In Stock"
                await self.run_notifications(website_name="amazon",product=product,method="Add to Cart button")

            elif len(all_buying_options) != 0:
                status="In Stock"
                await self.run_notifications(website_name="amazon",product=product,method="All buying options button")

            elif len(pre_order_button) != 0:
                status="In Stock"
                await self.run_notifications(website_name="amazon",product=product,method="Pre Order Now button")
            
            else:
                status=f"Amazon: A different response has been generated: {stock}"
            
            self.add_count(website_name="amazon",product=product)
            await asyncio.sleep(15)

    async def scrape_flipkart(self,flipkart_link,product):
        # headers_list = [{
        #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        #         'Accept': '*/*',
        #         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        #         'origin': 'https://www.flipkart.com',
        #         'referer': 'https://www.flipkart.com/',
        #         'accept-language': 'en-IN,en;q=0.9',
        #         'Referer': 'https://www.flipkart.com/',
        #         }, 
        #         {
        #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 Edg/91.0.864.54',
        #         'Accept-Language': 'en-US,en;q=0.9',
        #         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 Edg/91.0.864.54',
        #         'accept': '*/*',
        #         'referer': 'https://www.flipkart.com/',
        #         'accept-language': 'en-US,en;q=0.9',
        #         'origin': 'https://www.flipkart.com',
        #         'Cache-Control': 'max-age=0',
        #         'Service-Worker': 'script',
        #         },
        #         {
        #         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9",
        #         "Accept-Encoding": "gzip, deflate, br",
        #         "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
        #         "Upgrade-Insecure-Requests": "1",
        #         'referer': 'https://www.flipkart.com/',
        #         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 Edg/91.0.864.54",
        #         'origin': 'https://www.flipkart.com',
        #         } ,
        #         {
        #         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9", 
        #         "Accept-Encoding": "gzip, deflate, br", 
        #         "Accept-Language": "en-US,en;q=0.9",  
        #         'origin': 'https://www.flipkart.com',
        #         'referer': 'https://www.flipkart.com/',
        #         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36", 
        #         }
        #         ]


        while True:
            page_html = await self.get_page_html(flipkart_link)
            soup = BeautifulSoup(str(page_html), 'html.parser')
            try:
                notify_me_button=soup.find('button', class_ = '_2KpZ6l _2uS5ZX _2Dfasx').text#notify me button
            except:
                try:
                    add_to_cart_button=soup.find('button', class_ = '_2KpZ6l _2U9uOA _3v1-ww').text#add to cart
                    buy_now_button=soup.find('button', class_ = '_2KpZ6l _2U9uOA ihZ75k _3AWRsL').text#buy now/preorder now
                    
                    if add_to_cart_button in [' ADD TO CART']:
                        await self.run_notifications(website_name="flipkart",product=product,method="Add to Cart button")

                    elif buy_now_button in [' BUY NOW',' PROCEED TO BUY',' ORDER IT',' PREORDER NOW',' PRE ORDER']:
                        await self.run_notifications(website_name="flipkart",product=product,method="Pre Order Now/ Buy Now button")
                        
                    else: 
                        for x in ['NOW','BUY','ORDER',]:
                            if x in buy_now_button:
                                await self.run_notifications(website_name="flipkart",product=product,method="Buy Now/ Pre Order Now has 'NOW','BUY','ORDER' in it.")

                except:
                    print("Flipkart Error")
                    self.add_error(product=product,website_name="flipkart")
                    await asyncio.sleep(15)
                    continue
           
            self.add_count(product=product,website_name="flipkart")
            await asyncio.sleep(15)
        
        # while True:
        #     page_html =await self.get_page_html(link=flipkart_link)
        #     doc = lxml.html.fromstring(str(page_html))
        #     try:
        #         sold_out_element=doc.xpath('//*[@id="container"]/div/div[3]/div[1]/div[2]/div[3]/div')[0].text
        #         sold_out_sentence=doc.xpath('//*[@id="container"]/div/div[3]/div[1]/div[2]/div[3]/div[2]')[0].text
        #         add_to_cart_button=doc.xpath('//*[@id="container"]/div/div[3]/div[1]/div[1]/div[2]/div/ul/li[1]/button')
        #         buy_now_button=doc.xpath('//*[@id="container"]/div/div[3]/div[1]/div[1]/div[2]/div/ul/li[2]/form/button')
        #     except:
        #         print("Flipkart Error")
        #         self.add_error(product=product,website_name="flipkart")
        #         await asyncio.sleep(15)
        #         continue
            
        #     if len(add_to_cart_button) !=0 :
        #         await self.run_notifications(website_name="flipkart",product=product,method="Add to Cart button")
            
        #     elif len(buy_now_button) !=0:
        #         await self.run_notifications(website_name="flipkart",product=product,method="Pre Order Now/ Buy Now button")
            
        #     # elif sold_out_element is None and sold_out_sentence is None:
        #     #     await self.run_notifications(website_name="flipkart",product=product,method="\"Sold out\" is not shown. \n This method may result in false positive's. Contact the mod's if it is so.")

        #     else:
        #         pass

    async def scrape_shopatsc(self,shopatsc_link,product):
        while True:
            page_html = await self.get_page_html(link=shopatsc_link)
            soup = BeautifulSoup(page_html, 'html.parser')
            try:
                notify_me_button = soup.find(id='notify_btn_div')
            except:
                print("ShopAtSC Error")
                self.add_error(product=product,website_name="shopatsc")
                await asyncio.sleep(15)
                continue
            
            if notify_me_button is None:
                pass
            else:
                notify_me_button_style = notify_me_button.get('style')
                if notify_me_button_style is None:
                    pass
                else:
                    text_match = re.search('display:none;',notify_me_button_style, re.IGNORECASE)
                    print(text_match)
                    if text_match is not None:
                        await self.run_notifications(website_name="shopatsc",product=product,method="Notify Me button is not visible.")

            self.add_count(product=product,website_name="shopatsc")
            await asyncio.sleep(15)

    async def scrape_games_the_shop(self,games_the_shop_link,product):
        while True:
            page_html = await self.get_page_html(link=games_the_shop_link)
            doc = lxml.html.fromstring(page_html)
            try:
                stock=doc.xpath('//*[@id="ctl00_ContentPlaceHolder1_divOfferDetails"]/div/div[2]/div/div[2]/div[1]/text()')
            except:
                print("Games the Shop Error")
                self.add_error(product=product,website_name="games_the_shop")
                await asyncio.sleep(15)
                continue
        
            if " ADD TO CART" in stock:
                await self.run_notifications(website_name="games_the_shop",product=product,method="Add to Cart button")

            elif len(stock) == 0:
                pass

            else:
                status=f"Games the Shop: A different response has been generated: {stock}"               
            

            self.add_count(product=product,website_name="games_the_shop")
            await asyncio.sleep(15)

    async def scrape_ppgc(self,ppgc_link,product):
        while True:
            page_html = await self.get_page_html(link=ppgc_link)
            doc = lxml.html.fromstring(page_html)
            try:
                stock=doc.xpath('//*[@id="product-7990"]/div/div[1]/div/div[2]/form/button/text()')#[0].strip()
            except:
                print("Prepaid Gamer Card Error")
                self.add_error(product=product,website_name="ppgc")
                await asyncio.sleep(15)
                continue
        
            if "Add to cart" in stock:
                status="In Stock"
                await self.run_notifications(website_name="ppgc",product=product,method="Add to Cart Button")

            elif len(stock) == 0:
                pass

            else:
                status=f"Prepaid Gamer Card: A different response has been generated: {stock}"                
            

            self.add_count(product=product,website_name="ppgc")
            await asyncio.sleep(15)
  


def setup(bot):
    bot.add_cog(StockChecker(bot))