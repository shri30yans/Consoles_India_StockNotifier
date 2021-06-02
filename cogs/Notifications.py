import os,sys,discord,platform,random,aiohttp,json,time,asyncio,textwrap
from discord.ext import commands,tasks
import config   
from pytz import timezone
from datetime import datetime 
    
class Notifications(commands.Cog): 
    def __init__(self, bot):
        self.bot = bot
    
    async def notify(self,website_name):
        Indian_Time = datetime.now(timezone("Asia/Kolkata")).strftime('%d-%m-%y %H:%M:%S')

        website_links={"flipkart":"https://www.flipkart.com/sony-playstation-5-cfi-1008a01r-825-gb-astro-s-playroom/p/itma0201bdea62fa",
                        "amazon":"https://www.amazon.in/dp/B08FV5GC28"}
        channel=await self.bot.fetch_channel(config.stock_notifications_channel_id)
        link=website_links[website_name]
        embed = discord.Embed(title =f"PS5 in stock at {website_name.capitalize()}!",description=f"[Link]({link})",color =0x0000FF)
        embed.set_footer(text=f"PS5 Stock Updates • Time: {Indian_Time}")
        await channel.send(embed=embed)


    


    

def setup(bot):
    bot.add_cog(Notifications(bot))