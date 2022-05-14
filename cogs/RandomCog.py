from discord.ext import commands
import config
import discord
import random

class Random(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    # @commands.is_owner()
    # @commands.command(name="Deal",help=f"Sends the text after this to the deal channel.")
    # async def say(self,ctx,*arguments):
    #     response =  ' '.join(arguments) 
    #     deal_channel = self.bot.get_channel(config.my_deals_channel_id)
    #     await deal_channel.send(response)

    #@commands.Cog.listener(name="on_message")
    #async def feed_ping(self, message):
    #    if message.channel.id == config.feed_channel_id and message.author != self.bot.user:
    #        if config.PS_Leaks_Emoji in message.content or config.PS_News_Emoji in message.content:
    #            role = message.guild.get_role(config.feed_notification_role_id)
    #            response = f"||{role.mention}||"
    #            await message.channel.send(response,delete_after=1)
        
    


    @commands.Cog.listener(name="on_message")
    async def automatic_reactions(self, message):
        await self.bot.wait_until_ready()
        if message.author.bot:
            return

        elif message.channel.id == config.suggestions_channel_id:
            if message.content.startswith("*") or message.is_system():
                return
            else:
                await message.add_reaction(config.suggestion_yes)
                await message.add_reaction(config.suggestion_no)

        elif message.channel.id == config.meme_channel_id:
            if (
                len(message.attachments) != 0
                or "https://www.reddit.com/r/" in message.content
            ):
                await message.add_reaction(config.upvote_reaction)
                await message.add_reaction(config.downvote_reaction)

        elif (
            message.channel.id == config.game_deals_channel_id
            or message.channel.id == config.PS_game_deals_channel_id
        ):
            if message.content.startswith("*") or message.is_system():
                return
            else:
                await message.add_reaction(config.suggestion_yes)
                await message.add_reaction(config.suggestion_no)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id == 797570077364977696:
            if "Clonex" in member.name:
                await member.ban()

            # guild=ctx.guild
            # channel= self.bot.get_channel(config.member_count_channel_id)
            # await channel.edit(name=f"Member Count: {guild.member_count}",reason="Member Count")


#     @commands.Cog.listener()
#     async def on_member_remove(self,ctx):
#         if ctx.guild.id==848978999007117313:
#             guild=ctx.guild
#             channel= self.bot.get_channel(config.member_count_channel_id)
#             await channel.edit(name=f"Member Count: {guild.member_count}",reason="Member Count")


def setup(bot):
    bot.add_cog(Random(bot))
