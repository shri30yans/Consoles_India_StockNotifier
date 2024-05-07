import config
import asyncio
import platform, os
from StockChecker.scrapper import ScrapperObj
from StockChecker.RequestsStockChecker import RequestsClass
from StockChecker.PlaywrightStockChecker import PlaywrightClass


tasks = []
RequestsObj = RequestsClass()
PlaywrightObj = PlaywrightClass()


print(f"Bot started")
print(f"Python version: {platform.python_version()}")
print(f"Running on: {platform.system()} {platform.release()} ({os.name})")
print("-------------------")
print(f"Notifications are set to {config.notify}")
print(f"Scrapping mode is set to {config.mode}")
print("-------------------")


async def start_requests_scrapping():
    # Amazon Wishlist
    for product in [
        "PS_WISHLIST", 
        #"XBOX_WISHLIST"
    ]:
        tasks.append(
            asyncio.create_task(
                RequestsObj.requests_scrapper(
                    product_name=product,
                    website_name="amazon",
                    scrapper_function=ScrapperObj.scrape_amazon_wishlist,
                    delay=5,
                )
            )
        )
    
    # # Amazon Direct webpage
    # for product in [
    #     "TEST",
    #     "PS5",
    #     "PS5_DE",
    #     "PS5_HFW_BUNDLE",
    #     "PS5_DE_HFW_BUNDLE",
    #     #"XSX",
    #     #"XSX_HALO_EDITION",
    #     # "XBOX_WIRELESS_HEADSET",
    #     # "XSX_HALO_EDITION_CONTROLLER",
    #     # "XSS",
    # ]:
    #     tasks.append(
    #         asyncio.create_task(
    #             RequestsObj.requests_scrapper(
    #                 product_name=product,
    #                 website_name="amazon",
    #                 scrapper_function=ScrapperObj.scrape_amazon,
    #                 delay=5,
    #             )
    #         )
    #     )

    # Flipkart
    for product in [
        "ROG_ALLY_Z1_EXTREME",
        #"TEST",
        #"PS5",
        #"PS5_DE",
        #"XSX",
        #"XSX_HALO_EDITION",
        # "XBOX_WIRELESS_HEADSET",
        # "XSX_HALO_EDITION_CONTROLLER",
        # "XSS",
    ]:
        tasks.append(
            asyncio.create_task(
                RequestsObj.requests_scrapper(
                    product_name=product,
                    website_name="flipkart",
                    scrapper_function=ScrapperObj.scrape_flipkart,
                    delay=10,
                )
            )
        )

    # Shop At Sony Center
    for product in [
        # "PS5",
        # "PS5_DE",
        # "PS5_GT7_BUNDLE",
        # "PS5_HFW_BUNDLE",
        # "PS5_DE_HFW_BUNDLE",
        # "RED_DS",
        # "BLACK_DS",
    ]:
        tasks.append(
            asyncio.create_task(
                RequestsObj.requests_scrapper(
                    product_name=product,
                    website_name="shopatsc",
                    scrapper_function=ScrapperObj.scrape_shopatsc,
                    delay=5,
                )
            )
        )

    # # Reliance Digital
    # for product in [
    #     "PS5",
    #     "PS5_DE",
    #     # "XSX",
    # ]:
    #     tasks.append(
    #         asyncio.create_task(
    #             RequestsObj.requests_scrapper(
    #                 product_name=product,
    #                 website_name="reliance",
    #                 scrapper_function=ScrapperObj.scrape_reliance,
    #                 delay=20,
    #             )
    #         )
    #     )

    # # Prepaid Gamer Card
    # for product in [
    #     "PS5",
    #     "PS5_DE",
    #     # "XSX",
    #     "XSX_HALO_EDITION",
    # ]:
    #     tasks.append(
    #         asyncio.create_task(
    #             RequestsObj.requests_scrapper(
    #                 product_name=product,
    #                 website_name="ppgc",
    #                 scrapper_function=ScrapperObj.scrape_ppgc,
    #                 delay=60,
    #             )
    #         )
    #     )

    # # Games the Shop
    # for product in ["PS5", "PS5_DE"]:
    #     tasks.append(
    #         asyncio.create_task(
    #             RequestsObj.requests_scrapper(
    #                 product_name=product,
    #                 website_name="games_the_shop",
    #                 scrapper_function=ScrapperObj.scrape_games_the_shop,
    #                 delay=30,
    #             )
    #         )
    #     )




async def start_playwright_scrapping():
    await PlaywrightObj.start_playwright()
    # Amazon Wishlist
    for product in ["PS_WISHLIST", "XBOX_WISHLIST"]:
        tasks.append(
            asyncio.create_task(
                PlaywrightObj.playwright_scrapper(
                    product_name=product,
                    website_name="amazon",
                    scrapper_function=ScrapperObj.scrape_amazon_wishlist,
                    delay=5,
                )
            )
        )

    # Flipkart
    for product in [
        "PS5",
        "PS5_DE",
        "PS5_HFW_BUNDLE",
        "PS5_DE_GT7_BUNDLE",
        #"XSX_FORZA_EDITION",
        # "XSX",
        # "XSX_HALO_EDITION",
        # "XSS",
    ]:
        tasks.append(
            asyncio.create_task(
                PlaywrightObj.playwright_scrapper(
                    product_name=product,
                    website_name="flipkart",
                    scrapper_function=ScrapperObj.scrape_flipkart,
                    delay=5,
                )
            )
        )

    # Shop At Sony Center
    for product in [
        "PS5",
        "PS5_DE",
        #"PS5_GT7_BUNDLE",
        "PS5_HFW_BUNDLE",
        "PS5_DE_GT7_BUNDLE",
        # "RED_DS",
        # "BLACK_DS",
    ]:
        tasks.append(
            asyncio.create_task(
                PlaywrightObj.playwright_scrapper(
                    product_name=product,
                    website_name="shopatsc",
                    scrapper_function=ScrapperObj.scrape_shopatsc,
                    delay=5,
                )
            )
        )

    # Reliance Digital
    for product in [
        "PS5",
        "PS5_DE",
        "XSX",
    ]:
        asyncio.create_task(
            PlaywrightObj.playwright_scrapper(
                product_name=product,
                website_name="reliance",
                scrapper_function=ScrapperObj.scrape_reliance,
                delay=30,
            )
        )

    # Prepaid Gamer Card
    for product in ["PS5", "PS5_DE", "XSX", "XSX_HALO_EDITION"]:
        asyncio.create_task(
            tasks.append(
                asyncio.create_task(
                    PlaywrightObj.playwright_scrapper(
                        product_name=product,
                        website_name="ppgc",
                        scrapper_function=ScrapperObj.scrape_ppgc,
                        delay=30,
                    )
                )
            )
        )

    # Games the Shop
    for product in ["PS5", "PS5_DE"]:
        tasks.append(
            asyncio.create_task(
                asyncio.create_task(
                    PlaywrightObj.playwright_scrapper(
                        product_name=product,
                        website_name="games_the_shop",
                        scrapper_function=ScrapperObj.scrape_games_the_shop,
                        delay=30,
                    )
                )
            )
        )
    
async def start():
    if config.mode.lower() == "requests":
        await start_requests_scrapping()

    elif config.mode.lower() == "playwright":
        await start_playwright_scrapping()

    elif config.mode.lower() == "all":
        await start_requests_scrapping()
        await start_playwright_scrapping()
    
    elif config.mode.lower() == "pause":
        pass

    else:
        print(f"Mode {config.mode} not found. Exiting...")
    
    await asyncio.gather(*tasks)
    



asyncio.run(start())

# loop = asyncio.get_event_loop()
# loop.run_until_complete(asyncio.gather(mocked_function()))
