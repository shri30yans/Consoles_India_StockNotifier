import discord,random,asyncio,requests,time
from discord.ext import commands,tasks
import lxml.html
import config
from links import All_Websites

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

    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command(name="RunCount", help=f'Shows how many times the StockChecker has ran successfully. \n{config.prefix}runcount')
    async def runcount(self,ctx):
        embed=discord.Embed(Title="Run Count",description="Showing number of times StockChecker has run on each site.",colour=0x0000FF)
        embed.add_field(name="Amazon",value=f"{self.count['amazon']} times.",inline=False)
        embed.add_field(name="Flipkart",value=f"{self.count['flipkart']} times.",inline=False)
        embed.add_field(name="Games the Shop",value=f"{self.count['games_the_shop']} times.",inline=False)
        embed.add_field(name="Prepaid Gamer Card",value=f"{self.count['ppgc']} times.",inline=False)
        await ctx.send(embed=embed)

    

    
    async def run_notifications(self,website_name):
        Notifications = self.bot.get_cog('Notifications')
        await Notifications.notify(website_name)
   
    
    async def startup(self): 
        await self.bot.wait_until_ready()   
        self.bot.loop.create_task(self.scrape_flipkart(flipkart_link=All_Websites["flipkart"].link) )
        self.bot.loop.create_task(self.scrape_amazon(amazon_link=All_Websites["amazon"].link))    
        self.bot.loop.create_task(self.scrape_games_the_shop(games_the_shop_link=All_Websites["games_the_shop"].link))
        self.bot.loop.create_task(self.scrape_ppgc(ppgc_link=All_Websites["ppgc"].link))
        

    async def get_page_html(self,url):
        headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}
        page = requests.get(url, headers=headers)
        #print(page.status_code)
        return page.content
    
    async def scrape_amazon(self,amazon_link):
        while True:
            page_html = await self.get_page_html(amazon_link)
            doc = lxml.html.fromstring(page_html)
            try:
                stock=doc.xpath('//*[@id="availability"]/span')[0].text
            except:
                stock="Amazon Error"
            #print(stock)
            if "Currently unavailable." in stock or "We don't know when or if this item will be back in stock." in stock :
                status="Out of Stock"
            elif "In stock" in stock:
                status="In Stock"
                await self.run_notifications(website_name="amazon")
            else:
                status=f"A different response has been generated: {stock}"
            await asyncio.sleep(5)
            self.count["amazon"]+=1
            #print(status)

    async def scrape_flipkart(self,flipkart_link):
        while True:
            page_html = await self.get_page_html(flipkart_link)
            doc = lxml.html.fromstring(page_html)
            try:
                stock=doc.xpath('//*[@id="container"]/div/div[3]/div[1]/div[2]/div[3]/div')[0].text
                add_to_cart_button=doc.xpath('//*[@id="container"]/div/div[3]/div[1]/div[1]/div[2]/div/ul/li[1]/button')
            except:
                print("Flipkart Error")
            #print(stock)
            #print(add_to_cart_button)
            if stock is None and len(add_to_cart_button) !=0 :
                status="In Stock"
                await self.run_notifications(website_name="flipkart")

            if stock is None:
                #No value was retrived, but Add to Cart button doesn't exist
                pass

            elif "Sold Out" in stock or "Coming Soon" in stock :
                status="Out of Stock"

            else:
                status=f"A different response has been generated: {stock}"
            await asyncio.sleep(2)
            self.count["flipkart"]+=1
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
        
            if " ADD TO CART" in stock:
                status="In Stock"
                await self.run_notifications(website_name="games_the_shop")

            elif len(stock) == 0:
                status="Out of Stock"

            else:
                status=f"A different response has been generated: {stock}"               
            await asyncio.sleep(2)
            self.count["games_the_shop"]+=1
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
        
            if "Add to cart" in stock:
                status="In Stock"
                await self.run_notifications(website_name="ppgc")

            elif len(stock) == 0:
                status="Out of Stock"

            else:
                status=f"A different response has been generated: {stock}"
                
            await asyncio.sleep(2)
            #print(status)
            self.count["ppgc"]+=1

    
            




def setup(bot):
    bot.add_cog(StockChecker(bot))