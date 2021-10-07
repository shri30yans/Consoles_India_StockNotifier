from dotenv import load_dotenv
import os

#Fetch details from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
consumer_key = os.getenv("consumer_key")
consumer_secret = os.getenv("consumer_secret")
access_token = os.getenv("access_token")
access_token_secret = os.getenv("access_token_secret")

prefix="?"

#List of Cogs to run on startup
STARTUP_COGS = [
    "cogs.UtilityCog","cogs.TradeChannelCog","utils.ErrorHandler","jishaku",
    "StockChecker.scrapper","StockChecker.RequestsStockChecker","StockChecker.Notifications",#"StockChecker.PlaywrightStockChecker"
    ]

my_server_id = 893734056720740352
playstation_server_id=797570077364977696


#Channels
PS_stock_notification_channel = 892795445112369183
XBOX_stock_notification_channel = 893754612547481630
PS_India_stock_notification_channel = 850096085770567700

mod_logs_channel_id=860121260369379328
trade_category_id=844087063405395999


#Roles
stock_notification_roles = {
    "PS5" : {playstation_server_id:849606173522788352,my_server_id:893734056720740352},
    "PS5_DE" :  {playstation_server_id:857134006243688458,my_server_id:893734151428132894},
    "XSX" : {my_server_id:893734236392144926},
    "XSS" : {my_server_id:893734365476057119},
    "RED_DS" : {my_server_id:893734512255701035},
    "BLACK_DS" : {my_server_id:893734593621000232}}


#Notification channel configurations
both_playstation_channels = {my_server_id:PS_stock_notification_channel,playstation_server_id:PS_India_stock_notification_channel}
xbox_channel = {my_server_id:XBOX_stock_notification_channel}
playstation_channel = {my_server_id:PS_stock_notification_channel}

#Mod roles
head_moderator_role_id=798978668403753000
moderator_role_id=803139873078771713
game_trade_moderator_role_id=815165934338965504
admin_role_id=797840269109624862
bot_role_id=797840270028701756

#Reaction Messages
#ticket_reaction_message_id=
embed_colours=[0x00FFFF]#blue

#emoji
XSX_emoji="<:XSX:893792926574972929>"
XSS_emoji="<:XSS:893792927090884628>"
PS5_emoji="<:PS5:893792926050684929>"
PS5_DE_emoji = "<:PS5_DE:893792926705020960>"
RED_DS_emoji="<:Red_Dualsense:864361711183593472>"
BLACK_DS_emoji="<:Black_Dualsense:864361710532952064>"

cog_emojis={}