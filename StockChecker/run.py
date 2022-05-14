from discord.ext import commands
import config
import asyncio


class RunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ScrapperCog = self.bot.get_cog("Scrapper")
        self.bot.loop.create_task(self.start())
    

    async def start(self):

        if config.mode == "Requests":
            self.RequestsCog = self.bot.get_cog("RequestsCog")
            self.bot.loop.create_task(self.startup_requests_scrapping())
        
        elif config.mode == "Playwright":
            self.PlaywrightCog = self.bot.get_cog("PlaywrightCog")
            self.bot.loop.create_task(self.startup_playwright_scrapping())
        
        elif config.mode == "Basic":
            self.RequestsCog = self.bot.get_cog("RequestsCog")
            self.bot.loop.create_task(self.startup_basic())
        
        elif config.mode == "All":
            self.RequestsCog = self.bot.get_cog("RequestsCog")
            self.bot.loop.create_task(self.startup_requests_scrapping())
            
            self.PlaywrightCog = self.bot.get_cog("PlaywrightCog")
            self.bot.loop.create_task(self.startup_playwright_scrapping())
        
        elif config.mode == "Pause":
           pass

        else:
            print(f"Mode {config.mode} not found. Exiting...")


    # async def startup_basic(self):
    #     await self.bot.wait_until_ready()

    #     # Requests
    #     # Amazon Wishlist
    #     for product in ["PS_WISHLIST", "XBOX_WISHLIST"]:
    #         self.bot.loop.create_task(
    #             self.RequestsCog.requests_scrapper(
    #                 product_name=product,
    #                 website_name="amazon",
    #                 scrapper_function=self.ScrapperCog.scrape_amazon_wishlist,
    #                 delay=10,
    #             )
    #         )
    #     # Flipkart
    #     for product in [
    #         "PS5",
    #         "PS5_DE",
    #         #"XSX",
    #         #"XSX_HALO_EDITION",
    #         #"XBOX_WIRELESS_HEADSET",
    #         #"XSX_HALO_EDITION_CONTROLLER",
    #         # "XSS",
    #     ]:
    #         self.bot.loop.create_task(
    #             self.RequestsCog.requests_scrapper(
    #                 product_name=product,
    #                 website_name="flipkart",
    #                 scrapper_function=self.ScrapperCog.scrape_flipkart,
    #                 delay=10,
    #             )
    #         )
        
    #     # # Playwright
    #     # # Amazon Wishlist
    #     # for product in ["PS_WISHLIST", "XBOX_WISHLIST"]:
    #     #     self.bot.loop.create_task(
    #     #         self.PlaywrightCog.playwright_scrapper(
    #     #             product_name=product,
    #     #             website_name="amazon",
    #     #             scrapper_function=self.ScrapperCog.scrape_amazon_wishlist,
    #     #             delay=15,
    #     #         )
    #     #     )

    #     # # Flipkart
    #     # for product in [
    #     #     "PS5",
    #     #     "PS5_DE",
    #     #     "XSX",
    #     #     "XSX_HALO_EDITION",
    #     #     # "XSS",
    #     # ]:
    #     #     self.bot.loop.create_task(
    #     #         self.PlaywrightCog.playwright_scrapper(
    #     #             product_name=product,
    #     #             website_name="flipkart",
    #     #             scrapper_function=self.ScrapperCog.scrape_flipkart,
    #     #             delay=15,
    #     #         )
    #     #     )

    async def startup_requests_scrapping(self):
        await self.bot.wait_until_ready()

        # Amazon Wishlist
        for product in ["PS_WISHLIST", "XBOX_WISHLIST"]:
            self.bot.loop.create_task(
                self.RequestsCog.requests_scrapper(
                    product_name=product,
                    website_name="amazon",
                    scrapper_function=self.ScrapperCog.scrape_amazon_wishlist,
                    delay=10,
                )
            )

        # Flipkart
        for product in [
            "PS5",
            "PS5_DE",
            "XSX",
            #"XSX_HALO_EDITION",
            #"XBOX_WIRELESS_HEADSET",
            #"XSX_HALO_EDITION_CONTROLLER",
            # "XSS",
        ]:
            self.bot.loop.create_task(
                self.RequestsCog.requests_scrapper(
                    product_name=product,
                    website_name="flipkart",
                    scrapper_function=self.ScrapperCog.scrape_flipkart,
                    delay=10,
                )
            )

        # Shop At Sony Center
        for product in [
            "PS5",
            "PS5_DE",
            "PS5_GT7_BUNDLE",
            # "RED_DS",
            # "BLACK_DS",
        ]:
            self.bot.loop.create_task(
                self.RequestsCog.requests_scrapper(
                    product_name=product,
                    website_name="shopatsc",
                    scrapper_function=self.ScrapperCog.scrape_shopatsc,
                    delay=20,
                )
            )

        # # Reliance Digital
        # for product in [
        #     "PS5",
        #     "PS5_DE",
        #     #"XSX",
        # ]:
        #     self.bot.loop.create_task(
        #         self.RequestsCog.requests_scrapper(
        #             product_name=product,
        #             website_name="reliance",
        #             scrapper_function=self.ScrapperCog.scrape_reliance,
        #             delay=20,
        #         )
        #     )

        # # Prepaid Gamer Card
        # for product in [
        #     "PS5",
        #     "PS5_DE",
        #     # "XSX",
        #     "XSX_HALO_EDITION",
        # ]:
        #     self.bot.loop.create_task(
        #         self.RequestsCog.requests_scrapper(
        #             product_name=product,
        #             website_name="ppgc",
        #             scrapper_function=self.ScrapperCog.scrape_ppgc,
        #             delay=60,
        #         )
        #     )

        # # Games the Shop
        # for product in ["PS5", "PS5_DE"]:
        #     self.bot.loop.create_task(
        #        self.RequestsCog.requests_scrapper(
        #             product_name=product,
        #             website_name="games_the_shop",
        #             scrapper_function=self.ScrapperCog.scrape_games_the_shop,
        #             delay=30,
        #         )
        #     )

    async def startup_playwright_scrapping(self):
        await self.bot.wait_until_ready()
        await self.PlaywrightCog.start_playwright()
        # Amazon Wishlist
        for product in ["PS_WISHLIST", "XBOX_WISHLIST"]:
            self.bot.loop.create_task(
                self.PlaywrightCog.playwright_scrapper(
                    product_name=product,
                    website_name="amazon",
                    scrapper_function=self.ScrapperCog.scrape_amazon_wishlist,
                    delay=15,
                )
            )

        # Flipkart
        for product in [
            "PS5",
            "PS5_DE",
            #"XSX",
            #"XSX_HALO_EDITION",
            # "XSS",
        ]:
            self.bot.loop.create_task(
                self.PlaywrightCog.playwright_scrapper(
                    product_name=product,
                    website_name="flipkart",
                    scrapper_function=self.ScrapperCog.scrape_flipkart,
                    delay=20,
                )
            )

        # Shop At Sony Center
        for product in [
            "PS5",
            "PS5_DE",
            "PS5_GT7_BUNDLE",
            # "RED_DS",
            # "BLACK_DS",
        ]:
            self.bot.loop.create_task(
                self.PlaywrightCog.playwright_scrapper(
                    product_name=product,
                    website_name="shopatsc",
                    scrapper_function=self.ScrapperCog.scrape_shopatsc,
                    delay=60,
                )
            )

        # # Reliance Digital
        # for product in [
        #     "PS5",
        #     "PS5_DE",
        #     "XSX",
        # ]:
        #     self.bot.loop.create_task(
        #         self.PlaywrightCog.playwright_scrapper(
        #             product_name=product,
        #             website_name="reliance",
        #             scrapper_function=self.ScrapperCog.scrape_reliance,
        #             delay=30,
        #         )
        #     )

        # # Prepaid Gamer Card
        # for product in ["PS5", "PS5_DE", "XSX", "XSX_HALO_EDITION"]:
        #     self.bot.loop.create_task(
        #         self.PlaywrightCog.playwright_scrapper(
        #             product_name=product,
        #             website_name="ppgc",
        #             scrapper_function=self.ScrapperCog.scrape_ppgc,
        #             delay=30,
        #         )
        #     )

        # # Games the Shop
        # for product in ["PS5", "PS5_DE"]:
        #     self.bot.loop.create_task(
        #        self.PlaywrightCog.playwright_scrapper(
        #             product_name=product,
        #             website_name="games_the_shop",
        #             scrapper_function=self.ScrapperCog.scrape_games_the_shop,
        #             delay=30,
        #         )
        #     )


def setup(bot):
    bot.add_cog(RunCog(bot))
