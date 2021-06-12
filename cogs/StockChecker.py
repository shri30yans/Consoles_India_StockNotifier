import discord,random,asyncio,requests,time
from discord.ext import commands,tasks
import lxml.html
import config
from utils.links import All_Websites
from collections import OrderedDict


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
        self.count={"amazon":0,"flipkart":0,"games_the_shop":0,"ppgc":0}
        self.error_count={"amazon":0,"flipkart":0,"games_the_shop":0,"ppgc":0}
        self.last_website_notifications=None



    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command(name="RunCount", help=f'Shows how many times the StockChecker has ran successfully. \n{config.prefix}runcount')
    async def runcount(self,ctx):
        embed=discord.Embed(Title="Run Count",description="Showing number of times StockChecker has run succesfully on each site.",colour=0x0000FF)
        embed.add_field(name="Amazon",value=f"{self.count['amazon']} times. \nErrored out: {self.error_count['amazon']} times.",inline=False)
        embed.add_field(name="Flipkart",value=f"{self.count['flipkart']} times. \nErrored out: {self.error_count['flipkart']} times.",inline=False)
        embed.add_field(name="Games the Shop",value=f"{self.count['games_the_shop']} times. \nErrored out: {self.error_count['games_the_shop']} times.",inline=False)
        embed.add_field(name="Prepaid Gamer Card",value=f"{self.count['ppgc']} times. \nErrored out: {self.error_count['ppgc']} times.",inline=False)
        await ctx.send(embed=embed)

    async def run_notifications(self,website_name,method):
        if self.last_website_notifications == website_name:#checks whether already notified about availabilty
            self.last_website_notifications = None
            print(f"Already notified about {website_name}")
            await asyncio.sleep(30)
            
        else:
            Notifications = self.bot.get_cog('Notifications')
            await Notifications.notify(website_name,method)
            self.last_website_notifications=website_name#makes the last_website that has been notified about this one
   
    
    async def startup(self): 
        await self.bot.wait_until_ready()   
        self.bot.loop.create_task(self.scrape_flipkart(flipkart_link=All_Websites["flipkart"].PS5_link) )
        self.bot.loop.create_task(self.scrape_amazon(amazon_link=All_Websites["amazon"].PS5_link))    
        self.bot.loop.create_task(self.scrape_games_the_shop(games_the_shop_link=All_Websites["games_the_shop"].PS5_link))
        self.bot.loop.create_task(self.scrape_ppgc(ppgc_link=All_Websites["ppgc"].PS5_link))
        

    async def get_page_html(self,url,headers_list=[{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}]):
        ordered_headers_list = []
        for headers in headers_list:
            h = OrderedDict()
            for header,value in headers.items():
                h[header]=value
                ordered_headers_list.append(h)
        headers = random.choice(headers_list)

        page = requests.get(url, headers=headers)
        return page.content

    
    async def scrape_amazon(self,amazon_link):
        #these are a list of headers that makes  amazon to think that the requests are coming from real users
        headers_list = [{
            'Connection': 'keep-alive',
            'sec-ch-ua': '^\\^',
            'Accept': 'application/json',
            'DNT': '1',
            'X-Requested-With': 'XMLHttpRequest',
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
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'Origin': 'https://www.amazon.in/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://www.amazon.in/',
            },
            {
            'authority': 'www.amazon.in',
            'x-kl-ajax-request': 'Ajax_Request',
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
            'sec-ch-ua': '^\\^',
            'rtt': '50',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
            'content-type': 'application/x-www-form-urlencoded',
            'accept': 'text/html,*/*',
            'x-requested-with': 'XMLHttpRequest',
            'downlink': '10',
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
            page_html = await self.get_page_html(amazon_link,headers_list)
            doc = lxml.html.fromstring(str(page_html))
            try:
                stock=doc.xpath('//*[@id="availability"]/span')[0].text#Fetches Stock element
                add_to_cart_button=doc.xpath('//*[@id="add-to-cart-button"]')#Fetches the Add to Cart Button
                all_buying_options=doc.xpath('//*[@id="buybox-see-all-buying-choices"]/span/a')#Fetches the button with All Buying Options
                pre_order_button=doc.xpath('//*[@id="buy-now-button"]')#Fetches Pre Order button
            except:
                print("Amazon Error")
                status="error"
                self.error_count["amazon"]+=1
                await asyncio.sleep(5)
                continue
            #print(stock)
            if "Currently unavailable." in stock or "We don't know when or if this item will be back in stock." in stock:
                status="Out of Stock"
            
            elif "In stock" in stock:
                status="In Stock"
                #print("In stock in availability")
                await self.run_notifications(website_name="amazon",method="In stock throught availabilty element")                 
            
            # elif "This item will be released on" in stock:
            #     status="In Stock"
            #     #print("This item will be released on")
            #     await self.run_notifications(website_name="amazon",method="This item will be released on")

            elif len(add_to_cart_button) != 0: 
                status="In Stock"
                await self.run_notifications(website_name="amazon",method="Add to Cart button")

            elif len(all_buying_options) != 0:
                status="In Stock"
                await self.run_notifications(website_name="amazon",method="All buying options button")

            elif len(pre_order_button) != 0:
                status="In Stock"
                await self.run_notifications(website_name="amazon",method="Pre Order Now button")
            
            else:
                status=f"Amazon: A different response has been generated: {stock}"
            

            self.count["amazon"]+=1
            await asyncio.sleep(5)
            #print(status)

    async def scrape_flipkart(self,flipkart_link):
        while True:
            page_html =await self.get_page_html(flipkart_link)
            doc = lxml.html.fromstring(str(page_html))
            try:
                stock=doc.xpath('//*[@id="container"]/div/div[3]/div[1]/div[2]/div[3]/div')[0].text
                add_to_cart_button=doc.xpath('//*[@id="container"]/div/div[3]/div[1]/div[1]/div[2]/div/ul/li[1]/button')
            except:
                #print(page_html)
                print("Flipkart Error")
                status="error"
                self.error_count["flipkart"]+=1
                await asyncio.sleep(5)
                continue
            # print(stock)
            # print(add_to_cart_button)
            #stock will show Currently Unavailable when no stock is there
            #Flipkart shows no value for availabilty when an item is Out of Stock.
            #This checks if the Availabilty value is None and the Add to Cart Button Exists
            if stock is None and len(add_to_cart_button) !=0 :
                status="In Stock"
                await self.run_notifications(website_name="flipkart",method="Add to Cart exists and Stock element is not shown")

            elif stock is None:
                #No value was retrived, but Add to Cart button doesn't exist
                pass

            elif "Sold Out" in stock or "Coming Soon" in stock :
                status="Out of Stock"

            else:
                status=f"Flipkart: A different response has been generated: {stock}"
            

            self.count["flipkart"]+=1
            await asyncio.sleep(5)
            #print(status)

    async def scrape_games_the_shop(self,games_the_shop_link):
        while True:
            page_html = await self.get_page_html(games_the_shop_link)
            doc = lxml.html.fromstring(page_html)
            try:
                stock=doc.xpath('//*[@id="ctl00_ContentPlaceHolder1_divOfferDetails"]/div/div[2]/div/div[2]/div[1]/text()')
                #print(stock)
            except:
                print("Games the Shop Error")
                status="error"
                self.error_count["games_the_shop"]+=1
                await asyncio.sleep(5)
                continue
        
            if " ADD TO CART" in stock:
                status="In Stock"
                await self.run_notifications(website_name="games_the_shop",method="Add to Cart button")

            elif len(stock) == 0:
                status="Out of Stock"

            else:
                status=f"Games the Shop: A different response has been generated: {stock}"               
            

            self.count["games_the_shop"]+=1
            await asyncio.sleep(2)
            #print(status)
    

    async def scrape_ppgc(self,ppgc_link):
        while True:
            page_html = await self.get_page_html(ppgc_link)
            doc = lxml.html.fromstring(page_html)
            try:
                stock=doc.xpath('//*[@id="product-7990"]/div/div[1]/div/div[2]/form/button/text()')#[0].strip()
                #print(stock)
            except:
                print("Prepaid Gamer Card Error")
                status="error"
                self.error_count["ppgc"]+=1
                await asyncio.sleep(5)
                continue
        
            if "Add to cart" in stock:
                status="In Stock"
                await self.run_notifications(website_name="ppgc",method="Add to Cart Button")

            elif len(stock) == 0:
                status="Out of Stock"

            else:
                status=f"Prepaid Gamer Card: A different response has been generated: {stock}"                
            

            self.count["ppgc"]+=1
            await asyncio.sleep(2)
                        #print(status)
  


def setup(bot):
    bot.add_cog(StockChecker(bot))