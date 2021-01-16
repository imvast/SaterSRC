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

class Information(commands.Cog, name='Information'):
    def __init__(self, client):
        self.client = client
    
    @commands.command(
        name='ping',
        description='Check the latency',
        usage='`.ping`'
    )
    async def ping(self, ctx):
        time = int(self.client.latency * 1000)
        embed = discord.Embed(
        title = "🕐 Ping",
        colour = discord.Colour.from_rgb(182,7,7),
        description = f"{time}ms."
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif")
        await ctx.send(embed=embed)
        
    @commands.command(
        name="invite",
        description="Sends the bot's invite link.",
        usage="`.invite`"
    )
    async def invite(self, ctx):
        embed = discord.Embed(
        title = "🔗 Invite Link",
        colour = discord.Colour.from_rgb(182,7,7),
        description = "[Click Here](https://discord.com/api/oauth2/authorize?client_id=763886365858988062&permissions=8&scope=bot)"
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif")
        await ctx.send(embed=embed)
    
    @commands.command(
        name="upvote",
        description="Sends the bot's upvote link.",
        usage="`.upvote`"
    )
    async def upvote(self, ctx):
        embed = discord.Embed(
        title = "📈 Upvote",
        colour = discord.Colour.from_rgb(182,7,7),
        description = "[Click Here](https://discord.ly/sater)"
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif")
        await ctx.send(embed=embed)
    
    @commands.command(
        name="support",
        description="Sends the bot's support server link.",
        usage="`.support`"
    )
    async def support(self, ctx):
        embed = discord.Embed(
        title = "🌐 Support",
        colour = discord.Colour.from_rgb(182,7,7),
        description = "[Click Here](https://discord.gg/MS4zxwx)"
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif")
        await ctx.send(embed=embed)

    @commands.command(
        name="info",
        description="Shows information about the bot",
        usage="`.info`"
    )
    async def info(self, ctx):
        bot_guilds = len(self.client.guilds)
        bot_members = len(set(self.client.get_all_members()))
        bot_ping = int(self.client.latency * 1000)
        bot_invite = "[Click Here](https://discord.com/api/oauth2/authorize?client_id=763886365858988062&permissions=8&scope=bot)"
        bot_owner = "[skeet#1500](https://discord.com/users/714581739279876098/profile)"
        bot_discord = "[Click Here](https://discord.gg/5yFSHdd)"
        bot_upvote = "[Click Here](https://discord.ly/sater)"
        embed = discord.Embed(colour=discord.Colour.from_rgb(182,7,7), description="All the information about the bot.", timestamp=ctx.message.created_at)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif")
        embed.set_footer(text="Developed By skeet#1500")
        embed.set_author(name="Sater Information", icon_url=ctx.author.avatar_url)
        embed.add_field(name="💻 **Guilds**", value=f"{bot_guilds}", inline=False)
        embed.add_field(name="👥 **Users**", value=f"{bot_members}", inline=False)
        embed.add_field(name="🕐 **Ping**", value=f"{bot_ping}ms.", inline=False)
        embed.add_field(name="🔗 **Invite**", value=f"{bot_invite}", inline=False)
        embed.add_field(name="👑 **Owner**", value=f"{bot_owner}", inline=False)
        embed.add_field(name="🌐 **Support**", value=f"{bot_discord}", inline=False)
        embed.add_field(name="📈 **Upvote**", value=f"{bot_upvote}", inline=False)
        await ctx.send(embed=embed)
        
def setup(client):
    client.add_cog(Information(client))
