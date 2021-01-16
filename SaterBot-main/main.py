# Imports
import discord
import pymongo
import os
import asyncio
from helper import *
from utils import default
from discord.ext import commands, tasks

# Load environmental variables
try:
    exec(open('variable.py').read())
except:
    print('shit does not work, abort mission')

# Connect to mongodb database
client = pymongo.MongoClient(os.environ.get('dbconn'))
db = client['DaedBot']
guildcol = db['prefix']
queuecol = db['queue']
playlistcol = db['playlist']
blacklist_admin = db['adminblacklist']


# Load custom prefixes
def get_prefix(client, message):
    extras = guildcol.find_one({'guild_id': message.guild.id})
    prefixes = extras['prefixes']
    return commands.when_mentioned_or(*prefixes)(client, message)


def blacklist_check():
    def predicate(ctx):
        author_id = ctx.author.id
        if blacklist_admin.find_one({'user_id': author_id}):
            return False
        return True
    return commands.check(predicate)


# Start the bot
client = commands.Bot(command_prefix=get_prefix, owner_id=int(os.environ.get('owner')), intents=discord.Intents.all())


# Automatically restarts the bot
@tasks.loop(hours=12, reconnect=True)
async def bot_restart():
    os._exit(0)


# Remove default help command
client.remove_command('help')


# Load up cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')


# Run the bot
client.run(os.environ.get('DISCORD_TOKEN'), reconnect=True)

