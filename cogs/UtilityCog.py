import discord,random,platform,os
from discord.ext import commands
import config

colourlist=config.embed_colours

class Utility(commands.Cog): 
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="Prefix", help=f'Shows the current prefix \n {config.prefix}prefix')
    async def prefix(self,ctx):
        embed=discord.Embed(title="Current Prefix",color = random.choice(colourlist),timestamp=ctx.message.created_at)
        embed.add_field(name=f"{self.bot.user.name} Prefix",value=f"{config.prefix}",inline=False)
        embed.set_thumbnail(url=str(self.bot.user.avatar_url)) 
        embed.set_footer(icon_url= ctx.author.avatar_url,text=f"Requested by {ctx.message.author} • {self.bot.user.name} ")
        await ctx.send(embed=embed)
    
    @commands.command(name="Info",aliases=['botinfo'], help=f'Returns bot information \n {config.prefix}Info \nAliases: serverstats ')
    async def info(self,ctx):
        embed=discord.Embed(title="Bot Info",color = random.choice(colourlist),timestamp=ctx.message.created_at)
        #embed.add_field(name="Created by:",value=f"Shri30yans",inline=False)
        embed.add_field(name="Prefix",value=f"{config.prefix}",inline=False)
        embed.add_field(name="Servers:",value=f"{str(len(self.bot.guilds))}",inline=False)
        embed.add_field(name="Users:",value=f"{str(len(self.bot.users) + 1)}",inline=False)
        embed.add_field(name="Logged in as:",value=f"{self.bot.user.name}",inline=False)
        embed.add_field(name="Discord.py API version:",value=f"{discord.__version__}",inline=False)
        embed.add_field(name="Python version:",value=f"{platform.python_version()}",inline=False)
        embed.add_field(name="Running on:",value=f"{platform.system()} {platform.release()} ({os.name})",inline=False)
        #embed.add_field(name="Support server",value=f"[Join the support server.](https://top.gg/bot/750236220595896370/vote)",inline=False)
        #embed.add_field(name="Vote",value=f"[Top.gg Vote](https://top.gg/bot/750236220595896370/vote)",inline=False)
        embed.set_thumbnail(url=str(self.bot.user.avatar_url)) 
        embed.set_footer(icon_url= ctx.author.avatar_url,text=f"Requested by {ctx.message.author} • {self.bot.user.name} ")
        await ctx.send(embed=embed)
        

    
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

    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    #@commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(name="CreateTradeChannel",aliases=["ctc"], help=f'Creates a trade channel.  \n{config.prefix}CreateTradeChannel @User1 @User2 @User3 trade_number channel_description \nAliases: ctc',require_var_positional=True)#require_var_positional=True makes sure input is not empty
    async def CreateTicket(self,ctx,members:commands.Greedy[discord.Member],trade_number="",*, description='Trade Channel'):
        if ctx.guild.id in config.APPROVED_SERVERS:
            admin_role=ctx.guild.get_role(config.admin_role_id)
            head_moderator_role=ctx.guild.get_role(config.head_moderator_role_id)
            moderator_role=ctx.guild.get_role(config.moderator_role_id)
            game_trade_moderator_role=ctx.guild.get_role(config.game_trade_moderator_role_id)
            bot_role=ctx.guild.get_role(config.bot_role_id)

        
            overwrites = {  
                            admin_role: discord.PermissionOverwrite(send_messages=True, read_messages=True,),#read_message_history=True,use_external_emojis=True,attach_files=True,embed_links=True),
                            head_moderator_role: discord.PermissionOverwrite(send_messages=True, read_messages=True),
                            moderator_role: discord.PermissionOverwrite(send_messages=True, read_messages=True),
                            game_trade_moderator_role: discord.PermissionOverwrite(send_messages=True, read_messages=True),
                            bot_role: discord.PermissionOverwrite(send_messages=True, read_messages=True),
                            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),}
            member_names=""
            for mbr in members:
                if mbr == ctx.author: pass
                
                elif mbr.bot: pass
                
                else:
                    overwrites[mbr] = discord.PermissionOverwrite(send_messages=True, read_messages=True)
                    try:
                        member_names += mbr.mention + ", "
                    except:
                        try:
                            member_names += mbr.name + ", "
                        except: pass
            if member_names == "":
                member_names="No members were added to this Trade."
            else:
                member_names="Member's added to trade: " + member_names

                        
            category = discord.utils.get(ctx.guild.categories, name="Trades")
            channel = await category.create_text_channel(f'trade {trade_number}', overwrites=overwrites,topic=description,reason="Trade Channel")
            embed=discord.Embed(title=f"Trade channel created.",description=f"{channel.mention} \n{member_names} \nDescription: {description}")        
            embed.set_footer(icon_url= ctx.author.avatar_url,text=f"Requested by {ctx.message.author} • {self.bot.user.name} ")
            await ctx.send(embed=embed)
            embed=discord.Embed(title=f"Trade instructions",)
            embed.add_field(name="Process",value="The selling party would send the product to the buying party. Meanwhile the buying party can transfer a Game Trade Moderator the money. Once the buyer gets the product and checks the condition, the Game Trade Moderator would send the money to the seller.",inline=False)
            embed.add_field(name="Seller Instructions",value="Confirm the product and its price before proceeding further.",inline=False)
            embed.add_field(name="Buyer Instructions",value="Check with the selling party before transferring the amount to a Game Trade Moderator. Make sure collect the tracking ID to make sure the seller shipped it.",inline=False)       
            embed.set_footer(icon_url= ctx.author.avatar_url,text=f"Requested by {ctx.message.author} • {self.bot.user.name} ")
            await channel.send(embed=embed)

        else:
            await ctx.send("You can't use this command in this server. Use this command in a Approved Server.")
    
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
        