# import os,sys,discord,platform,random,aiohttp,json,time,asyncio,textwrap
# from discord.ext import commands,tasks
# import config   
    
# class Listener(commands.Cog): 
#     def __init__(self, bot):
#         self.bot = bot
    
    
#     @commands.Cog.listener()
#     async def on_member_join(self,ctx):
#         if ctx.guild.id==848978999007117313:
#             guild=ctx.guild
#             channel= self.bot.get_channel(config.member_count_channel_id)
#             await channel.edit(name=f"Member Count: {guild.member_count}",reason="Member Count")
    
#     @commands.Cog.listener()
#     async def on_member_remove(self,ctx):
#         if ctx.guild.id==848978999007117313:
#             guild=ctx.guild
#             channel= self.bot.get_channel(config.member_count_channel_id)
#             await channel.edit(name=f"Member Count: {guild.member_count}",reason="Member Count")

    

# def setup(bot):
#     bot.add_cog(Listener(bot))