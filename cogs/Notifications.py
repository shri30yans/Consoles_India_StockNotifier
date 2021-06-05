import discord,os,time
from discord.ext import commands
import config   
from pytz import timezone
from datetime import datetime
from utils.links import All_Websites 
from selenium import webdriver

    
class Notifications(commands.Cog): 
    def __init__(self, bot):
        self.bot = bot
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

    
    async def notify(self,website_name):
        guild = await self.bot.fetch_guild(config.server_id)
        role = discord.utils.get(guild.roles, id=config.stock_notifications_role_id)


        channel=await self.bot.fetch_channel(config.stock_notifications_channel_id)
        Website_Class=All_Websites[website_name]
        embed = discord.Embed(title =f"PS5 in stock at {Website_Class.display_name}!",url=Website_Class.link,color =0x0000FF)
        embed.set_thumbnail(url="https://i.imgur.com/pmgar66.jpg?1") 
        #embed.set_image(url="https://i.imgur.com/pmgar66.jpg?1") 
        Indian_Time = datetime.now(timezone("Asia/Kolkata")).strftime('%d-%m-%y • %H:%M:%S')
        embed.set_footer(text=f"PS5 Stock Updates • {Indian_Time}")
        await channel.send(embed=embed,content=role.mention)
    
    
    @commands.command(name="ScreenShot",aliases=['ss'], help=f'Returns ScreenShot of webpage \n {config.prefix}ss url \nAliases: ss ')
    async def ss(self,ctx,url):      
        _start = time.time()
        self.driver.get(url)
        self.driver.get_screenshot_as_file("screenshot.png")
        _end = time.time()
        _time_taken = _end - _start
        await ctx.send(content=f"Took {_time_taken} to fetch the screenshot",file=discord.File('screenshot.png'))
        os.remove('screenshot.png')




    


    

def setup(bot):
    bot.add_cog(Notifications(bot))