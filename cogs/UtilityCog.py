import discord, random, platform, os
from discord.ext import commands
import config
import datetime, time

colourlist = config.embed_colours


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.launch_time = datetime.datetime.utcnow()

    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name="stuff")
    async def createmuterole(self, ctx):
        embed = discord.Embed(title="Doing stuff", description="Startup")
        embed.set_footer(
            icon_url=ctx.author.avatar_url,
            text=f"Requested by {ctx.message.author} • {self.bot.user.name}",
        )
        message = await ctx.send(embed=embed)

        embed = discord.Embed(title="stuff", description="Setting permissions...")
        embed.set_footer(
            icon_url=ctx.author.avatar_url,
            text=f"Requested by {ctx.message.author} • {self.bot.user.name}",
        )
        await message.edit(embed=embed)

        role = ctx.guild.get_role(798978668403753000)

        for x in [
            797570310190530560,
            865583434969514014,
            797570078249844736,
            814432680074412073,
            807669335916806154,
            861950014774050826,
            814434416801480704,
            797570078249844737,
            844178807187439617,
            797848476988735528,
            800317930939482112,
            801069934041497631,
            850658377469788180,
            798467157364834324,
            807682660411375656,
        ]:
            category = self.bot.get_channel(x)
            await category.set_permissions(
                role, manage_channels=True, manage_permissions=True
            )
            for channel in category.channels:
                await channel.set_permissions(
                    role,
                    manage_channels=True,
                    manage_permissions=True,
                    view_channel=True,
                )

        embed = discord.Embed(title="Stuff", description=f"Done stuff")
        embed.set_footer(
            icon_url=ctx.author.avatar_url,
            text=f"Requested by {ctx.message.author} • {self.bot.user.name}",
        )
        await message.edit(embed=embed)

    @commands.command(name="Prefix", help=f"Shows the current prefix")
    async def prefix(self, ctx):
        embed = discord.Embed(
            title="Prefix",
            color=random.choice(colourlist),
            timestamp=ctx.message.created_at,
        )
        prefixes_list = (
            config.server_prefixes.get(ctx.guild.id) or config.default_prefixes[0]
        )
        prefixes = ", ".join(prefixes_list)
        embed.add_field(name=f"My Prefix", value=f"`{prefixes}`", inline=False)
        embed.set_thumbnail(url=str(self.bot.user.avatar_url))
        embed.set_footer(
            icon_url=ctx.author.avatar_url,
            text=f"Requested by {ctx.message.author} • {self.bot.user.name} ",
        )
        await ctx.send(embed=embed)

    @commands.command(name="Info", aliases=["botinfo"], help=f"Returns bot information")
    async def info(self, ctx):
        embed = discord.Embed(
            title="Bot Info",
            color=random.choice(colourlist),
            timestamp=ctx.message.created_at,
        )
        # embed.add_field(name="Created by:",value = self.bot.get_user(self.bot.owner_id).mention,inline=False)
        prefixes_list = (
            config.server_prefixes.get(ctx.guild.id) or config.default_prefixes[0]
        )
        prefixes = ", ".join(prefixes_list)
        embed.add_field(name="Prefix", value=f"{prefixes}", inline=False)
        embed.add_field(
            name="Servers:", value=f"{str(len(self.bot.guilds))}", inline=False
        )
        embed.add_field(
            name="Users:", value=f"{str(len(self.bot.users) + 1)}", inline=False
        )
        embed.add_field(
            name="Logged in as:", value=f"{self.bot.user.name}", inline=False
        )
        embed.add_field(
            name="Discord.py API version:", value=f"{discord.__version__}", inline=False
        )
        embed.add_field(
            name="Python version:", value=f"{platform.python_version()}", inline=False
        )
        embed.add_field(
            name="Running on:",
            value=f"{platform.system()} {platform.release()} ({os.name})",
            inline=False,
        )
        # embed.add_field(name="Support server",value=f"[Join the support server.](https://top.gg/bot/750236220595896370/vote)",inline=False)
        # embed.add_field(name="Vote",value=f"[Top.gg Vote](https://top.gg/bot/750236220595896370/vote)",inline=False)
        embed.set_thumbnail(url=str(self.bot.user.avatar_url))
        embed.set_footer(
            icon_url=ctx.author.avatar_url,
            text=f"Requested by {ctx.message.author} • {self.bot.user.name} ",
        )
        await ctx.send(embed=embed)

    @commands.command(name="Ping", help=f'Tells the Ping of a server')
    async def ping(self,ctx):
        """ Pong! """
        start = time.perf_counter()
        message = await ctx.reply(embed=discord.Embed(title=f"{config.loading_reaction}  Pinging",description="Pinging...",color = random.choice(colourlist),timestamp=ctx.message.created_at))
        end = time.perf_counter()
        typing_ping = (end - start) * 1000
        
        start = time.perf_counter()
        async with self.bot.pool.acquire() as connection:
            async with connection.transaction():
                await connection.fetchrow("SELECT rep FROM info LIMIT 1")
        
        end = time.perf_counter()
        database_ping = (end - start) * 1000

        embed=discord.Embed(title="Ping",color = random.choice(colourlist),timestamp=ctx.message.created_at)
        embed.add_field(name="Typing",value=f"```{int(typing_ping)}ms```",inline=True)
        embed.add_field(name="Websocket",value=f"```{round(self.bot.latency * 1000)}ms```",inline=True)
        embed.add_field(name="Database",value=f"```{round(database_ping)}ms```",inline=True)
        embed.set_footer(icon_url=ctx.author.avatar_url,text=f"Requested by {ctx.message.author} • {self.bot.user.name} ")
        await message.edit(embed=embed)

    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(
        name="ServerInfo", aliases=["serverstats", "server"], help=f"Finds server stats"
    )
    async def stats(self, ctx):
        embed = discord.Embed(
            title=f"{ctx.guild.name}",
            color=random.choice(colourlist),
            timestamp=ctx.message.created_at,
        )
        embed.add_field(name="Name", value=f"{ctx.guild.name}", inline=False)
        embed.add_field(name="Owner", value=f" {str(ctx.guild.owner)}", inline=False)
        embed.add_field(name="ID", value=f"{ctx.guild.id}", inline=False)
        embed.add_field(name="Roles", value=f"{len(ctx.guild.roles)}", inline=False)
        embed.add_field(
            name="Features",
            value=f"{(', '.join(x.lower().capitalize().replace('_',' ') for y, x in enumerate(ctx.guild.features))) or 'None'} ",
            inline=False,
        )

        # Member calculator
        members_offline = 0
        members_online = 0
        members_idle = 0
        members_dnd = 0

        no_of_bots = 0
        for member in ctx.guild.members:
            if member.bot:
                no_of_bots = no_of_bots + 1
            else:
                if str(member.status) == "online":
                    members_online += 1
                elif str(member.status) == "dnd":
                    members_dnd += 1
                elif str(member.status) == "idle":
                    members_idle += 1
                elif str(member.status) == "offline":
                    members_offline += 1

                # created_at_time=await self.time_format_function()
                time_ago = await self.find_time_difference(ctx.guild.created_at)
        total_members = members_online + members_offline + members_idle + members_dnd

        embed.add_field(
            name="Member",
            value=f"``` 😀 Total members  {total_members}\n 🟢 Online         {members_online}\n 🔴 Dnd            {members_dnd}\n 🟠 Idle           {members_idle}\n ⚫ Offline        {members_offline}\n 🤖 Bots           {no_of_bots}```",
            inline=False,
        )
        embed.add_field(name="Created", value=f"{time_ago} ago", inline=False)
        embed.set_thumbnail(url=str(ctx.guild.icon_url))
        embed.set_footer(
            icon_url=ctx.author.avatar_url,
            text=f"Requested by {ctx.message.author} • {self.bot.user.name} ",
        )
        await ctx.reply(embed=embed)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(
        name="Uptime", help=f"Shows the amount of time the bot has been up."
    )
    async def uptime(self, ctx):
        time = await self.find_time_difference(self.bot.launch_time)
        await ctx.reply(f"I have been up from {time}.")

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(
        name="Whois", aliases=["userinfo"], help=f"Shows information of a user"
    )
    async def whois(self, ctx, user: discord.Member = None):
        user_mention = user or ctx.author
        embed = discord.Embed(
            title=f"{user_mention}",
            color=random.choice(colourlist),
            timestamp=ctx.message.created_at,
        )
        embed.add_field(
            name="User mention", value=f"{user_mention.mention}", inline=True
        )
        embed.add_field(
            name="Status:", value=f"{user_mention.raw_status.capitalize()}", inline=True
        )
        embed.add_field(
            name="Nickname:", value=f"{str(user_mention.nick)}", inline=True
        )
        embed.add_field(name="User ID:", value=f"{user_mention.id}", inline=False)

        status_string = ""

        if str(user_mention.mobile_status) != "offline":
            status_string += "`📱` Mobile\n"

        if str(user_mention.desktop_status) != "offline":
            status_string += "`💻` Desktop\n"

        if str(user_mention.web_status) != "offline":
            status_string += "`🖥️` Web\n"

        if status_string == "":
            status_string = "Offline"

        embed.add_field(name="Device:", value=f"{status_string}", inline=True)
        join_time_ago = await self.find_time_difference(user_mention.joined_at)
        embed.add_field(name="Joined server:", value=f"{join_time_ago}", inline=False)
        create_time_ago = await self.find_time_difference(user_mention.created_at)
        embed.add_field(
            name="Account made:", value=f"{create_time_ago} ago", inline=False
        )
        top_role = user_mention.top_role
        if str(top_role) == "@everyone":
            pass
        else:
            top_role = top_role.mention

        embed.add_field(name="Top Role:", value=f"{top_role}", inline=False)
        # embed.add_field(name="",value=f"{user_mention.}")
        embed.set_thumbnail(url=str(user_mention.avatar_url))

        author_avatar = ctx.author.avatar_url
        embed.set_footer(
            icon_url=author_avatar,
            text=f"Requested by {ctx.message.author} • {self.bot.user.name} ",
        )
        await ctx.reply(embed=embed)

    async def find_time_difference(self, datetime_object):
        time_difference = datetime.datetime.utcnow() - datetime_object
        td = datetime.timedelta(seconds=time_difference.total_seconds())
        years, remainder = divmod(td.days, 365)
        months, days = divmod(remainder, 30)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        d = {
            "years": years,
            "months": months,
            "days": days,
            "hours": hours,
            "minutes": minutes,
        }

        revised_d = {}
        string = ""
        for unit in list(d):
            if d[unit] != 0:
                revised_d[unit] = d[unit]

        # Units and conjuctions
        for unit in list(revised_d):
            string += f"{revised_d[unit]} {unit}"
            if len(revised_d) > 1:
                if list(revised_d)[-2] == unit:
                    string += " and "
                elif list(revised_d)[-1] == unit:
                    pass
                else:
                    string += ", "
        if string == "":
            string = "1 second"
        return string

    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.command(name="Delete", aliases=["del", "clear"], help=f"Deletes messages")
    async def delete(self, ctx, num: int):
        if num > 100:
            embed = discord.Embed(
                color=random.choice(colourlist), timestamp=ctx.message.created_at
            )
            embed.add_field(
                name="Too many messages deleted.",
                value=f"You can delete a maximum of 100 messages at one go to prevent excessive deleting. ",
            )
            author_avatar = ctx.author.avatar_url
            embed.set_footer(
                icon_url=author_avatar,
                text=f"Requested by {ctx.message.author} • {self.bot.user.name} ",
            )
            await ctx.send(embed=embed, delete_after=4)

        else:
            await ctx.channel.purge(limit=num + 1, bulk=True)
            embed = discord.Embed(
                color=random.choice(colourlist), timestamp=ctx.message.created_at
            )
            embed.add_field(name="Deleted", value=f"Deleted {num} message(s)")
            author_avatar = ctx.author.avatar_url
            embed.set_footer(
                icon_url=author_avatar,
                text=f"Requested by {ctx.message.author} • {self.bot.user.name} ",
            )
            await ctx.send(embed=embed, delete_after=4)

    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command(
        name="PFP", aliases=["dp", "avatar", "av"], help=f"Shows the avatar of a user"
    )
    async def pfp(self, ctx, user: discord.Member = None):
        if user == None:
            user_mention = ctx.author
        else:
            user_mention = user
        embed = discord.Embed(
            title=f"Avatar of {user_mention.name}",
            color=random.choice(colourlist),
            timestamp=ctx.message.created_at,
        )
        embed.set_image(url=user_mention.avatar_url)
        author_avatar = ctx.author.avatar_url
        embed.set_footer(
            icon_url=author_avatar,
            text=f"Requested by {ctx.message.author} • {self.bot.user.name} ",
        )
        await ctx.send(embed=embed)

    # @commands.command(name="sendmsg")
    # async def send_embed(self,ctx,msg_id):
    #     await ctx.message.delete()
    #     message=await ctx.channel.fetch_message(msg_id)
    #     await message.reply(content="https://media1.tenor.com/images/11f97eab72fb4056bdfe7922ba7af723/tenor.gif")

    def time_format_function(self, time):
        time_inputted = time
        time_inputted.strftime("%Y")
        time_inputted.strftime("%m")
        time_inputted.strftime("%d")
        time_inputted.strftime("%H:%M:%S")
        output_time = time_inputted.strftime("%d/%m/%Y (D/M/Y), %H:%M:%S")
        return output_time


def setup(bot):
    bot.add_cog(Utility(bot))
