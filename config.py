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

#Playstation India Server
#Channels
server_id=797570077364977696
stock_notifications_channel_id = 850096085770567700
mod_logs_channel_id=860121260369379328

#Roles
PS5_stock_notifications_role_id = 849606173522788352
PS5_DE_stock_notifications_role_id = 857134006243688458
XSX_stock_notifications_role_id = 856442409142976542
XSS_stock_notifications_role_id = 856442480857972745

#Mod roles
head_moderator_role_id=798978668403753000
moderator_role_id=803139873078771713
game_trade_moderator_role_id=815165934338965504
admin_role_id=797840269109624862
bot_role_id=797840270028701756

embed_colours=[0xFFFF00,#yellow
            0xFF0000,#red
            0xFF0000,#green
            0x00FFFF,#blue
            0xFF00FF,#pink
]

#emoji
XSX_emoji="<:XSX:856448011831738389>"
XSS_emoji="<:XSS:856448352510148628>"
PS5_emoji="<:PS5:856448878340210708>"


#webhook_url="https://discord.com/api/webhooks/858323481296240680/HrsIIfo93fUouPvKR6WE8lwiWDkm2cV6Yd9X22AQ1zbOWyIXEzMzbjEnj77Y6DniLNgF"

webhook_url="https://discord.com/api/webhooks/858329509677498386/dIyMtB0S7-WdDIS2t-AlgWeh14Y5MJ6lXJN_R_r3s0LFhe4uJvX1r8Kmkv6Jz_xlu2OT"