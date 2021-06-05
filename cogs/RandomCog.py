import discord,random,platform,os
from discord.ext import commands
import config
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

colourlist=config.embed_colours

class RandomCog(commands.Cog): 
    def __init__(self, bot):
        self.bot = bot
        self.options = webdriver.ChromeOptions()
        self.options.headless = True
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.set_window_size(1800,900)


    
    @commands.command(name="ScreenShot",aliases=['ss'], help=f'Returns ScreenShot of webpage \n {config.prefix}ss url \nAliases: ss ')
    async def ss(self,ctx,url):      
        self.driver.get(url)
        self.driver.get_screenshot_as_file("screenshot.png")
        await ctx.send(file=discord.File('screenshot.png'))
        os.remove('screenshot.png')



           


def setup(bot):
    bot.add_cog(RandomCog(bot))
        