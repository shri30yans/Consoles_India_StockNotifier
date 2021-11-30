import re
import logging
import pytz
import lxml.html
from bs4 import BeautifulSoup
from datetime import datetime
from io import BytesIO
from discord.ext import commands
from StockChecker.ScrapperConfig import All_Websites


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
        self.countinous_stock = {}

    async def get_countinous_stock(self, product, website_name):
        product_value = self.countinous_stock.get(product)
        if product_value is None:
            self.countinous_stock[product] = {}
            self.countinous_stock[product][website_name] = False
        else:
            count = product_value.get(website_name)
            if count is None:
                self.countinous_stock[product][website_name] = False
        return self.countinous_stock[product][website_name]

    async def change_countinous_stock(self, product, website_name, value):
        product_value = self.countinous_stock.get(product)
        if product_value is None:
            self.countinous_stock[product] = {}
            self.countinous_stock[product][website_name] = False
        else:
            count = product_value.get(website_name)
            if count is None:
                self.countinous_stock[product][website_name] = False
            else:
                self.countinous_stock[product][website_name] = value
        # print("Change stock",product,website_name,value,self.countinous_stock)

    async def run_notifications(self, website_name, product, method, page=None):
        countinous_stock = await self.get_countinous_stock(product, website_name)
        if not (countinous_stock):
            Notifications = self.bot.get_cog("Notifications")
            if page is None:
                await Notifications.notify(
                    website_name=website_name, product=product, method=method
                )
            else:
                screenshot_bytes = await page.screenshot()
                image = BytesIO(screenshot_bytes)
                await Notifications.notify(
                    website_name=website_name,
                    product=product,
                    method=method,
                    image=image,
                )
            logger.info(f"Notified for {product} stock in {website_name}")
        await self.change_countinous_stock(product, website_name=website_name, value=True)

    async def scrape_amazon_wishlist(
        self, page_html, product_name=None, page=None
    ):
        #print(product_name)
        soup = BeautifulSoup(page_html, "html.parser")
        wishlist_products = All_Websites["amazon"].wishlist_products
        for item in list(wishlist_products.values()):
            ASIN_regex = re.compile(item.ASIN)
            all_list_elements=soup.find_all('li',{"data-reposition-action-params": ASIN_regex})
            for list_element in all_list_elements:
                add_to_cart_button = list_element.find_all("span", {"class": re.compile("add_to_cart")})
                all_buying_options_button = list_element.find_all("span", {"class" : re.compile('buying_options')})
                
                # #To cross-check if item-id is correct
                # if len(all_buying_options_button) > 0 or len(add_to_cart_button) > 0:
                #     print(item.name,"There")
                # else:
                #     pass
                #     print(item.name,"Not there")
                
                async def check_price():
                    '''To check if price is in a certain in range.
                    If the price is "-Infinity" it means the product is out of stock.'''

                    if list_element.has_attr("data-price"):
                        if item.max_cost:
                            if float(list_element["data-price"]) <= item.max_cost and float(list_element["data-price"]) > 0:
                                return True
                        else:
                            return True
                    else:
                        return True

                if len(add_to_cart_button) > 0 and await check_price():
                    await self.run_notifications(
                        website_name="amazon",
                        product=item.name,
                        method="Wishlist",
                        page=page,
                    )
                else:
                    await self.change_countinous_stock(
                        product=item.name, website_name="amazon", value=False
                )
        #print("----------------")
        
        return True
        
    async def scrape_amazon(self, page_html, product, page=None):
        doc = lxml.html.fromstring(str(page_html))
        try:
            stock = doc.xpath('//*[@id="availability"]/span')  # Fetches Stock element
            add_to_cart_button = doc.xpath('//*[@id="add-to-cart-button"]')  # Fetches the Add to Cart Button
            pre_order_button = doc.xpath('//*[@id="buy-now-button"]')  # Fetches Pre Order button
        except:
            return False

        # checks if the availabilty element shows anything, if there are no elements pass
        if len(stock) > 0:
            stock = stock[0].text
            if (
                "Currently unavailable" in stock
                or "We don't know when or if this item will be back in stock." in stock
            ):
                pass

            elif "In stock" in stock:
                await self.run_notifications(
                    website_name="amazon",
                    product=product,
                    method="In stock throught availabilty element",
                    page=page,
                )

            elif len(add_to_cart_button) != 0:
                await self.run_notifications(
                    website_name="amazon",
                    product=product,
                    method="Add to Cart button",
                    page=page,
                )

            elif len(pre_order_button) != 0:
                await self.run_notifications(
                    website_name="amazon",
                    product=product,
                    method="Pre Order Now button",
                    page=page,
                )

            else:
                await self.change_countinous_stock(
                    product, website_name="amazon", value=False
                )

                # print(f"Amazon: A different response has been generated: {stock}")
        return True

    async def scrape_flipkart(self, page_html, product, page=None):
        soup = BeautifulSoup(str(page_html), "html.parser")
        # notify me button
        notify_me_button = soup.find("button", class_="_2KpZ6l _2uS5ZX _2Dfasx")

        # If the notify me button is missing
        if notify_me_button is None:
            add_to_cart_button = soup.find(
                "button", class_="_2KpZ6l _2U9uOA _3v1-ww"
            )  # add to cart
            buy_now_button = soup.find(
                "button", class_="_2KpZ6l _2U9uOA ihZ75k _3AWRsL"
            )  # buy now/preorder now

            try:
                # Will error out if these buttons were None
                if add_to_cart_button.text in [" ADD TO CART"]:
                    await self.run_notifications(
                        website_name="flipkart",
                        product=product,
                        method="Add to Cart button",
                        page=page,
                    )

                elif buy_now_button.text in [
                    " BUY NOW",
                    " PROCEED TO BUY",
                    " ORDER IT",
                    " PREORDER NOW",
                    " PRE ORDER",
                ]:
                    await self.run_notifications(
                        website_name="flipkart",
                        product=product,
                        method="Pre Order Now/ Buy Now button",
                        page=page,
                    )

                else:
                    for x in [
                        "NOW",
                        "BUY",
                        "ORDER",
                    ]:
                        if x in buy_now_button.text:
                            await self.run_notifications(
                                website_name="flipkart",
                                product=product,
                                method="Buy Now/ Pre Order Now has 'NOW','BUY','ORDER' in it.",
                                page=page,
                            )
                            break
                return True

            except:
                return False
        else:
            await self.change_countinous_stock(
                product, website_name="flipkart", value=False
            )
            return True

    async def scrape_shopatsc(self, page_html, product, page=None):
        soup = BeautifulSoup(page_html, "html.parser")
        pincode_input_element = soup.find(class_="checker-combine")
        if pincode_input_element is not None:
            await self.run_notifications(
                website_name="shopatsc",
                product=product,
                method="Enter PINCODE element exists.",
                page=page,
            )
        else:
            await self.change_countinous_stock(
                product, website_name="shopatsc", value=False
            )
        return True
    
    async def scrape_reliance(self, page_html, product, page=None):
        soup = BeautifulSoup(page_html, "html.parser")
        add_to_cart_button = soup.find(id="add_to_cart_main_btn")
        buy_now_button = soup.find(id="buy_now_main_btn")
        notify_me_button = soup.find(id="notify_me_btn_main")
        pincode_input_element = soup.find(class_="pdp__pincodeSection")
        # print(product)
        # print("Add to cart",add_to_cart_button)
        # print("Buy now",buy_now_button)
        # print("Notify:",notify_me_button)
        # print("Pincode:",pincode_input_element)
        # print("-----------")
        if notify_me_button is None:
            pass
        elif add_to_cart_button is not None:
            await self.run_notifications(
                website_name="reliance",
                product=product,
                method="Add to Cart button.",
                page=page,
            )
        elif buy_now_button is not None:
            await self.run_notifications(
                website_name="reliance",
                product=product,
                method="Buy Now button.",
                page=page,
            )
        elif pincode_input_element is not None:
            await self.run_notifications(
                website_name="reliance",
                product=product,
                method="Enter PINCODE element is exists.",
                page=page,
            )
        else:
            await self.change_countinous_stock(
                product, website_name="reliance", value=False
            )
        return True
    
    async def scrape_ppgc(self, page_html, product, page=None):
        soup = BeautifulSoup(page_html, "html.parser")
        add_to_cart_button = soup.find(attrs={"name" : "add-to-cart"})
        if add_to_cart_button is not None:
            await self.run_notifications(
                website_name="ppgc",
                product=product,
                method="Add to Cart button",
                page=page,
            )
        else:
            await self.change_countinous_stock(
                product, website_name="games_the_shop", value=False
            )
        return True

    async def scrape_games_the_shop(self, page_html, product, page=None):
        # soup = BeautifulSoup(page_html, "html.parser")
        # #add_to_cart_button = soup.find_all("div",class_= re.compile("addToCart"))
        # add_to_cart_button = soup.find_all(class_= "addToCart-nw addToCart-nw-dv bo errorherebg-blu")

        # print(add_to_cart_button)
        doc = lxml.html.fromstring(page_html)
        try:
            stock = doc.xpath(
                '//*[@id="ctl00_ContentPlaceHolder1_divOfferDetails"]/div/div[2]/div/div[2]/div[1]/text()'
            )
        except:
            return False

        if " ADD TO CART" in stock:
            await self.run_notifications(
                website_name="games_the_shop",
                product=product,
                method="Add to Cart button",
                page=page,
            )
        else:
            await self.change_countinous_stock(
                product, website_name="games_the_shop", value=False
            )
        return True


def setup(bot):
    bot.add_cog(Scrapper(bot))
