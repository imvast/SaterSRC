import discord
import time
import pymongo
import os
import re
from datetime import datetime
from helper import *
from discord.ext import commands
import asyncio


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

class Management(commands.Cog, name='Management'):
    def __init__(self, client):
        self.client = client
        
    @commands.command(
    name='setprefix',
    description='Set the custom prefix for the server',
    usage='`.setprefix [new prefix]`'
    )
    
    @blacklist_check()
    @commands.has_guild_permissions(manage_guild=True)
    async def setprefix(self, ctx, new_prefix: str):
        info = guildcol.find_one(
            {'guild_id': ctx.guild.id}
        )
        prefixes = info['prefixes']
        prefixes[0] = new_prefix
        guildcol.update_one(
            {'guild_id': ctx.guild.id},
            {
                '$set': {
                    'prefixes': prefixes
                }
            }
        )
        await ctx.send(
            embed=create_embed(
                f'Prefix changed to {new_prefix}'
            )
        )
        
    @commands.command(
    name='set_leave',
    description='Sets the channel for member leave and the announcement message',
    usage='`.set_leave [#channel] [message]`'
    )
    @blacklist_check()
    @commands.has_guild_permissions(manage_guild=True)
    async def set_leave(self, ctx, channel: discord.TextChannel, *, message: str):
        if re.search('\{\}', message) == None:
            await ctx.send(
                embed=create_embed(
                    'Your message must contain "{}" to specify where to put the member name'
                ),
                delete_after=10
            )
        else:
            guildcol.update_one(
                {'guild_id': ctx.guild.id},
                {
                    '$set': {
                        'announcement_leave_channel': channel.id,
                        'announcement_leave_message': message
                    }
                }
            )
            await ctx.send(
                embed=create_embed(
                    f'Leave message set to "{message}" at {channel.mention}'
                ),
                delete_after=60
            )
            
    @commands.command(
    name='set_join',
    description='Sets the channel for member join and the announcement message',
    usage='`.set_join [#channel] [message]`'
    )
    @blacklist_check()
    @commands.has_guild_permissions(manage_guild=True)
    async def set_join(self, ctx, channel: discord.TextChannel, *, message: str):
        if re.search('\{\}', message) == None:
            await ctx.send(
                embed=create_embed(
                    'Your message must contain "{}" to specify where to put the member name'
                ),
                delete_after=10
            )
        else:
            guildcol.update_one(
                {'guild_id': ctx.guild.id},
                {
                    '$set': {
                        'announcement_join_channel': channel.id,
                        'announcement_join_message': message
                    }
                }
            )
            await ctx.send(
                embed=create_embed(
                    f'Join message set to "{message}" at {channel.mention}'
                ),
                delete_after=60
            )

    @commands.command(
        name="slowmode",
        description="Sets a slowmode for the channel.",
        usage="`.slowmode <seconds>`",
        aliases=['slowmo']
    )
    @commands.has_permissions(manage_messages=True)
    async def slowmode(self, ctx, seconds: int=0):
        if seconds > 120:
            return await ctx.send(embed=create_embed("Amount can't be over 120 seconds"))
        if seconds is 0:
            await ctx.channel.edit(slowmode_delay=seconds)
            await ctx.send(embed=create_embed("**Slowmode is off for this channel**"))
        else:
            if seconds is 1:
                numofsecs = "second"
            else:    
                numofsecs = "seconds"
            await ctx.channel.edit(slowmode_delay=seconds)
            await ctx.send(embed=create_embed(f"**Set the channel slow mode delay to `{seconds}` {numofsecs}\nTo turn this off, do .slowmode**"))


    @setprefix.error
    async def setprefix_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'You do not have the {"".join(error.missing_perms)} permission for this command'
                )
            )

def setup(client):
    client.add_cog(Management(client))
