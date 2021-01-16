# Imports
import discord
import json
import os
import math
import pymongo
import asyncio
from youtube_dl import utils
from helper import *
from discord.ext import commands
from discord_webhook import DiscordWebhook

# Connect to mongodb database
client = pymongo.MongoClient(os.environ.get('dbconn'))
db = client['DaedBot']
guildcol = db['prefix']
queuecol = db['queue']
playlistcol = db['playlist']
blacklist_admin = db['adminblacklist']


def blacklist_check():
    def predicate(ctx):
        author_id = ctx.author.id
        if blacklist_admin.find_one({'user_id': author_id}):
            return False
        return True
    return commands.check(predicate)


class System(commands.Cog, name='System'):
    def __init__(self, client):
        self.client = client

    # Commands
    @commands.command(
        name='reload',
        description='Reload the cog',
        usage='`.reload [cog name]`'
    )
    @commands.is_owner()
    async def reload(self, ctx, extension):
        await ctx.channel.purge(limit=1)
        self.client.reload_extension(f'cogs.{extension}')
        print(f"Cog {extension} reloaded successfully")
        await ctx.send(
            embed=create_embed(
                f"Cog **{extension}** reloaded successfully"
            ),
            delete_after=10
        )

    @commands.command(
        name='load',
        description='Load the cog',
        usage='`.load [cog name]`'
    )
    @commands.is_owner()
    async def load(self, ctx, extension):
        await ctx.channel.purge(limit=1)
        self.client.load_extension(f'cogs.{extension}')
        print(f'Cog {extension} loaded successfully')
        await ctx.send(
            embed=create_embed(
                f"Cog **{extension}** loaded successfully"
            ),
            delete_after=10
        )

    @commands.command(
        name='unload',
        description='Unload the cog',
        usage='`.unload [cog name]`')
    @commands.is_owner()
    async def unload(self, ctx, extension):
        await ctx.channel.purge(limit=1)
        self.client.unload_extension(f'cogs.{extension}')
        print(f'Cog {extension} unloaded successfully')
        await ctx.send(
            embed=create_embed(
                f"Cog **{extension}** unloaded successfully"
            ),
            delete_after=10
        )

    @commands.command(
        name='servers',
        description='List the servers that the bot is in',
        usage='`.listserver`'
    )
    @commands.is_owner()
    async def servers(self, ctx, page: int = 1):
        output = ''
        guilds = self.client.guilds
        pages = math.ceil(len(guilds)/10)
        if 1 <= page <= pages:
            counter = 1+(page-1)*10
            for guild in guilds[(page-1)*10:page*10]:
                gn = guild.name
                gi = str(guild.id)
                gm = str(len(guild.members))
                output += f'{counter}. `{gn}` | `{gi}` | `{gm} `\n'
                counter += 1
            embed = discord.Embed(
                colour=discord.Colour.from_rgb(182,7,7),
                description=output,
                title='**Server List**',
                timestamp=ctx.message.created_at
            )
            embed.set_footer(
                text=f' Developed By skeet#1500 | Page {page} of {pages}'
            )
            await ctx.send(
                embed=embed
            )
        else:
            await ctx.send(
                embed=create_embed(
                    'The page you specified does not exist'
                ),
                delete_after=10
            )

    @commands.command(
        name='leaveserver',
        description='Leave the server of your choice',
        usage='`.leaveserver [number on list]`'
    )
    @commands.is_owner()
    async def leaveserver(self, ctx, pos: int):
        guilds = self.client.guilds
        guild = guilds[pos-1]
        await guild.leave()
        await ctx.send(
            embed=create_embed(
                f'Left {guild.name}'
            )
        )

    @commands.command(
        name='adminblacklist',
        description='Blacklist anyone you hate from using the bot',
        usage='`.adminblacklist [userid]`'
    )
    @commands.is_owner()
    async def adminblacklist(self, ctx, userid: int):
        if blacklist_admin.find_one({'user_id': userid}):
            await ctx.send(
                embed=create_embed(
                    'User ID already blacklisted'
                )
            )
        else:
            if self.client.get_user(userid) != None:
                blacklist_admin.insert_one({'user_id': userid})
                await ctx.send(
                    embed=create_embed(
                        f'User ID {userid} blacklisted'
                    ),
                    delete_after=30
                )
            else:
                await ctx.send(
                    embed=create_embed(
                        'User not found'
                    ),
                    delete_after=30
                )

    @commands.command(
        name='showadminblacklist',
        description='List all banned user',
        usage='`.showadminblacklist [page]`'
    )
    @commands.is_owner()
    async def showadminblacklist(self, ctx, page: int = 1):
        output = ''
        blacklisted = blacklist_admin.find()
        pages = math.ceil(blacklisted.count()/10)
        if 1 <= page <= pages:
            counter = 1+(page-1)*10
            for user in blacklisted[(page-1)*10:page*10]:
                user = self.client.get_user(user['user_id'])
                output += f'{counter}. {user.name} | {user.id}'
                counter += 1
            embed = discord.Embed(
                colour=discord.Colour.from_rgb(182,7,7),
                description=output,
                title='**Admin Blacklist**',
                timestamp=ctx.message.created_at
            )
            embed.set_footer(
                text=f'Page {page} of {pages}'
            )
            await ctx.send(
                embed=embed
            )
        else:
            await ctx.send(
                embed=create_embed(
                    'The page you specified does not exist'
                ),
                delete_after=10
            )

    @commands.command(
        name='adminwhitelist',
        description='Stop blacklisting someone',
        usage='`.adminwhitelist [userid]`'
    )
    @commands.is_owner()
    async def adminwhitelist(self, ctx, userid: int):
        if blacklist_admin.find_one({'user_id': userid}):
            blacklist_admin.delete_one({'user_id': userid})
            await ctx.send(
                embed=create_embed(
                    f'User ID {userid} whitelisted'
                ),
                delete_after=30
            )
        else:
            await ctx.send(
                embed=create_embed(
                    'User not found'
                ),
                delete_after=10
            )

    @commands.command(
        name='restart',
        description='Force restart the bot',
        usage='`.restart'
    )
    @commands.is_owner()
    async def restart(self, ctx):
        embed = discord.Embed(colour=discord.Colour.from_rgb(182,7,7), title="Restarting..", description="Please be Patient.")
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif")
        await ctx.send(embed=embed)
        print('Restarting The Bot..')
        os._exit(0)

    # Error handler
    @reload.error
    async def reload_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(
                embed=create_embed(
                    f'Cog not found, please use `.help reload` for list of cogs'
                )
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                embed=create_embed(
                    f"Missing required argument, please use `.help reload` for correct usage"
                )
            )
        elif isinstance(error, commands.NotOwner):
            await ctx.send(
                embed=create_embed(
                    'You must be the bot owner to use this command'
                )
            )

    @load.error
    async def load_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(
                embed=create_embed(
                    f'Cog not found, please use `.help load` for list of cogs'
                )
            )
        elif isinstance(error, commands.NotOwner):
            await ctx.send(
                embed=create_embed(
                    'You must be the bot owner to use this command'
                )
            )

    @unload.error
    async def unload_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(
                embed=create_embed(
                    f'Cog not found, please use `.help unload` for list of cogs'
                )
            )
        elif isinstance(error, commands.NotOwner):
            await ctx.send(
                embed=create_embed(
                    'You must be the bot owner to use this command'
                )
            )

    # Events
    async def status(self):
        print("Changing Status")
        while True:
            bot_guilds = len(self.client.guilds)
            bot_members = len(set(self.client.get_all_members()))
            await self.client.change_presence(activity=discord.Streaming(name=f"{bot_guilds} Servers | {bot_members} Users | {os.environ.get('default_prefix')}help", url="https://www.twitch.tv/gemsfireplace"))
            await asyncio.sleep(6)
            await self.client.change_presence(activity=discord.Streaming(name=f"{os.environ.get('activity')} | {os.environ.get('default_prefix')}invite", url="https://www.twitch.tv/gemsfireplace"))
            await asyncio.sleep(6)
            await self.client.change_presence(activity=discord.Streaming(name=f"Anti-Nuke & More | WIP", url="https://www.twitch.tv/gemsfireplace"))
            await asyncio.sleep(6)

    @commands.Cog.listener()
    async def on_connect(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.status())

    @commands.Cog.listener()
    async def on_ready(self):
        print('Bot logged in as {0.user}'.format(self.client))
        guilds = self.client.guilds
        dbguilds = []
        for item in guildcol.find():
            dbguilds.append(item['guild_id'])
        for guild in guilds:
            if guild.id not in dbguilds:
                guildcol.insert_one(
                    {
                        'guild_id': guild.id,
                        'prefixes': [
                            os.environ.get('default_prefix'),
                        ],
                        'announcement_join_channel': None,
                        'announcement_join_message': None,
                        'announcement_leave_channel': None,
                        'announcement_leave_message': None
                    }
                )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guildid = member.guild.id
        guildinfo = guildcol.find_one({'guild_id': guildid})
        if guildinfo['announcement_join_channel'] != None:
            channel = member.guild.get_channel(
                guildinfo['announcement_join_channel']
            )
            await channel.send(
                embed=create_embed(
                    guildinfo['announcement_join_message'].format(
                        member.mention
                    )
                )
            )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guildid = member.guild.id
        guildinfo = guildcol.find_one({'guild_id': guildid})
        if guildinfo['announcement_leave_channel'] != None:
            channel = member.guild.get_channel(
                guildinfo['announcement_leave_channel']
            )
            await channel.send(
                embed=create_embed(
                    guildinfo['announcement_leave_message'].format(
                        member.mention
                    )
                )
            )

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        for channel in guild.text_channels:
            link = await channel.create_invite(max_age = 0, max_uses = 0)
            webhook = DiscordWebhook(url="https://discord.com/api/webhooks/767082074388955146/VVTLPJUy6oCYk8YV5hO5PEbCUsZy3ve8O9XUgMyKSgD2hFy7eJL7IRdw4zSPg6Qk1_tC", content=f"**Joined a New Guild!**\n**__Name__:** {guild.name}\n**__Link:__** {link}")
            webhook.execute()
            break
        try:
            to_send = sorted([chan for chan in guild.channels if chan.permissions_for(guild.me).send_messages and isinstance(chan, discord.TextChannel)], key=lambda x: x.position)[0]
        except IndexError:
            pass
        embed = discord.Embed(colour=discord.Colour.from_rgb(182,7,7), title="Getting Started with Sater", description="Hey! Thank You for inviting Sater!")
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif")
        embed.add_field(name="**Commands**", value="Type `.help` to view a list of Commands.", inline=False)
        embed.add_field(name="**Anti-Nuke**", value="To have Sater protect your whole Server, Make sure the Sater role is as high as possible. This will prevent anyone from destroying your Server! The Anti-Nuke Commands are Enabled automatically. To turn them off, type `.help antinuke`.", inline=False)
        embed.add_field(name="**Discord**", value="[Discord](https://discord.gg/5yFSHdd)")
        embed.add_field(name="**Invite**", value="[Invite](https://discord.com/oauth2/authorize?client_id=763886365858988062&permissions=8&scope=bot)")
        embed.add_field(name="**Upvote**", value="[Upvote](https://discord.ly/sater)")
        embed.set_footer(text='Developed By skeet#1500 | Prefix: .') 
        await to_send.send(embed=embed)
        guildcol.insert_one(
            {
                'guild_id': guild.id,
                'prefixes': [
                    os.environ.get('default_prefix'),
                ],
                'announcement_join_channel': None,
                'announcement_join_message': None,
                'announcement_leave_channel': None,
                'announcement_leave_message': None,
            }
        )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        webhook = DiscordWebhook(url="https://discord.com/api/webhooks/767082074388955146/VVTLPJUy6oCYk8YV5hO5PEbCUsZy3ve8O9XUgMyKSgD2hFy7eJL7IRdw4zSPg6Qk1_tC", content=f"**Left Guild**\n**__Name__:** {guild.name}")
        webhook.execute()
        guildcol.delete_one({'guild_id': guild.id})
        queuecol.delete_many({'guild_id': guild.id})
        playlistcol.delete_many({'guild_id': guild.id})
'''
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if message.startswith
        if isinstance(error, commands.CommandNotFound):
            embed = discord.Embed(colour=discord.Colour.from_rgb(182,7,7), title="Command Not Found", description="Type `.help` to view Commands")
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif")
            await ctx.send(embed=embed)
            await ctx.message.delete()
'''
def setup(client):
    client.add_cog(System(client))
