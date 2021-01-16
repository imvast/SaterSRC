import discord
import time
import pymongo
import os
import re
from datetime import datetime
from helper import *
from discord.ext import commands

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
  
class Utility(commands.Cog, name='Utility'):
    def __init__(self, client):
        self.client = client
                  
    @commands.command(
        name='userinfo',
        aliases=['whois', 'profile'],
        description='Displays the user info',
        usage='`.userinfo`'
    )
    @blacklist_check()
    async def userinfo(self, ctx, member: discord.Member = None):
        if member == None:
            member = ctx.author
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            timestamp=ctx.message.created_at
        )
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_author(
            name=f'User Info: {member.display_name}',
            icon_url=member.avatar_url
        )
        embed.add_field(
            name='👤 **Account Info**',
            value=f"Currently {member.status}\nAccount Created on {member.created_at.strftime('%d %b %Y %H:%M')}\nAbout {(datetime.now()-member.created_at).days} days ago.",
            inline=False
        )
        if member.premium_since == None:
            embed.add_field(
                name='💻 **Server Info**',
                value=f"Joined Server on {member.joined_at.strftime('%d %b %Y %H:%M')}\nAbout {(datetime.now()-member.joined_at).days} days ago.\nNot boosting the server",
                inline=False
            )
        else:
            embed.add_field(
                name='💻 **Server Info**',
                value=f"Joined Server on {member.joined_at.strftime('%d %b %Y %H:%M')}\nAbout {(datetime.now()-member.joined_at).days} days ago.\nBoosting the server",
                inline=False
            )
        role_str = ''
        for role in member.roles:
            role_str += str(role.mention)+', '
        embed.add_field(
            name="🏷 **Member's Roles**",
            value=role_str,
            inline=False
        )
        embed.set_footer(
            text=f'ID: {member.id}'
        )
        await ctx.send(embed=embed)
     
    @commands.command(
        name='avatar',
        aliases=['photo', 'pfp', 'av'],
        description='Shows the user photo',
        usage='`.avatar [member]`'
    )
    @blacklist_check()
    async def avatar(self, ctx, member: discord.Member = None):
        if member == None:
            member = ctx.author
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            title=f"**{member.display_name}'s Avatar**",
            timestamp=ctx.message.created_at
        )
        embed.set_image(url='{}'.format(member.avatar_url))
        embed.set_footer(text="Developed By skeet#1500")
        await ctx.send(embed=embed)

    @commands.command(
        name='serverinfo',
        description='Displays the server info',
        aliases=['svinfo', ],
        usage='`.serverinfo`',
    )
    @blacklist_check()
    async def serverinfo(self, ctx):
        guild = ctx.message.guild
        online = len([member.status for member in guild.members
                      if member.status == discord.Status.online or
                      member.status == discord.Status.idle or member.status == discord.Status.do_not_disturb])
        total_users = len(guild.members)
        total_bots = len([member for member in guild.members if member.bot == True])
        total_humans = total_users - total_bots
        text_channels = len(ctx.guild.text_channels)
        voice_channels = len(ctx.guild.voice_channels)
        passed = (ctx.message.created_at - guild.created_at).days
        created_at = ("Created on {}. Over {} days ago."
                      "".format(guild.created_at.strftime("%d %b %Y %H:%M"),
                                passed))

        embed = discord.Embed(description=created_at, colour=discord.Colour.from_rgb(182,7,7))
        embed.add_field(name="🌍 **Region**", value=str(guild.region), inline=False)
        embed.add_field(name="👥 **Members**", value="{}/{}".format(online, total_users), inline=False)
        embed.add_field(name="🧍 **Humans**", value=total_humans, inline=False)
        embed.add_field(name="🤖 **Bots**", value=total_bots, inline=False)
        embed.add_field(name="💬 **Text Channels**", value=text_channels, inline=False)
        embed.add_field(name="🔊 **Voice Channels**", value=voice_channels, inline=False)
        embed.add_field(name="🏷 **Roles**", value=len(guild.roles), inline=False)
        embed.add_field(name="👑 **Owner**", value=str(guild.owner), inline=False)
        embed.set_footer(text=f"Guild ID:{str(guild.id)}")

        if guild.icon_url:
            embed.set_author(name=guild.name, url=guild.icon_url)
            embed.set_thumbnail(url=guild.icon_url)
            await ctx.send(embed=embed)
        else:
            embed.set_author(name=guild.name)
            await ctx.send(embed=embed)
    
    @commands.command(
        name="roleinfo",
        description="Shows you the info of a role.",
        usage="`.roleinfo [role]`"
    )
    async def roleinfo(self, ctx, *, role: discord.Role):
        '''Shows information about a role'''
        guild = ctx.guild

        since_created = (ctx.message.created_at - role.created_at).days
        role_created = role.created_at.strftime("%d %b %Y %H:%M")
        created_on = "{} ({} days ago!)".format(role_created, since_created)
        members = ''
        i = 0
        for user in role.members:
            members += f'{user.name}, '
            i+=1
            if i > 30:
                break
                
        em = discord.Embed(colour=discord.Colour.from_rgb(182,7,7))
        em.set_author(name=role.name)
        em.add_field(name="Users", value=len(role.members))
        em.add_field(name="Mentionable", value=role.mentionable)
        em.add_field(name="Hoist", value=role.hoist)
        em.add_field(name="Position", value=role.position)
        em.add_field(name="Managed", value=role.managed)
        em.add_field(name="Colour", value=colour)
        em.add_field(name='Creation Date', value=created_on)
        em.add_field(name='Members', value=members[:-2], inline=False)
        em.set_footer(text=f'Role ID: {role.id}')

        await ctx.send(embed=em)

    
    # Error handler
    @avatar.error
    async def avatar_error(self, ctx, error):
        await ctx.send(
            embed=create_embed(
                f"Couldn't get the users avatar. Make sure you typed their name correctly or mention them"
            )
        )
    
    @roleinfo.error
    async def roleinfo_error(self, ctx, error):
        await ctx.send(
            embed=create_embed(
                f"Couldn't get the info of that role. Make sure you typed it correctly or mention it"
            )
        )
     
    @serverinfo.error
    async def serverinfo_error(self, ctx, error):
        await ctx.send(
            embed=create_embed(
                f"Couldn't get the server info. Please try again"
            )
        )
        
    @userinfo.error
    async def userinfo_error(self, ctx, error):
        await ctx.send(
            embed=create_embed(
                f"Couldn't get the users info Make sure you typed their name correctly or mention them"
            )
        )
        
def setup(client):
    client.add_cog(Utility(client))


