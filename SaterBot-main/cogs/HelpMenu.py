# Imports
import discord
import pymongo
import os
from helper import *
from discord.ext import commands
from discord.utils import get

# Connect to mongodb database
client = pymongo.MongoClient(os.environ.get('dbconn'))
db = client['DaedBot']
guildcol = db['prefix']
queuecol = db['queue']
playlistcol = db['playlist']
    
class HelpMenu(commands.Cog, name='Help'):
    def __init__(self, client):
        self.client = client
    
    @commands.group(
        name='Help',
        description='The help command',
        invoke_without_command=True,
        aliases=['h', 'help']
    )
    async def help(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                colour=discord.Colour.from_rgb(182,7,7),
                description='**Use** `.help [module name]` **for more information**\n**[Support](https://discord.gg/MS4zxwx) • [Upvote](https://discord.ly/sater) • [Invite](https://discord.com/oauth2/authorize?client_id=763886365858988062&permissions=8&scope=bot)**',
                timestamp=ctx.message.created_at
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif"
            )
            embed.set_author(
                name='Sater Help Commands',
                icon_url=ctx.author.avatar_url
            )
            embed.add_field(
                name='🛠 **Moderation**',
                value='The Admin Commands',
                inline=False
            )
            embed.add_field(
                name='🎵 **Music**',
                value='The Music Commands',
                inline=False
            )
            embed.add_field(
                name='💼 **Management**',
                value='The Management Commands',
                inline=False
            )
            embed.add_field(
                name='🔍 **Utility**',
                value='The Utility Commands',
                inline=False
            )
            embed.add_field(
                name='📋 **Information**',
                value='The Information Commands',
                inline=False
            )
            embed.add_field(
                name='🎭 **Fun**',
                value='The Fun Commands',
                inline=False
            )
            embed.add_field(
                name='⚠️ **Anti Nuke**',
                value='The Anti Nuke Commands',
                inline=False
            )
            embed.add_field(
                name='**[Support](https://discord.gg/MS4zxwx) • [Upvote](https://discord.ly/sater) • [Invite](https://discord.com/oauth2/authorize?client_id=763886365858988062&permissions=8&scope=bot)**',
                value='',
                inline=False
            )
            extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
            embed.set_footer(
                text='Developed By skeet#1500 | Prefix: ' +
                ' and '.join(extras)
            )
            await ctx.send(embed=embed)

    @help.command(
        name='Moderation',
        aliases=['mod', 'moderation', 'MOD', 'MODERATION' ],
        description='Show list of administrative commands',
    )
    async def Moderation(self, ctx):
        cog = self.client.get_cog('Moderation')
        commands = cog.get_commands()
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            description='**List of administrative commands**\n\nUse `.help [command name]` for more information',
            timestamp=ctx.message.created_at
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif"
        )
        embed.set_author(
            name="Moderation",
            icon_url=ctx.author.avatar_url
        )
        extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
        embed.set_footer(
            text='Developed By skeet#1500 | Server Prefix: ' +
            ' and '.join(extras)
        )
        for command in commands:
            if command.aliases != []:
                alias_list = command.aliases
                temp_alias_list = []
                for i in range(len(alias_list)):
                    temp_alias_list.append(f'.'+alias_list[i])
                embed.add_field(
                    name=command.qualified_name,
                    value=f'Description: {command.description}\nUsage: {command.usage}\nAliases: `{", ".join(temp_alias_list)}`',
                    inline=False
                )
            else:
                embed.add_field(
                    name=command.qualified_name,
                    value=f'Description: {command.description}\nUsage: {command.usage}',
                    inline=False
                )
        await ctx.send(embed=embed)
        
       
    @help.command(
        name='Management',
        aliases=['manage', 'management', 'MANAGEMENT', 'MANAGE' ],
        description='Show list of administrative commands',
    )
    async def Management(self, ctx):
        cog = self.client.get_cog('Management')
        commands = cog.get_commands()
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            description='**List of management commands**\n\nUse `.help [command name]` for more information',
            timestamp=ctx.message.created_at
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif"
        )
        embed.set_author(
            name="Management",
            icon_url=ctx.author.avatar_url
        )
        extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
        embed.set_footer(
            text='Developed By skeet#1500 | Server Prefix: ' +
            ' and '.join(extras)
        )
        for command in commands:
            if command.aliases != []:
                alias_list = command.aliases
                temp_alias_list = []
                for i in range(len(alias_list)):
                    temp_alias_list.append(f'.'+alias_list[i])
                embed.add_field(
                    name=command.qualified_name,
                    value=f'Description: {command.description}\nUsage: {command.usage}\nAliases: `{", ".join(temp_alias_list)}`',
                    inline=False
                )
            else:
                embed.add_field(
                    name=command.qualified_name,
                    value=f'Description: {command.description}\nUsage: {command.usage}',
                    inline=False
                )
        await ctx.send(embed=embed)
        
    @help.command(
        name='Utility',
        aliases=['UTILITY', 'UTIL', 'util', 'utility' ],
        description='Show list of utility commands',
    )
    async def Utility(self, ctx):
        cog = self.client.get_cog('Utility')
        commands = cog.get_commands()
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            description='**List of utility commands**\n\nUse `.help [command name]` for more information',
            timestamp=ctx.message.created_at
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif"
        )
        embed.set_author(
            name="Utility",
            icon_url=ctx.author.avatar_url
        )
        extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
        embed.set_footer(
            text='Developed By skeet#1500 | Server Prefix: ' +
            ' and '.join(extras)
        )
        for command in commands:
            if command.aliases != []:
                alias_list = command.aliases
                temp_alias_list = []
                for i in range(len(alias_list)):
                    temp_alias_list.append(f'.'+alias_list[i])
                embed.add_field(
                    name=command.qualified_name,
                    value=f'Description: {command.description}\nUsage: {command.usage}\nAliases: `{", ".join(temp_alias_list)}`',
                    inline=False
                )
            else:
                embed.add_field(
                    name=command.qualified_name,
                    value=f'Description: {command.description}\nUsage: {command.usage}',
                    inline=False
                )
        await ctx.send(embed=embed)
    
    @help.command(
        name='Information',
        aliases=['inf', 'information', 'INF', 'INFORMATION' ],
        description='Show list of information commands',
    )
    async def Information(self, ctx):
        cog = self.client.get_cog('Information')
        commands = cog.get_commands()
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            description='**List of information commands**\n\nUse `.help [command name]` for more information',
            timestamp=ctx.message.created_at
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif"
        )
        embed.set_author(
            name="Information",
            icon_url=ctx.author.avatar_url
        )
        extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
        embed.set_footer(
            text='Developed By skeet#1500 | Server prefix: ' +
            ' and '.join(extras)
        )
        for command in commands:
            if command.aliases != []:
                alias_list = command.aliases
                temp_alias_list = []
                for i in range(len(alias_list)):
                    temp_alias_list.append(f'.'+alias_list[i])
                embed.add_field(
                    name=command.qualified_name,
                    value=f'Description: {command.description}\nUsage: {command.usage}\nAliases: `{", ".join(temp_alias_list)}`',
                    inline=False
                )
            else:
                embed.add_field(
                    name=command.qualified_name,
                    value=f'Description: {command.description}\nUsage: {command.usage}',
                    inline=False
                )
        await ctx.send(embed=embed)
        
    @help.command(
        name='Fun',
        aliases=['fun', 'FUN'],
        description='Show list of fun commands',
    )
    async def Fun(self, ctx):
        cog = self.client.get_cog('Fun')
        commands = cog.get_commands()
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            description='**List of fun commands**\n\nUse `.help [command name]` for more information',
            timestamp=ctx.message.created_at
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif"
        )
        embed.set_author(
            name="Fun",
            icon_url=ctx.author.avatar_url
        )
        extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
        embed.set_footer(
            text='Developed By skeet#1500 | Server Prefix: ' +
            ' and '.join(extras)
        )
        for command in commands:
            if command.aliases != []:
                alias_list = command.aliases
                temp_alias_list = []
                for i in range(len(alias_list)):
                    temp_alias_list.append(f'.'+alias_list[i])
                embed.add_field(
                    name=command.qualified_name,
                    value=f'Description: {command.description}\nUsage: {command.usage}\nAliases: `{", ".join(temp_alias_list)}`',
                    inline=False
                )
            else:
                embed.add_field(
                    name=command.qualified_name,
                    value=f'Description: {command.description}\nUsage: {command.usage}',
                    inline=False
                )
        await ctx.send(embed=embed)
    
    @help.command(
        name='AntiNuke',
        aliases=['anti', 'ANTINUKE', 'ANTI', 'antinuke' ],
        description='Show list of anti nuke commands',
    )
    async def AntiNuke(self, ctx):
        cog = self.client.get_cog('AntiNuke')
        commands = cog.get_commands()
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            description='**List of anti nuke commands**\n\nUse `.[command name]` for more information',
            timestamp=ctx.message.created_at
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif"
        )
        embed.set_author(
            name="Anti Nuke",
            icon_url=ctx.author.avatar_url
        )
        extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
        embed.set_footer(
            text='Developed By skeet#1500 | Server Prefix: ' +
            ' and '.join(extras)
        )
        for command in commands:
            if command.aliases != []:
                alias_list = command.aliases
                temp_alias_list = []
                for i in range(len(alias_list)):
                    temp_alias_list.append(f'.'+alias_list[i])
                embed.add_field(
                    name=command.qualified_name,
                    value=f'Description: {command.description}\nUsage: {command.usage}\nAliases: `{", ".join(temp_alias_list)}`',
                    inline=False
                )
            else:
                embed.add_field(
                    name=command.qualified_name,
                    value=f'Description: {command.description}\nUsage: {command.usage}',
                    inline=False
                )
        await ctx.send(embed=embed)
        
    @help.command(
        name='ping',
        description='How to use ping command'
    )
    async def help_ping(self, ctx):
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            description='Shows you the WebSocket heartbeat or latency of the Bot',
            timestamp=ctx.message.created_at,
        )
        embed.set_author(
            name='Ping'
        )
        embed.add_field(
            name='Usage',
            value='`.ping`: Show the bot latency',
            inline=False
        )
        embed.add_field(
            name='Examples',
            value='`.ping`',
            inline=False
        )
        extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
        embed.set_footer(
            text='Developed By skeet#1500 | Server prefix: ' +
            ' and '.join(extras)
        )
        await ctx.send(
            embed=embed
        )

    @help.command(
        name='clear',
        description='How to use the clear command',
        aliases=['purge']
    )
    async def help_clear(self, ctx):
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            description='Clear command, clear a specific number of command (defaults to 5)\nYou must have the manage message permission to use this command',
            timestamp=ctx.message.created_at
        )
        embed.set_author(
            name='Clear'
        )
        embed.add_field(
            name='Usage',
            value='`.clear [number of messages]`: clear a number of messages',
            inline=False
        )
        embed.add_field(
            name='Examples',
            value='`.clear`: deletes the latest 5 messages\n`.clear 10`: deletes the latest 10 messages',
            inline=False
        )
        extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
        embed.set_footer(
            text='Developed By skeet#1500 | Server Prefix: ' +
            ' and '.join(extras)
        )
        await ctx.send(
            embed=embed
        )

    @help.command(
        name='nuke',
        description='How to use the nuke command'
    )
    async def help_nuke(self, ctx):
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            description='Nuke command, deletes all message in a channel',
            timestamp=ctx.message.created_at
        )
        embed.set_author(
            name='Nuke'
        )
        embed.add_field(
            name='Usage',
            value='`.nuke`: nukes the channel, deletes all messages',
            inline=False
        )
        embed.add_field(
            name='Example',
            value='`.nuke`',
            inline=False
        )
        extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
        embed.set_footer(
            text='Developed By skeet#1500 | Server Prefix: ' +
            ' and '.join(extras)
        )
        await ctx.send(
            embed=embed
        )

    @help.command(
        name='kick',
        description='How to use the kick command',
    )
    async def help_kick(self, ctx):
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            description='Kick command, kicks a member out of the server',
            timestamp=ctx.message.created_at
        )
        embed.set_author(
            name='Kick'
        )
        embed.add_field(
            name='Usage',
            value='`.kick [member]`: kicks a member out of the server',
            inline=False
        )
        embed.add_field(
            name='Example',
            value='`.kick @abc`: abc kicked from server',
            inline=False
        )
        extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
        embed.set_footer(
            text='Developed By skeet#1500 | Server Prefix: ' +
            ' and '.join(extras)
        )
        await ctx.send(
            embed=embed
        )

    @help.command(
        name='ban',
        description='How to use the ban command',
    )
    async def help_ban(self, ctx):
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            description='Ban command, bans a member out of the server',
            timestamp=ctx.message.created_at
        )
        embed.set_author(
            name='Ban'
        )
        embed.add_field(
            name='Usage',
            value='`.ban [member]`: bans a member out of the server',
            inline=False
        )
        embed.add_field(
            name='Example',
            value='`.ban @abc`: abc banned from server',
            inline=False
        )
        extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
        embed.set_footer(
            text='Server Prefix: ' +
            ' and '.join(extras)
        )
        await ctx.send(
            embed=embed
        )

    @help.command(
        name='userinfo',
        description='How to use the userinfo command',
        aliases=['ui', ]
    )
    async def help_userinfo(self, ctx):
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            description='Userinfo command, shows the info of a member',
            timestamp=ctx.message.created_at
        )
        embed.set_author(
            name='Userinfo'
        )
        embed.add_field(
            name='Usage',
            value='`.userinfo [member]`: shows the info of the member',
            inline=False
        )
        embed.add_field(
            name='Example',
            value="`.userinfo`: shows your membership info\n`.userinfo @abc`: shows abc's membership info",
            inline=False
        )
        extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
        embed.set_footer(
            text='Server Prefix: ' +
            ' and '.join(extras)
        )
        await ctx.send(
            embed=embed
        )

    @help.command(
        name='setprefix',
        description='How to use the setprefix command',
    )
    async def help_setprefix(self, ctx):
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            description='Setprefix command, sets the custom prefix for the server',
            timestamp=ctx.message.created_at
        )
        embed.set_author(
            name='Setprefix'
        )
        embed.add_field(
            name='Usage',
            value='`.setprefix [new prefix]`: sets the custom prefix for the server',
            inline=False
        )
        embed.add_field(
            name='Example',
            value="`.setprefix ?`: changes the command prefix to '?'",
            inline=False
        )
        extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
        embed.set_footer(
            text='Server Prefix: ' +
            ' and '.join(extras)
        )
        await ctx.send(
            embed=embed
        )

    @help.command(
        name='Music',
        aliases=['music', ],
        description='Show list of music commands',
    )
    async def Music(self, ctx):
        cog = self.client.get_cog('Music')
        commands = cog.get_commands()
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            description='**List of music commands**\n\nUse `.help [command name]` for more information',
            timestamp=ctx.message.created_at
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif"
        )
        embed.set_author(
            name="Music",
            icon_url=ctx.author.avatar_url
        )
        extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
        embed.set_footer(
            text='Server Prefix: ' +
            ' and '.join(extras)
        )
        for command in commands:
            if command.aliases != []:
                alias_list = command.aliases
                temp_alias_list = []
                for i in range(len(alias_list)):
                    temp_alias_list.append(f'.'+alias_list[i])
                embed.add_field(
                    name=command.qualified_name,
                    value=f'Description: {command.description}\nUsage: {command.usage}\nAliases: `{", ".join(temp_alias_list)}`',
                    inline=False
                )
            else:
                embed.add_field(
                    name=command.qualified_name,
                    value=f'Description: {command.description}\nUsage: {command.usage}',
                    inline=False
                )
        await ctx.send(embed=embed)

    @help.command(
        name='join',
        description='How to use the join command',
        aliases=['j', 'connect']
    )
    async def help_join(self, ctx):
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            description='Setprefix command, sets the custom prefix for the server',
            timestamp=ctx.message.created_at
        )
        embed.set_author(
            name='Join'
        )
        embed.add_field(
            name='Usage',
            value='`.join`: connects to the voice channel that you are inside',
            inline=False
        )
        embed.add_field(
            name='Example',
            value="`.join`: Bot connected to voice channel",
            inline=False
        )
        extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
        embed.set_footer(
            text='Server Prefix: ' +
            ' and '.join(extras)
        )
        await ctx.send(
            embed=embed
        )

    @help.command(
        name='leave',
        description='How to use the leave command',
        aliases=['dc', 'disconnect']
    )
    async def help_leave(self, ctx):
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            description='Leave command, sets the custom prefix for the server',
            timestamp=ctx.message.created_at
        )
        embed.set_author(
            name='Leave'
        )
        embed.add_field(
            name='Usage',
            value='`.leave`: disconnect from the current voice channel',
            inline=False
        )
        embed.add_field(
            name='Example',
            value="`.leave`: Bot disconnected from voice channel",
            inline=False
        )
        extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
        embed.set_footer(
            text='Server Prefix: ' +
            ' and '.join(extras)
        )
        await ctx.send(
            embed=embed
        )

    @help.group(
        name='playlist',
        invoke_without_command=True,
        aliases=['pl', 'plist']
    )
    async def help_playlist(self, ctx):
        cog = self.client.get_cog('Music')
        commands = discord.utils.get(cog.get_commands(), name='playlist')
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(182,7,7),
            description='**List of playlist options**\n\nUse `.help playlist [option]` for more information',
            timestamp=ctx.message.created_at
        )
        extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
        embed.set_footer(
            text='Server Prefix: ' +
            ' and '.join(extras)
        )
        embed.add_field(
            name='playlist',
            value='Description: show list of available playlists in the server\nUsage: `.playlist`\nAliases: `.pl, .plist`'
        )
        for command in commands.commands:
            if command.aliases != []:
                alias_list = command.aliases
                temp_alias_list = []
                for i in range(len(alias_list)):
                    temp_alias_list.append(f'.'+alias_list[i])
                embed.add_field(
                    name=command.qualified_name,
                    value=f'Description: {command.description}\nUsage: {command.usage}\nAliases: `{", ".join(temp_alias_list)}`',
                    inline=False
                )
            else:
                embed.add_field(
                    name=command.qualified_name,
                    value=f'Description: {command.description}\nUsage: {command.usage}',
                    inline=False
                )
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(HelpMenu(client))
