import asyncio,logging,pytz,re,lxml.html
from discord.ext import commands
from StockChecker.ScrapperConfig import All_Websites,notifications_delay
from bs4 import BeautifulSoup
from datetime import datetime
from io import BytesIO
from datetime import datetime
import config

# Gets or creates a logger
logger = logging.getLogger(__name__)  

# define file handler and set formatter
file_handler = logging.FileHandler('logs/StockChecker.log')
formatter    = logging.Formatter(f"{datetime.now(tz=pytz.timezone('Asia/Kolkata'))} : %(levelname)s : %(name)s : %(message)s")#logs in Indian Standard Time
file_handler.setFormatter(formatter)
# add file handler to logger
logger.addHandler(file_handler)

# How the bot checks for Stock availability?
# The bot uses Playwright to replicate a browser experience to fetch the HTML code of a URL. The bot then uses another library to scour the HTML code to and looks for certain keywords in a specified location.
# Logic:
# Amazon: Amazon has a seperate divison in it's HTML page called Availabilty which allows me to check if a product is "Currently unavailable." or "In Stock"
# Flipkart: Flipkart has a seperate element to display Out of Stock. In case the product is available that element gives no value. The bot checks if that element is not displayed and double checks if the Add to Cart Button Exists.
# ShopatSC: The Notify button has a property that makes it invisble if stock is present
# Games the Shop: Games the Shop shows the Add to Cart Button when the product is available.
# Prepaid Gamer Card: Prepaid Gamer Card shows the Add to Cart Button when the product is available.



class Scrapper(commands.Cog): 
    def __init__(self, bot):
        self.bot = bot
        self.last_notified={   
                            "PS5":{"amazon":None,"flipkart":None,"games_the_shop":None,"ppgc":None,"shopatsc":None},
                            "PS5_DE":{"amazon":None,"flipkart":None,"games_the_shop":None,"ppgc":None,"shopatsc":None},
                            "XSX":{"amazon":None,"flipkart":None},
                            "XSS":{"amazon":None,"flipkart":None},
                            "RED_DS":{"amazon":None,"shopatsc":None},
                            "BLACK_DS":{"amazon":None,"shopatsc":None}}

        


    async def run_notifications(self,website_name,product,method,page=None):
        Notifications = self.bot.get_cog('Notifications')
        default_notification_delay = 30
        notification_delay = notifications_delay.get(product) or default_notification_delay
        timestamp = self.last_notified[product][website_name] 
        
        if timestamp is None:
            last_notified = float("Infinity") 
        else:
            last_notified= (datetime.now()-timestamp).total_seconds()
        
        if  last_notified < notification_delay:
            '''If a product is notified before 'notifcation_delay' later. '''
            logger.info(f'Already notified {product} stock in {website_name}')
            #await asyncio.sleep(30)
            return
        elif page is None:
            self.last_notified[product][website_name] = datetime.now()
            await Notifications.notify(website_name=website_name,product=product,method=method)
        else:
            self.last_notified[product][website_name] = datetime.now()
            screenshot_bytes = await page.screenshot()
            image = BytesIO(screenshot_bytes)
            await Notifications.notify(website_name=website_name,product=product,method=method,image=image)
        
        logger.info(f'Notified for {product} stock in {website_name}')


        
    async def scrape_amazon_wishlist(self,page_html,page = None):
        soup = BeautifulSoup(page_html, 'html.parser')
        wishlist_products = All_Websites["amazon"].wishlist_products

        #Method 1: Checks for Add to Cart button
        for item in list(wishlist_products):
            obj = wishlist_products[item]
            async def add_to_cart_button_check():
                cart_regex = re.compile('add_to_cart')
                id_regex = re.compile(obj.item_id)
                all_span_elements= soup.find_all("span", {"class" : cart_regex,"id": id_regex})
                if len(all_span_elements) > 0:
                    await self.run_notifications(website_name="amazon",product=item,method="Wishlist",page=page)
            await add_to_cart_button_check()
        #Method 2: Check list elements/ Whole product listing for prices
        # all_list_elements=soup.find_all('li')
        # if len(all_list_elements) > 0:
        #     for elem in all_list_elements:
        #         for item in list(wishlist_products):
                    
        #             #If the list element has a price
        #             if elem.has_attr("data-price"):
        #                 obj = wishlist_products[item]
                        
        #                 async def check_price():
        #                     '''To check if price is in a certain in range.
        #                     If the price is "-Infinity" it means the product is out of stock.'''
        #                     if float(elem["data-price"]) <= obj.max_cost and float(elem["data-price"]) > 0:
        #                         await self.run_notifications(website_name="amazon",product=item,method="Wishlist",page=page)

        #                 if elem.has_attr("data-itemid"):
        #                     if obj.item_id in elem["data-itemid"]:
        #                         await check_price()

        #                 elif elem.has_attr("id"):
        #                     if obj.item_id in elem["id"]:
        #                         return "pause"
        #                         #await check_price()
                        
        #                 else:
        #                     logger.error(f'Amazon Error Wishlist: Both attributes do not exist.')
                        
        # else:
        #     return False
        
        return True

    
    async def scrape_amazon(self,page_html,product,page = None):        
        doc = lxml.html.fromstring(str(page_html))
        try:
            stock=doc.xpath('//*[@id="availability"]/span')#Fetches Stock element
            add_to_cart_button=doc.xpath('//*[@id="add-to-cart-button"]')#Fetches the Add to Cart Button
            pre_order_button=doc.xpath('//*[@id="buy-now-button"]')#Fetches Pre Order button
        except:
            return False
        
        #checks if the availabilty element shows anything, if there are no elements pass
        if len(stock) > 0:
            stock=stock[0].text
            if "Currently unavailable" in stock or "We don't know when or if this item will be back in stock." in stock:
                pass
            
            elif "In stock" in stock:
                await self.run_notifications(website_name="amazon",product=product,method="In stock throught availabilty element",page=page)                 
            

            elif len(add_to_cart_button) != 0: 
                await self.run_notifications(website_name="amazon",product=product,method="Add to Cart button",page=page)


            elif len(pre_order_button) != 0:
                await self.run_notifications(website_name="amazon",product=product,method="Pre Order Now button",page=page)
            
            else:
                print(f"Amazon: A different response has been generated: {stock}")
        return True


    async def scrape_flipkart(self,page_html,product,page=None):
        soup = BeautifulSoup(str(page_html), 'html.parser')
        try:
            notify_me_button=soup.find('button', class_ = '_2KpZ6l _2uS5ZX _2Dfasx').text#notify me button
        except:
            try:
                add_to_cart_button=soup.find('button', class_ = '_2KpZ6l _2U9uOA _3v1-ww').text#add to cart
                buy_now_button=soup.find('button', class_ = '_2KpZ6l _2U9uOA ihZ75k _3AWRsL').text#buy now/preorder now
                
                if add_to_cart_button in [' ADD TO CART']:
                    await self.run_notifications(website_name="flipkart",product=product,method="Add to Cart button",page=page)

                elif buy_now_button in [' BUY NOW',' PROCEED TO BUY',' ORDER IT',' PREORDER NOW',' PRE ORDER']:
                    await self.run_notifications(website_name="flipkart",product=product,method="Pre Order Now/ Buy Now button",page=page)
                    
                else: 
                    for x in ['NOW','BUY','ORDER',]:
                        if x in buy_now_button:
                            await self.run_notifications(website_name="flipkart",product=product,method="Buy Now/ Pre Order Now has 'NOW','BUY','ORDER' in it.",page=page)

            except:
                return False
        
        return True

    async def scrape_shopatsc(self,page_html,product,page=None):
        soup = BeautifulSoup(page_html, 'html.parser')
        try:
            pincode_input_element = soup.find(class_="checker-combine")
        except:
           return False
        
        if pincode_input_element is not None:
            await self.run_notifications(website_name="shopatsc",product=product,method="Enter PINCODE element is not available.",page=page)

        return True

    async def scrape_games_the_shop(self,page_html,product,page=None):
        doc = lxml.html.fromstring(page_html)
        try:
            stock=doc.xpath('//*[@id="ctl00_ContentPlaceHolder1_divOfferDetails"]/div/div[2]/div/div[2]/div[1]/text()')
        except:
            return False
        
        if " ADD TO CART" in stock:
            await self.run_notifications(website_name="games_the_shop",product=product,method="Add to Cart button",page=page)

        # elif len(stock) == 0:
        #     pass

        # else:
        #     pass
        
        return True

    async def scrape_ppgc(self,page_html,product,page=None):
        doc = lxml.html.fromstring(page_html)
        try:
            stock=doc.xpath('//*[@id="product-7990"]/div/div[1]/div/div[2]/form/button/text()')#[0].strip()
        except:
           return False
        
        if "Add to cart" in stock:
            await self.run_notifications(website_name="ppgc",product=product,method="Add to Cart Button",page=page)

        # elif len(stock) == 0:
        #     pass

            #print(f"Prepaid Gamer Card: A different response has been generated: {stock}"   )             
        

        return True
  


def setup(bot):
    bot.add_cog(Scrapper(bot))
