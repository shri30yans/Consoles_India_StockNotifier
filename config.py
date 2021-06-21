from dotenv import load_dotenv
import os

#Fetch details from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
#Fetching database details is shifted to main.py
#DATABASE_DICT = dict(eval(os.getenv("DISCORD_DATABASE_DETAILS")))


prefix="?"

APPROVED_SERVERS=[797570077364977696]
#BLACKLIST = []
#List of Cogs to run on startup;
STARTUP_COGS = [
    "cogs.UtilityCog","cogs.Notifications","cogs.StockChecker","utils.ErrorHandler","jishaku"
    ]

#Channels and Roles
#Test Server
# server_id=848978999007117313
# stock_notifications_channel_id=849310570821713927
# stock_notifications_role_id=849561150684659732

#playstation India Server
server_id=797570077364977696
stock_notifications_channel_id = 850096085770567700
PS5_stock_notifications_role_id = 849606173522788352
XSX_stock_notifications_role_id = 856442409142976542
XSS_stock_notifications_role_id = 856442480857972745
#screenshot_sharing_channel_id=850711788144164885

head_moderator_role_id=798978668403753000
moderator_role_id=803139873078771713
game_trade_moderator_role_id=815165934338965504
admin_role_id=797840269109624862
bot_role_id=797840270028701756
#member_count_channel_id=850221909227995137



embed_colours=[0xFFFF00,#yellow
            0xFF0000,#red
            0xFF0000,#green
            0x00FFFF,#blue
            0xFF00FF,#pink
]


