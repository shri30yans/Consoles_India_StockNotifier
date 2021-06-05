import discord
from discord.ext import commands
import config   
from pytz import timezone
from datetime import datetime
from utils.links import All_Websites 
    
class Notifications(commands.Cog): 
    def __init__(self, bot):
        self.bot = bot
    
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



    


    

def setup(bot):
    bot.add_cog(Notifications(bot))