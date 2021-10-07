import discord
from discord.ext import commands
import config   
from pytz import timezone
from datetime import datetime
import StockChecker.ScrapperConfig as ScrapperConfig
import tweepy

    
class Notifications(commands.Cog): 
    def __init__(self, bot):
        self.bot = bot

    async def notify(self,website_name,product,method,image=None):
        Website_Class = ScrapperConfig.All_Websites[website_name]
        product_obj = ScrapperConfig.All_Products.get(product)

        await self.discord_notify(Website_Class,product_obj,method,image)
        await self.twitter_notify(Website_Class,product_obj,method)

    async def get_product_link(self,product,Website_Class):
        if Website_Class.common_name == "amazon":
            link = Website_Class.affiliate_links.get(product)
        else:
            link = Website_Class.links.get(product)
        return link
    
    async def twitter_notify(self,Website_Class,product_obj,method):
        def OAuth():
            try:
                auth = tweepy.OAuthHandler(config.consumer_key,config.consumer_secret)
                auth.set_access_token(config.access_token,config.access_token_secret)
                return auth
            except Exception as e:
                print(e)

        message = f"❗ {product_obj.name.replace('_',' ')} in stock at {Website_Class.display_name}! {await self.get_product_link(product_obj.name,Website_Class)}\n"#\nDev Notes: {method}\n"
        if Website_Class.common_name == "amazon":
            message += f"🛒 Directly add {product_obj.name.replace('_',' ')} to cart: {Website_Class.add_to_cart_links.get(product_obj.name)}\n"
            message += f"📜 Wishlist link: {Website_Class.affiliate_links.get('WISHLIST')}\n"
        
        Indian_Time = datetime.now(timezone("Asia/Kolkata")).strftime('%d-%m-%y • %H:%M:%S')
        message += f"🕒 Time: {Indian_Time}\n"
        hashtags = product_obj.twitter_hashtags + " #ConsoleStockNotificationsIndia"
        message+=hashtags

        

        oauth = OAuth()
        api = tweepy.API(oauth)
        try:
            api.update_status(message)
            #print("Done")

        except Exception as e:
            print(e)
            print("Try creating Access Tokens and Secret with Read, Write and Direct message permission")
            print("Instructions:\nSettings Tab (near details tab) > Scroll down and Select Read, Write and Accept direct messages.\nClick on Update this twitter's application settings and then generate new tokens.")


    async def discord_notify(self,Website_Class,product_obj,method,image=None):
        async def get_destination(product_obj):
            channel_dict = {}
            for x in product_obj.notification_channels:
                channel = self.bot.get_channel(product_obj.notification_channels.get(x))
                channel_dict[x] = channel
            return channel_dict

        async def get_role(product_obj,channel_dict):
            roles_dict = {}
            notification_roles = config.stock_notification_roles.get(product_obj.name)
            for x in notification_roles:
                channel = channel_dict.get(x)
                role = channel.guild.get_role(notification_roles.get(x))
                roles_dict[x] = role
            return roles_dict

        if product_obj:
            emoji = product_obj.emoji + "  " if product_obj.emoji != "" else ""
            embed = discord.Embed(title =f"{emoji}{product_obj.name.replace('_',' ')} in stock at {Website_Class.display_name}!",url = await self.get_product_link(product_obj.name,Website_Class),color = product_obj.colour)
            embed.add_field(name="Dev Notes:",value=f"`{method}`")
            if product_obj.thumbnail_link:
                embed.set_thumbnail(url=product_obj.thumbnail_link) 
            Indian_Time = datetime.now(timezone("Asia/Kolkata")).strftime('%d-%m-%y • %H:%M:%S')
            embed.set_footer(text=f"{product_obj.name.replace('_',' ')} Stock Updates • {Indian_Time}")

            #Add wishlist link
            if Website_Class.common_name== "amazon" and "wishlist" in method.lower():
                embed.add_field(name="Add product from Wishlist",value=f"If the link isn't working add the product from the [wishlist]({Website_Class.affiliate_links.get('WISHLIST')}/ \"Click this for the wishlist link.\").",inline = False)
                
            file=None
            if image is not None:
                file_name=f"{Website_Class.common_name}_{product_obj.name}.png"
                file = discord.File(fp=image, filename=file_name)
                embed.set_image(url=f"attachment://{file_name}")

            channels = await get_destination(product_obj)
            roles = await get_role(product_obj,channels)
            
            for x in channels:
                role = roles.get(x)
                
                if Website_Class.common_name == "amazon"and x == config.my_server_id:
                    #Add Add_to_cart links for notifications for my server.
                    if x == config.my_server_id:
                        embed.add_field(name="Add to Cart link",value=f"[Directly add {product_obj.name.replace('_',' ')} to cart.]({Website_Class.add_to_cart_links.get(product_obj.name)}/ \"Click this for the add to cart links.\")",inline = False)
                    

                if role is None:
                    await channels.get(x).send(file=file,embed=embed)
                else:
                    await channels.get(x).send(file=file,embed=embed,content=role.mention)
        
        else:
            print('Invalid product set to Notification')
            return

    
    




    


    

def setup(bot):
    bot.add_cog(Notifications(bot))