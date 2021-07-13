import discord,os,time
from discord.ext import commands
import config   
from pytz import timezone
from datetime import datetime
from utils.links import All_Websites 
#from selenium import webdriver

    
class Notifications(commands.Cog): 
    def __init__(self, bot):
        self.bot = bot
        #Heroku
        # chrome_options = webdriver.ChromeOptions()
        # #chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        # chrome_options.add_argument("--headless")
        # #chrome_options.add_argument("--disable-dev-shm-usage")
        # #chrome_options.add_argument("--no-sandbox")
        # #self.driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
        # self.driver = webdriver.Chrome()
        # self.driver.set_window_size(1800,900)

        # options = webdriver.ChromeOptions()
        # options.headless = True
        # self.driver = webdriver.Chrome(options=options)
        # self.driver.set_window_size(1800,900)



    
    async def notify(self,website_name,product,method):
        guild = await self.bot.fetch_guild(config.server_id)
        channel=await self.bot.fetch_channel(config.stock_notifications_channel_id)
        Website_Class=All_Websites[website_name]
        
        if product == "PS5":
            role = guild.get_role(config.PS5_stock_notifications_role_id)
            embed = discord.Embed(title =f"PS5 in stock at {Website_Class.display_name}!",url=Website_Class.PS5_link,color =0x0000FF)
            embed.add_field(name="Dev Notes:",value=f"`{method}`")
            embed.set_thumbnail(url="https://i.imgur.com/pmgar66.jpg?1") 
            Indian_Time = datetime.now(timezone("Asia/Kolkata")).strftime('%d-%m-%y • %H:%M:%S')
            embed.set_footer(text=f"PS5 Stock Updates • {Indian_Time}")

        elif product == "PS5_DE":
            role = guild.get_role(config.PS5_DE_stock_notifications_role_id)
            embed = discord.Embed(title =f"PS5 Digital Edition in stock at {Website_Class.display_name}!",url=Website_Class.PS5_DE_link,color =0x0000FF)
            embed.add_field(name="Dev Notes:",value=f"`{method}`")
            embed.set_thumbnail(url="https://i.imgur.com/pmgar66.jpg?1") 
            Indian_Time = datetime.now(timezone("Asia/Kolkata")).strftime('%d-%m-%y • %H:%M:%S')
            embed.set_footer(text=f"PS5 DE Stock Updates • {Indian_Time}")
        
        elif product == "XSX":
            role = guild.get_role(config.XSX_stock_notifications_role_id)
            embed = discord.Embed(title =f"Xbox Series X in stock at {Website_Class.display_name}!",url=Website_Class.XSX_link,color =0x0000FF)
            embed.add_field(name="Dev Notes:",value=f"`{method}`")
            embed.set_thumbnail(url="https://i.imgur.com/WpKbZXR.jpg") 
            Indian_Time = datetime.now(timezone("Asia/Kolkata")).strftime('%d-%m-%y • %H:%M:%S')
            embed.set_footer(text=f"Xbox Series X Stock Updates • {Indian_Time}")
        
        elif product == "XSS":
            role = guild.get_role(config.XSS_stock_notifications_role_id)
            embed = discord.Embed(title =f"Xbox Series S in stock at {Website_Class.display_name}!",url=Website_Class.XSS_link,color =0x0000FF)
            embed.add_field(name="Dev Notes:",value=f"`{method}`")
            embed.set_thumbnail(url="https://i.imgur.com/OpInEum.jpg") 
            Indian_Time = datetime.now(timezone("Asia/Kolkata")).strftime('%d-%m-%y • %H:%M:%S')
            embed.set_footer(text=f"Xbox Series S Stock Updates • {Indian_Time}")
        
        elif product == "BLACK_DS":
            role = guild.get_role(config.BLACK_DS_stock_notifications_role_id)
            embed = discord.Embed(title =f"Black Dualsense in stock at {Website_Class.display_name}!",url=Website_Class.XSS_link,color =0x0000FF)
            embed.add_field(name="Dev Notes:",value=f"`{method}`")
            embed.set_thumbnail(url="https://i.imgur.com/25S4UKg.png") 
            Indian_Time = datetime.now(timezone("Asia/Kolkata")).strftime('%d-%m-%y • %H:%M:%S')
            embed.set_footer(text=f"Dualsense Stock Updates • {Indian_Time}")
        
        elif product == "RED_DS":
            role = guild.get_role(config.RED_DS_stock_notifications_role_id)
            embed = discord.Embed(title =f"Red Dualsense in stock at {Website_Class.display_name}!",url=Website_Class.XSS_link,color =0x0000FF)
            embed.add_field(name="Dev Notes:",value=f"`{method}`")
            embed.set_thumbnail(url="https://i.imgur.com/Z6nsHlN.png?1") 
            Indian_Time = datetime.now(timezone("Asia/Kolkata")).strftime('%d-%m-%y • %H:%M:%S')
            embed.set_footer(text=f"Dualsense Stock Updates • {Indian_Time}")

        else:
            print('Invalid product set to Notification')

        if role is None:
            await channel.send(embed=embed)
        else:
            await channel.send(embed=embed,content=role.mention)
        #await self.screenshot(Website_Class.link)
    
    # @commands.is_owner()
    # @commands.command(name="ScreenShot",aliases=['ss'], help=f'Returns ScreenShot of webpage \n {config.prefix}ss url \nAliases: ss ')
    # async def screenshot(self,url): 
    #     channel=await self.bot.fetch_channel(config.screenshot_sharing_channel_id)     
    #     _start = time.time()
    #     self.driver.get(url)
    #     self.driver.get_screenshot_as_file("screenshot.png")
    #     _end = time.time()
    #     _time_taken = round(_end - _start,2)
    #     await channel.send(content=f"Took `{_time_taken}` seconds to fetch the screenshot",file=discord.File('screenshot.png'))
    #     os.remove('screenshot.png')




    


    

def setup(bot):
    bot.add_cog(Notifications(bot))