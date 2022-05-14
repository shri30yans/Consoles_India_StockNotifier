from dotenv import load_dotenv
import os

#####################
# Choose True or False
notify = True

# Modes:
# 1. Basic (Amazon/Flipkart only, No other cogs are loaded)
# 2. Requests
# 3. Playwright
# 4. All
# 5. Pause
mode = "Requests"

#####################

# Fetch details from .env file
load_dotenv()
# Discord
TOKEN = os.getenv("DISCORD_TOKEN")

#Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = "@Consoles_India"

# Twitter
consumer_key = os.getenv("consumer_key")
consumer_secret = os.getenv("consumer_secret")
access_token = os.getenv("access_token")
access_token_secret = os.getenv("access_token_secret")

# Database
DATABASE_DICT = dict(eval(os.getenv("DISCORD_DATABASE_DETAILS")))

# Prefixes
default_prefixes = ["?", "!"]
server_prefixes = {797570077364977696: ["!s"]}


# List of Cogs to run on startup
STARTUP_COGS = [
    "cogs.UtilityCog",
    "cogs.TagsCog",
    "cogs.DatabaseCog",
    "cogs.RepCog",
    "cogs.TradeChannelCog",
    "cogs.RandomCog",
    "utils.ErrorHandler",
    "jishaku",
    "StockChecker.scrapper",
    "StockChecker.RequestsStockChecker",
    #"StockChecker.PlaywrightStockChecker",
    "StockChecker.run",
    # "StockChecker.gui",
    "StockChecker.Notifications",
]

BASIC_COGS = [
    "utils.ErrorHandler",
    "jishaku",
    "StockChecker.scrapper",
    "StockChecker.RequestsStockChecker",
    #"StockChecker.PlaywrightStockChecker",
    "StockChecker.run",
    # "StockChecker.gui",
    # "StockChecker.PlaywrightStockCheckerSeparate",
    "StockChecker.Notifications",
]

my_server_id = 889437492477046785
playstation_server_id = 797570077364977696

amazon_affiliate_tag = "consolesindia-21"

# Channels
PS_stock_notification_channel = 892795445112369183
XBOX_stock_notification_channel = 893754612547481630
PS_India_stock_notification_channel = 850096085770567700

# PS Server
mod_logs_channel_id = 860121260369379328
trade_category_id = 844087063405395999
PS_game_deals_channel_id = 806509594049511464

# My Server
suggestions_channel_id = 898472126602948608
meme_channel_id = 892798621458776074
game_deals_channel_id = 892796421525364796
my_deals_channel_id = 932459628225253427
feed_channel_id = 859392494487732244

feed_notification_role_id = 945564793983631360


# Notification channel configurations
both_playstation_channels = {
    my_server_id: PS_stock_notification_channel,
    playstation_server_id: PS_India_stock_notification_channel,
}
xbox_channel = {my_server_id: XBOX_stock_notification_channel}
playstation_channel = {my_server_id: PS_stock_notification_channel}

# Mod roles
head_moderator_role_id = 798978668403753000
moderator_role_id = 803139873078771713
game_trade_moderator_role_id = 815165934338965504
admin_role_id = 797840269109624862
bot_role_id = 797840270028701756

embed_colours = [0x00FFFF]  # blue

# Emoji's
XSX_emoji = "<:XSX:893792926574972929>"
XSS_emoji = "<:XSS:893792927090884628>"
PS5_emoji = "<:PS5:893792926050684929>"
PS5_DE_emoji = "<:PS5_DE:893792926705020960>"
RED_DS_emoji = "<:Red_Dualsense:864361711183593472>"
BLACK_DS_emoji = "<:Black_Dualsense:864361710532952064>"
upvote_reaction = "<:upvote:895214345498275910>"
downvote_reaction = "<:downvote:895214345548611614>"
suggestion_yes = "👍"
suggestion_no = "👎"
cog_emojis = {}
loading_reaction = "<a:loading:931910934312652850>"
PS_Leaks_Emoji = "<:PSLeaks:941751129627308032>"
PS_News_Emoji = "<:PSNews:941750280754692116>"
