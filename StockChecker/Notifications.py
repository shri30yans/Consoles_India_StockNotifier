import config, pytz
from pytz import timezone
from datetime import datetime
from io import BytesIO
import logging
import StockChecker.ScrapperConfig as ScrapperConfig
import tweepy
import asyncio, aiohttp

try:
    import winsound
except:
    pass



# Gets or creates a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# define file handler and set formatter
file_handler = logging.FileHandler("StockChecker/logs/Notifications.log")
formatter = logging.Formatter(
    f"{datetime.now(tz=pytz.timezone('Asia/Kolkata'))} : %(levelname)s : %(name)s : %(message)s"
)  # logs in Indian Standard Time
file_handler.setFormatter(formatter)
# add file handler to logger
logger.addHandler(file_handler)



async def notify(ScrapperObj, website_name, product, method, page = None):
    print(f"{product} in stock at {website_name}.")
    logger.info(f"{product} in stock at {website_name}.")
    
    countinous_stock = await ScrapperObj.get_countinous_stock(product, website_name)
    
    if not (countinous_stock):
        # If the product was not in stock during the last check
        
        if page is None:
            image = None
        else:
            screenshot_bytes = await page.screenshot()
            image = BytesIO(screenshot_bytes)

        
        Website_Class = ScrapperConfig.All_Websites.get(website_name)
        Product_Class = ScrapperConfig.All_Products.get(product)

        if Product_Class is None:
            print(product, "is an invalid product sent to notify for.")
        else:
            # Will only notify if notify is enabled in the config file.
            if config.notify:
                print(Product_Class.name, "notified for", Website_Class.name)
                logger.info(f"{product} notified for {website_name}.")
                
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, twitter_notify, Website_Class, Product_Class, method
                )
                # await discord_notify(Website_Class, Product_Class, method, image)
                await telegram_notify(Website_Class, Product_Class, method)
    
    await ScrapperObj.change_countinous_stock(
            product, website_name=website_name, value=True
        )


async def telegram_notify(Website_Class, Product_Class, method):
    message = f"❗ [{Product_Class.display_name} in stock at {Website_Class.display_name}!]({Product_Class.affiliate_links.get(Website_Class.name) or Product_Class.links.get(Website_Class.name)}) %0a"  # \nDev Notes: {method}\n"

    if Website_Class.name == "amazon":
        message += f"[📜 Click on this Wishlist if the link is down.]({Product_Class.wishlist}{f'?tag={config.amazon_affiliate_tag}'}) %0a"
        # message += f"[🛒 Add to cart]({Product_Class.add_to_cart_links.get(Website_Class.name)})%0a"

    Indian_Time = datetime.now(timezone("Asia/Kolkata")).strftime("%d-%m-%y • %H:%M:%S")
    message += f" 🕒 Time: {Indian_Time}"

    link = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage?chat_id={config.TELEGRAM_CHAT_ID}&parse_mode=Markdown&text={message}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=link) as response:
                # print( await response.json())
                pass
    except asyncio.TimeoutError:
        pass


def twitter_notify(Website_Class, Product_Class, method):
    def OAuth():
        try:
            auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
            auth.set_access_token(config.access_token, config.access_token_secret)
            return auth
        except Exception as e:
            print(e)

    message = f"❗ {Product_Class.display_name} in stock at {Website_Class.display_name}! {Product_Class.affiliate_links.get(Website_Class.name) or Product_Class.links.get(Website_Class.name)}\n"  # \nDev Notes: {method}\n"

    if Website_Class.name == "amazon":
        atc_link = Product_Class.add_to_cart_links.get(Website_Class.name)
        if atc_link is not None:
            message += f"🛒 Add to cart: {atc_link}\n"

        message += f"📜 Wishlist: {Product_Class.wishlist+f'?tag={config.amazon_affiliate_tag}'}\n"

    elif Website_Class.name == "shopatsc":
        atc_link = Product_Class.add_to_cart_links.get(Website_Class.name)
        if atc_link is not None:
            message += f"🛒 Add to cart: {atc_link}\n"

    Indian_Time = datetime.now(timezone("Asia/Kolkata")).strftime("%d-%m-%y • %H:%M:%S")
    message += f"🕒 Time: {Indian_Time}\n"
    hashtags = Product_Class.twitter_hashtags + " #ConsolesIndia"
    message += hashtags

    oauth = OAuth()
    api = tweepy.API(oauth)
    try:
        api.update_status(message)

    except Exception as e:
        print(e)
        # print(
        #     "Try creating Access Tokens and Secret with Read, Write and Direct message permission"
        # )
        # print(
        #     "Instructions:\nSettings Tab (near details tab) > Scroll down and Select Read, Write and Accept direct messages.\nClick on Update this twitter's application settings and then generate new tokens."
        # )


# async def discord_notify(Website_Class, Product_Class, method, image=None):

#     emoji = Product_Class.emoji + "  " if Product_Class.emoji != "" else ""
#     embed = discord.Embed(
#         title=f"{emoji}{Product_Class.display_name} in stock at {Website_Class.display_name}!",
#         url=Product_Class.affiliate_links.get(Website_Class.name)
#         or Product_Class.links.get(Website_Class.name),
#         color=Product_Class.colour,
#     )
#     embed.add_field(name="Dev Notes:", value=f"`{method}`")
#     if Product_Class.thumbnail_link:
#         embed.set_thumbnail(url=Product_Class.thumbnail_link)
#     Indian_Time = datetime.now(timezone("Asia/Kolkata")).strftime(
#         "%d-%m-%y • %H:%M:%S"
#     )
#     embed.set_footer(
#         text=f"{Product_Class.display_name} Stock Updates • {Indian_Time}"
#     )

#     # Add atc/wishlist link
#     if Website_Class.name == "amazon":
#         atc_link = Product_Class.add_to_cart_links.get(Website_Class.name)
#         if atc_link is not None:
#             embed.add_field(
#                 name="Add to Cart link",
#                 value=f"[Directly add {Product_Class.name.replace('_',' ')} to cart.]({atc_link}/ \"Click this for the add to cart links.\")",
#                 inline=False,
#             )
#         embed.add_field(
#             name="Wishlist link",
#             value=f"[If the link isn't working add the product from the wishlist.]({Product_Class.wishlist+f'?tag={config.amazon_affiliate_tag}'} 'Click this for the wishlist link.')",
#             inline=False,
#         )

#     elif Website_Class.name == "shopatsc":
#         atc_link = Product_Class.add_to_cart_links.get(Website_Class.name)
#         if atc_link is not None:
#             embed.add_field(
#                 name="Add to Cart link",
#                 value=f"[Directly add {Product_Class.name.replace('_',' ')} to cart.]({atc_link}/ \"Click this for the add to cart links.\")",
#                 inline=False,
#             )


#     file = None
#     if image is not None:
#         file_name = f"{Website_Class.name}_{Product_Class.name}.png"
#         file = discord.File(fp=image, filename=file_name)
#         embed.set_image(url=f"attachment://{file_name}")

#     for x in Product_Class.notification_channels:
#         if Product_Class.notification_channels is not None:
#             channel_id = Product_Class.notification_channels.get(x)
#             channel = bot.get_channel(channel_id)

#             role = None
#             if Product_Class.notification_roles is not None:
#                 role = channel.guild.get_role(
#                     Product_Class.notification_roles.get(channel.guild.id)
#                 )

#             if role is None:
#                 await channel.send(file=file, embed=embed)
#             else:
#                 await channel.send(file=file, embed=embed, content=role.mention)
