# import os,sys,discord,platform,random,aiohttp,json,time,asyncio,textwrap
# from discord.ext import commands
# import config

# colourlist=config.embed_colours  

# class Exit(Exception):   
#     pass
    
# class GameTradeCog(commands.Cog): 
#     def __init__(self, bot):
#         self.bot = bot
    
#     @commands.cooldown(1, 3, commands.BucketType.user)
#     @commands.command(name="Create-Trade",aliases=["ct"], help=f'Create a Trade')
#     async def CreateTrade(self,ctx):

#         async def question_function(ctx,question,description):
#             question_embed=await ctx.send(embed=discord.Embed(title = question,description=description,color = random.choice(colourlist),timestamp=ctx.message.created_at).set_footer(icon_url= ctx.author.avatar_url,text=f"Requested by {ctx.message.author} • {self.bot.user.name} "))
#             try:
#                 answer= await self.bot.wait_for('message', timeout=60.0, check=lambda m:(ctx.author == m.author and ctx.channel == m.channel))
            
#             except asyncio.TimeoutError:
#                 await question_embed.edit(embed=discord.Embed(title ="Timeout Error",description="Your Game trade has expired. Please create a new one.",color = random.choice(colourlist),timestamp=ctx.message.created_at).set_footer(icon_url= ctx.author.avatar_url,text=f"Requested by {ctx.message.author} • {self.bot.user.name} "))
#                 raise Exit("Timeout Error")
#             else: 
#                 if answer.content.lower() in ["cancel","exit"]:
#                     await ctx.send("Your Game Trade has expired.")
#                     raise Exit("Exit")
#                 elif len(answer.content)> 200:
#                     embed=discord.Embed(title=":warning: | Too many Characters ",description="You crossed the limit of 200 characters. ",color = random.choice(colourlist))
#                     embed.add_field(name="Please type within the 200 words Character limit.",value=f"You typed {len(answer.content)} letters. Please reply to this question again", inline=False)
#                     embed.set_footer(icon_url= ctx.author.avatar_url,text=f"Requested by {ctx.message.author} • {self.bot.user.name} ")
#                     await ctx.send(embed=embed)
#                     return await question_function(ctx,question,description)
#                 else:
#                     print("returned")
#                     return answer.content
        
#         await ctx.send("You have successfully created a Game Trade. Your message will be deleted. Please check your Direct Messages to procced further. ",delete_after=5)
#         await ctx.message.delete()

#         product = await question_function(ctx,question="What is the product you are selling?",description="Please enter a brief description of the product you are selling.")
#         condition = await question_function(ctx,question="What is the condition of the product?",description="Explain the condition of the product. (Pre-owned/New/Sealed,Owned for how long, Any damages)")
#         location= await question_function(ctx,question="What is your location?",description="Your city/village.")
#         shipping= await question_function(ctx,question="Explain your shipping arrangment.",description="Should include \nMethod: Included with cost of product/ Separate / Split by both parties \nService: Which shipping retailer are you going for. ")
#         price= await question_function(ctx,question="How much are you expecting for your product?",description="Suggestions: Included with cost of product/ Separate / Split by both parties")
#         #pictures=question_function(ctx,question="How much are you expecting for your product?",description="Suggestions: Included with cost of product/ Separate / Split by both parties")
       
#     @CreateTrade.error
#     async def question_function_Error(self,ctx, error):
#         if isinstance(error,Exit):
#             pass
    

    

# def setup(bot):
#     bot.add_cog(GameTradeCog(bot))