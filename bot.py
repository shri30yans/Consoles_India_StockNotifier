import os, sys, discord, platform, random
from discord.ext import commands, tasks
from utils.help import EmbedHelpCommand
import config
import asyncpg

if not os.path.isfile("config.py"):
    sys.exit("'config.py' not found! Please add it and try again.")
else:
    import config

colourlist = config.embed_colours


async def get_prefix(bot, message):
    if message.guild:
        prefixes_list = (
            config.server_prefixes.get(message.guild.id) or config.default_prefixes[0]
        )
    else:
        prefixes_list = config.default_prefixes[0]

    prefixes = ", ".join(prefixes_list)
    if prefixes:
        return commands.when_mentioned_or(prefixes)(bot, message)
    else:
        return commands.when_mentioned_or(config.default_prefixes[0])(bot, message)


intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix=get_prefix,
    strip_after_prefix = True,
    case_insensitive=True,
    intents=intents,
    help_command=EmbedHelpCommand(),
)
TOKEN = config.TOKEN


@tasks.loop(minutes=15)
async def status_update():
    await bot.wait_until_ready()
    list_of_statuses = [
        discord.Activity(type=discord.ActivityType.watching, name=f"How to get a PS5?"),
        discord.Activity(type=discord.ActivityType.watching, name=f"How to get a XSX?"),
        discord.Activity(type=discord.ActivityType.watching, name=f"PS5 stock when?"),
        discord.Activity(type=discord.ActivityType.playing, name=f"Astro's Playroom"),
        discord.Activity(type=discord.ActivityType.playing, name=f"Bloodborne"),
        discord.Activity(type=discord.ActivityType.playing, name=f"God of War"),
    ]

    activity = random.choice(list_of_statuses)
    await bot.change_presence(status=discord.Status.online, activity=activity)


status_update.start()

if config.mode == "Basic":
    cogs = config.BASIC_COGS
else:
    cogs = config.STARTUP_COGS

for extension in cogs:
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

    
    print(f"Notifications are set to {config.notify}")
    print(f"Scrapping mode is set to {config.mode}")
    
    print("-------------------")


   


DATABASE_DICT = config.DATABASE_DICT


async def connection_pool():
    bot.pool = await asyncpg.create_pool(
        database=DATABASE_DICT["database"],
        user=DATABASE_DICT["user"],
        password=DATABASE_DICT["password"],
        host=DATABASE_DICT["host"],
        port=DATABASE_DICT["port"],
        max_inactive_connection_lifetime=5,
    )


bot.loop.run_until_complete(connection_pool())
bot.run(TOKEN)
