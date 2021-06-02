import discord,random
from discord.ext import commands
import config

colourlist=config.embed_colours

class Utility(commands.Cog): 
    def __init__(self, bot):
        self.bot = bot


    
    # @commands.command(name="Info",aliases=['botinfo'], help=f'Returns bot information \n {config.prefix}Info \nAliases: serverstats ')
    # async def info(self,ctx):
    #     embed=discord.Embed(title="Bot Info",color = random.choice(colourlist),timestamp=ctx.message.created_at)
    #     embed.add_field(name="Created by:",value=f"Shri30yans",inline=False)
    #     embed.add_field(name="Prefix",value=f"{config.prefix}",inline=False)
    #     embed.add_field(name="Servers:",value=f"{str(len(self.bot.guilds))}",inline=False)
    #     embed.add_field(name="Users:",value=f"{str(len(self.bot.users) + 1)}",inline=False)
    #     embed.add_field(name="Logged in as:",value=f"{self.bot.user.name}",inline=False)
    #     embed.add_field(name="Discord.py API version:",value=f"{discord.__version__}",inline=False)
    #     embed.add_field(name="Python version:",value=f"{platform.python_version()}",inline=False)
    #     embed.add_field(name="Running on:",value=f"{platform.system()} {platform.release()} ({os.name})",inline=False)
    #     #embed.add_field(name="Support server",value=f"[Join the support server.](https://top.gg/bot/750236220595896370/vote)",inline=False)
    #     #embed.add_field(name="Vote",value=f"[Top.gg Vote](https://top.gg/bot/750236220595896370/vote)",inline=False)
    #     embed.set_thumbnail(url=str(self.bot.user.avatar_url)) 
    #     embed.set_footer(icon_url= ctx.author.avatar_url,text=f"Requested by {ctx.message.author} • {self.bot.user.name} ")
    #     await ctx.send(embed=embed)
        

    
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command(name="Ping", help=f'Tells the Ping of a server \n{config.prefix}ping')
    async def ping(self,ctx):
        """ Pong! """
        message = await ctx.send(embed=discord.Embed(title="Ping",description=":Pong!  :ping_pong:",color = random.choice(colourlist),timestamp=ctx.message.created_at))
        ping = (message.created_at.timestamp() - ctx.message.created_at.timestamp()) * 1000
        embed=discord.Embed(title="Ping",description=f'Pong!  :ping_pong:  \nBot latency: {int(ping)}ms\nWebsocket latency: {round(self.bot.latency * 1000)}ms',color = random.choice(colourlist),timestamp=ctx.message.created_at)
        embed.set_footer(icon_url=ctx.author.avatar_url,text=f"Requested by {ctx.message.author} • {self.bot.user.name} ")
        await message.edit(embed=embed)
    
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command(name="ServerInfo",aliases=['serverstats','server'], help=f'Finds server stats \n{config.prefix}stats \nAliases: serverstats ')
    async def stats(self,ctx):
            #f-strings
            guild_owner=str(ctx.guild.owner)
            embed=discord.Embed(title="Server Stats",color = random.choice(colourlist),timestamp=ctx.message.created_at)
            embed.add_field(name="Name",value=f"{ctx.guild.name}",inline=False)
            if (ctx.message.author.id == ctx.guild.owner_id):
                embed.add_field(name="Owner",value="You are the owner of this server.",inline=False)
            else:
                embed.add_field(name="Owner",value=f"{guild_owner}, is the owner of this server.")
            #Region Convert
            region=str(ctx.guild.region)    
            
            #Member calculator
            no_of_members=0
            no_of_bots=0
            for member in ctx.guild.members:
                if member.bot:
                    no_of_bots=no_of_bots+1
                else:
                    no_of_members=no_of_members+1

            embed.add_field(name="Region",value=f"{region.capitalize() }",inline=False)
            embed.add_field(name="Members",value=f"Members in server: {no_of_members}")
            embed.add_field(name="Bots",value=f"Bots in server: {no_of_bots}",inline=False)
            embed.add_field(name="Roles",value=f"Number of roles: {len(ctx.guild.roles)}")
            created_at_time=self.time_format_function(ctx.guild.created_at)
            embed.add_field(name="Creation date",value=f"{created_at_time}",inline=False) 
            embed.set_thumbnail(url=str(ctx.guild.icon_url)) 
            author_avatar=ctx.author.avatar_url
            embed.set_footer(icon_url= author_avatar,text=f"Requested by {ctx.message.author} • {self.bot.user.name} ")
            await ctx.send(embed=embed) 

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(name="Whois",aliases=["userinfo"], help=f'Shows information of a user \n{config.prefix}whois @User')
    async def whois(self,ctx,user:discord.Member=None):
        if (user == None):
            user_mention= ctx.author
        else:
            user_mention=user
        embed=discord.Embed(title = f"{user_mention.name}",color =random.choice(colourlist), timestamp=ctx.message.created_at)
        embed.add_field(name="Status:",value=f"{user_mention.raw_status.capitalize()}")
        joined_on_time=self.time_format_function(user_mention.joined_at)
        embed.add_field(name="Joined server at:",value=f"{joined_on_time}")
        embed.add_field(name="Nickname:",value=f"{user_mention.nick}")
        
        roles_mention_form=[]
        #roles_mention_form.append(role.mention for role in user_mention.roles)
        for role in user_mention.roles:
            roles_mention_form.append(role.mention)
        #del roles_mention_form[0 :1] 
        roles_mention_form.pop(0)
        roles_mention_form.reverse()
        roles_mention_string =  ' '.join(roles_mention_form)
        embed.add_field(name="Roles:",value=f"{roles_mention_string}")
        made_on_time=self.time_format_function(user_mention.created_at)
        embed.add_field(name="Account made on:",value=f"{made_on_time}")
        embed.add_field(name="User ID:",value=f"{user_mention.id}")
        embed.set_thumbnail(url=str(user_mention.avatar_url)) 

        author_avatar=ctx.author.avatar_url
        embed.set_footer(icon_url= author_avatar,text=f"Requested by {ctx.message.author} • {self.bot.user.name} ")
        await ctx.send(embed=embed)
    
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command(name="PFP",aliases=['dp', 'avatar','av'], help=f'Shows the avatar of a user \n {config.prefix}pfp @User\n Aliases: DP, Avatar ')
    async def pfp(self,ctx,user:discord.Member=None):
        if (user == None):
            user_mention= ctx.author
        else:
            user_mention=user
        embed=discord.Embed(title = f"Avatar of {user_mention.name}", color =random.choice(colourlist), timestamp=ctx.message.created_at)
        embed.set_image(url=user_mention.avatar_url)
        author_avatar=ctx.author.avatar_url
        embed.set_footer(icon_url= author_avatar,text=f"Requested by {ctx.message.author} • {self.bot.user.name} ")
        await ctx.send(embed=embed)    
    
    def time_format_function(self,time):
        time_inputted = time
        time_inputted.strftime("%Y")
        time_inputted.strftime("%m")
        time_inputted.strftime("%d")
        time_inputted.strftime("%H:%M:%S")
        output_time = time_inputted.strftime("%d/%m/%Y (D/M/Y), %H:%M:%S")
        return output_time
           


def setup(bot):
    bot.add_cog(Utility(bot))
        