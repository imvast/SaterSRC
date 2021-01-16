# Imports
import discord
import time
import pymongo
import os
import re
import asyncio
from utils import permissions, default
from datetime import datetime
from helper import *
from discord.ext import commands


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


class Moderation(commands.Cog, name='Moderation'):
    def __init__(self, client):
        self.client = client
 
    # Commands            
    @commands.command(
        name='kick',
        description='Kick someone from the server',
        usage='`.kick [@user]`'
    )
    @blacklist_check()
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await ctx.message.delete()
        guild = ctx.guild
        if ctx.author == member:
            await ctx.send(
                embed=create_embed('You cannot kick yourself'), delete_after=10)
        elif ctx.author.top_role < member.top_role:
            await ctx.send(embed=create_embed(f"**You can't kick a member above you.**"))
        elif ctx.guild.owner == member:
            await ctx.send(
                embed=create_embed('You cannot kick the server owner'), delete_after=10)
        else:
            if reason == None:
                try:
                    try:
                        await member.send(embed=create_embed(f"**You have been kicked from {guild.name}**"))
                        await member.kick()
                        await ctx.send(embed=create_embed(f'**{member} was kicked**'))
                    except:
                        await member.kick()
                        await ctx.send(embed=create_embed(f'**{member} was kicked**'))
                except:
                    await ctx.send(embed=create_embed(f"**Couldn't kick that user.**"))
            else:
                try:
                    await member.send(embed=create_embed(f"**You have been kicked from {guild.name} | {reason}**"))
                    await member.kick(reason=reason)
                    await ctx.send(embed=create_embed(f'**{member} was kicked | {reason}**'))
                except:
                    await ctx.send(embed=create_embed(f"Couldn't kick that user.**"))
                
    @commands.command(
        name='ban',
        description='Bans mentioned user.',
        usage='`.ban [@user]`'
    )
    @blacklist_check()
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        await ctx.message.delete()
        guild = ctx.guild
        if ctx.author == member:
            await ctx.send(embed=create_embed('You cannot ban yourself'), delete_after=10)
        elif ctx.author.top_role < member.top_role:
            await ctx.send(embed=create_embed(f"**You can't ban a member above you.**"))
        elif ctx.guild.owner == member:
            await ctx.send(
                embed=create_embed('You cannot ban the server owner'), delete_after=10)
        else:
            if reason == None:
                try:
                    try:
                        await member.send(embed=create_embed(f"**You have been banned from {guild.name}**"))
                        await member.ban()
                        await ctx.send(embed=create_embed(f'**{member} was banned**'))
                    except:
                        await member.ban()
                        await ctx.send(embed=create_embed(f'**{member} was banned**'))
                except:
                    await ctx.send(embed=create_embed(f"**Couldn't ban that user.**"))
            else:
                try:
                    try:
                        await member.send(embed=create_embed(f"**You have been banned from {guild.name} | {reason}**"))
                        await member.ban(reason=reason)
                        await ctx.send(embed=create_embed(f'**{member} was banned | {reason}**'))
                    except:
                        await member.ban(reason=reason)
                        await ctx.send(embed=create_embed(f'**{member} was banned | {reason}**'))
                except:
                    await ctx.send(embed=create_embed(f"**Couldn't ban that user.**"))
                
    @commands.command(
        name='unban',
        description='Unbans the specified user.',
        usage='`.unban [@user]`'
    )
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, userid):
        await ctx.message.delete()
        if ctx.author == userid:
            await ctx.send(embed=embed_create(f"You cannot ban yourself"), delete_after=10)
        else: 
            try:
               user = discord.Object(id=userid)
               await ctx.guild.unban(user)
               await ctx.send(embed=create_embed(f"**{userid}** has been unbanned."))
            except:
               await ctx.send(embed=create_embed(f"Couldn't unban that user."))

    @commands.command(
        name='clear',
        description='Delete messages (default = 5)',
        aliases=['purge', ],
        usage='`.clear [number of messages]`'
    )
    @blacklist_check()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount=5):
        await ctx.channel.purge(limit=amount+1)
        
    @commands.command(
        name='nuke',
        description='Deletes all messages in a text channel',
        usage='`.nuke`'
    )
    @blacklist_check()
    @commands.cooldown(1, 30, commands.BucketType.channel)
    @commands.has_permissions(manage_channels=True)
    async def nuke(self, ctx, arg=None):
        await ctx.message.delete()
        if arg != None:
            await ctx.send(
                embed=create_embed('This command does not take in any other argument'), delete_after=10)
        else:
            counter = 0
            await ctx.send(embed=create_embed(f"Nuking {ctx.channel.name}..."))
            channel_info = [ctx.channel.category,
            ctx.channel.position]
            channel_id = ctx.channel.id
            await ctx.channel.clone()
            await ctx.channel.delete()
            new_channel = channel_info[0].text_channels[-1]
            await new_channel.edit(position=channel_info[1])
            embed = discord.Embed(colour=discord.Colour.from_rgb(182,7,7))
            embed.set_author(name=f"Successfully nuked this channel.", icon_url=ctx.author.avatar_url)
            embed.set_image(url="https://media.discordapp.net/attachments/720812237794574347/765218830418182204/200.gif?width=269&height=150")
            await new_channel.send(embed=embed)
            queue = queuecol.find_one(
            {'guild_id': ctx.guild.id})
            if queue['text_channel'] == channel_id:
                queuecol.update_one(
                    {'guild_id': ctx.guild.id},
                    {'$set': {'text_channel': new_channel.id}})
            else:
                pass
    
    @commands.command(
        name="addrole",
        description="Gives the mentioned user the specified role.",
        usage="`.addrole [@user] [role]`",
        aliases=["giverole"]
    )
    @commands.has_permissions(manage_roles=True)
    async def addrole(self, ctx, user : discord.Member, *, role : discord.Role):
        await ctx.message.delete()
        if ctx.author.top_role < role:
            await ctx.send(embed=create_embed(f"**You are not high enough to add that role.**"))
        elif ctx.author.top_role < user.top_role and ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_embed(f"**You can't add roles to a member above you.**"))
        else:
            try:
                await user.add_roles(role)
                await ctx.send(embed=create_embed(f"**Successfully Given {user.mention} `{role}`**"))
            except:
                await ctx.send(embed=create_embed(f"**Couldn't add roles to that user.**"))
            
    @commands.command(
        name="derole",
        description="Removes the mentioned user the specified role.",
        usage="`.derole [@user] [role]`",
        aliases=["removerole"]
    )
    @commands.has_permissions(manage_roles=True)
    async def derole(self, ctx, user : discord.Member, *, role : discord.Role):
        await ctx.message.delete()
        if ctx.author.top_role < role:
            await ctx.send(embed=create_embed(f"**You are not high enough to remove that role.**"))
        elif ctx.author.top_role < user.top_role or ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_embed(f"**You can't remove roles from a member above you.**"))
        else:
            try:
                await user.remove_roles(role)
                await ctx.send(embed=create_embed(f"**Successfully removed `{role}` from {user.mention}**"))
            except:
                await ctx.send(embed=create_embed(f"**Couldn't remove roles from that user.**"))
            
    
    @commands.command(
        name="softban",
        description="Softbans mentioned user.",
        usage="`.softban [@user] [reason]`",
        aliases=['sb']
    )
    @commands.has_permissions(ban_members=True)
    async def softban(self, ctx, user : discord.Member, *, reason=None):
        await ctx.message.delete()
        guild = ctx.guild
        if ctx.author.top_role > user.top_role or ctx.author == ctx.guild.owner:
            if user == ctx.author:
                return await ctx.send(embed=create_embed("**You can't softban yourself**"))
            elif reason == None:
                try:
                    try:
                        await user.send(embed=create_embed(f"**You have been softbanned from {guild.name}**"))
                        await ctx.send(embed=create_embed(f"**{user} was softbanned**"))
                        await user.ban()
                        await user.unban()
                    except:
                        await ctx.send(embed=create_embed(f"**{user} was softbanned | {reason}**"))
                        await user.ban()
                        await user.unban()
                except:
                    await ctx.send(embed=create_embed(f"**Couldn't softban that user.**"))
            else:
                try:
                    try:
                        await user.send(embed=create_embed(f"**You have been softbanned from {guild.name} | {reason}**"))
                        await ctx.send(embed=create_embed(f"**{user} was softbanned | {reason}**"))
                        await user.ban(reason=reason)
                        await user.unban(reason=reason)
                    except:
                        await ctx.send(embed=create_embed(f"**{user} was softbanned | {reason}**"))
                        await user.ban(reason=reason)
                        await user.unban(reason=reason)
                except:
                    await ctx.send(embed=create_embed(f"**Couldn't softban that user.**"))
    
    @commands.command(
        name="hackban",
        description="Bans a user thats not in the server.",
        usage="`.hackban [id] [reason]`"
    )
    async def hackban(self, ctx, userid, *, reason=None):
        await ctx.message.delete()
        try:
            userid = int(userid)
        except:
            await ctx.send(embed=create_embed('Invalid ID!'))
        
        try:
            await ctx.guild.ban(discord.Object(userid), reason=reason)
            await ctx.send(embed=create_embed(f"**{userid} has been banned. | {reason}**"))
        except:
            await ctx.send(embed=create_embed(f"**Couldn't Ban that user.**"))
    
    @commands.command(
        name="lockchan",
        description="Locks down a channel.",
        usage="`.lockchan [channel] [reason]`",
    )
    @commands.has_permissions(manage_channels=True)
    async def lockchan(self, ctx, channel:discord.TextChannel = None, *, reason=None):
        await ctx.message.delete()
        if channel is None: channel = ctx.channel
        try:
            await channel.set_permissions(ctx.guild.default_role, overwrite=discord.PermissionOverwrite(send_messages = False), reason=reason)
            await ctx.send(embed=create_embed(f"**#{channel}** has been locked. | **{reason}**"))
        except:
            await ctx.send(embed=create_embed(f"**This channel couldn't be locked.**"))
        else:
            pass

    @commands.command(
        name="lockserver",
        description="Locks down the server.",
        usage="`.lockserver`"
    )
    @commands.has_permissions(manage_channels=True)
    async def lockserver(self, ctx, server:discord.Guild = None, *, reason=None):
        await ctx.message.delete()
        if server is None: server = ctx.guild
        try:
            for channel in server.channels:
                await channel.set_permissions(ctx.guild.default_role, overwrite=discord.PermissionOverwrite(send_messages = False), reason=reason)
            await ctx.send(embed=create_embed(f"**{server} has been locked. | {reason}**"))
        except:
            await ctx.send(embed=create_embed(f"**Server couldn't be locked.**"))
        else:
            pass
    
    @commands.command(
        name="unlockserver",
        description="Unlocks the server.",
        usage="`.unlockserver`"
    )
    @commands.has_permissions(manage_channels=True)
    async def unlockserver(self, ctx, server:discord.Guild = None, *, reason=None):
        await ctx.message.delete()
        if server is None: server = ctx.guild
        try:
            for channel in server.channels:
                await channel.set_permissions(ctx.guild.default_role, overwrite=discord.PermissionOverwrite(send_messages = True), reason=reason)
            await ctx.send(embed=create_embed(f"**{server} has been unlocked. | {reason}**"))
        except:
            await ctx.send(embed=create_embed(f"**Server couldn't be unlocked.**"))
        else:
            pass
    
    
    @commands.command(
        name="unlockchan",
        description="Unlocks a channel.",
        usage="`.unlockchan [channel] [reason]`",
    )
    @commands.has_permissions(manage_channels=True)
    async def unlockchan(self, ctx, channel:discord.TextChannel = None, *, reason=None):
        await ctx.message.delete()
        if channel is None: channel = ctx.channel
        try:
            await channel.set_permissions(ctx.guild.default_role, overwrite=discord.PermissionOverwrite(send_messages = True), reason=reason)
            await ctx.send(embed=create_embed(f"**{channel} has been unlocked. | {reason}**"))
        except:
            await ctx.send(embed=create_embed(f"**This channel couldn't be unlocked.**"))
        else:
            pass
    
    @commands.command(
        name="mute",
        description="Mutes the mentioned user.",
        usage="`.mute [@user] [reason]`"
    )
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, reason: str = None):
        await ctx.message.delete()
        guild = ctx.guild
        muted_role = next((g for g in ctx.guild.roles if g.name == "Muted"), None)

        if not muted_role:
            return await ctx.send(embed=create_embed("Can't Find the **Muted** role."))
        else:
            try:
                try:
                    await member.send(embed=create_embed(f"**You have been muted in {guild.name} | {reason}**"))
                    await member.add_roles(muted_role, reason=default.responsible(ctx.author, reason))
                    await ctx.send(embed=create_embed(f'**{member} has been muted. | {reason}**'))
                except:
                    await member.add_roles(muted_role, reason=default.responsible(ctx.author, reason))
                    await ctx.send(embed=create_embed(f'**{member} has been muted. | {reason}**'))
            except:
                await ctx.send(embed=create_embed(f"**Couldn't Mute that user.**"))
    
    @commands.command(
        name="unmute",
        description="Unmutes the mentioned user.",
        usage="`.unmute [@user] [reason]`"
    )
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member, *, reason: str = None):
        await ctx.message.delete()
        guild = ctx.guild
        muted_role = next((g for g in ctx.guild.roles if g.name == "Muted"), None)
        if not muted_role:
            return await ctx.send(embed=create_embed("**{member} is not muted.**"))
        else:
            try:
                try:
                    await member.send(embed=create_embed(f"**You have been unmuted from {guild.name} | {reason}**"))
                    await member.remove_roles(muted_role, reason=default.responsible(ctx.author, reason))
                    await ctx.send(embed=create_embed(f'**{member} has been unmuted. | {reason}**'))
                except:
                    await member.remove_roles(muted_role, reason=default.responsible(ctx.author, reason))
                    await ctx.send(embed=create_embed(f'**{member} has been unmuted. | {reason}**'))
            except:
                await ctx.send(embed=create_embed(f"**Couldn't Unmute that user.**"))
            
    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'User Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'Bot Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
    
    @lockchan.error
    async def lockchan_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'User Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'Bot Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
    
    @lockserver.error
    async def lockserver_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'User Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'Bot Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
     
    @unlockchan.error
    async def unlockchan_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'User Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'Bot Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
    
    @unlockserver.error
    async def unlockserver_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'User Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'Bot Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )

    @addrole.error
    async def addrole_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'User Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'Bot Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=create_embed('Please Specify a Member.'))
    
    @derole.error
    async def derole_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'User Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'Bot Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=create_embed('Please Specify a Member.'))
    
    @unmute.error
    async def unmute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'User Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'Bot Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=create_embed('Please Specify a Member.'))
    
    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'User Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'Bot Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=create_embed('Please Specify a Member.'))
            
    @nuke.error
    async def nuke_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                embed=create_embed(
                    f'You can only send **1** nuke every **40 seconds**\nTime until next available nuke: {int(error.retry_after)}s'
                )
            )
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'User Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'Bot Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
  
    @hackban.error
    async def hackban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'User Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'Bot Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=create_embed('Please Specify a Member ID.'))
                                              
    @softban.error
    async def softban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'User Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'Bot Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=create_embed('Please Specify a Member.'))
    
    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'User Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'Bot Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=create_embed('Please Specify a Member.'))

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'User Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'Bot Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=create_embed('Please Specify a Member.'))
  

    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'User Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=create_embed(
                    f'Bot Missing Permissions: **{"".join(error.missing_perms)}**'
                )
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=create_embed('Please Specify a Member.'))

# Add cog
def setup(client):
    client.add_cog(Moderation(client))
