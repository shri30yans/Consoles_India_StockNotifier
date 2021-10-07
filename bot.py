import os, sys, discord, platform, random # aiohttp, json, time, asyncio,traceback,asyncpg
from discord.ext import commands,tasks
#from discord.ext.commands.cooldowns import BucketType
from utils.help import EmbedHelpCommand
import config #our config.py
if not os.path.isfile("config.py"):
	sys.exit("'config.py' not found! Please add it and try again.")
else:
	import config

colourlist=config.embed_colours



#bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=commands.when_mentioned_or(config.prefix),case_insensitive = True,intents = intents,help_command=EmbedHelpCommand())
TOKEN = config.TOKEN

@tasks.loop(minutes=15)
async def status_update():
    await bot.wait_until_ready()
    list_of_statuses=[
                        discord.Activity(type = discord.ActivityType.watching, name = f"How to get a PS5?"),
                        discord.Activity(type = discord.ActivityType.playing, name = f"Demon Souls"),
                        discord.Activity(type = discord.ActivityType.playing, name = f"Astro's Playroom"),
                        discord.Activity(type = discord.ActivityType.playing, name = f"Bloodborne"),
                        discord.Activity(type = discord.ActivityType.playing, name = f"God of War"),
                        discord.Activity(type = discord.ActivityType.playing, name = f"The Last of Us"),
                        discord.Activity(type = discord.ActivityType.playing, name = f"Call of Duty: Black Ops - Cold War "),
                        ]

    activity=random.choice(list_of_statuses)
    #activity=list_of_statuses[3]

    await bot.change_presence(status = discord.Status.online, activity =activity)

status_update.start()


for extension in config.STARTUP_COGS:
		try:
			bot.load_extension(extension)
			extension = extension.replace("cogs.", "")
			print(f"Loaded extension '{extension}'")
		except Exception as e:
			exception = f"{type(e).__name__}: {e}"
			extension = extension.replace("cogs.", "")
			print(f"Failed to load extension {extension}\n{exception}")



@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    print(f"Discord.py API version: {discord.__version__}")
    print(f"Python version: {platform.python_version()}")
    print(f"Running on: {platform.system()} {platform.release()} ({os.name})")
    print("-------------------")

    
bot.run(TOKEN)

