from discord.ext import commands
import config


class Random(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener(name="on_message")
    async def automatic_reactions(self, message):
        await self.bot.wait_until_ready()
        if message.author == self.bot.user:
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


def setup(bot):
    bot.add_cog(Random(bot))
