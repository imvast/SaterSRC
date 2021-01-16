import discord
import pymongo
import os
import asyncio
from discord.ext import commands, tasks
from helper import *

client = pymongo.MongoClient(os.environ.get('dbconn'))
db = client['DaedBot']
guildcol = db['prefix']
queuecol = db['queue']
playlistcol = db['playlist']
blacklist_admin = db['adminblacklist']

class AntiNuke(commands.Cog, name='AntiNuke'):
    def __init__(self, client):
        self.client = client
        self.client.antiBot = True
        self.client.antiBan = True     
        self.client.antiKick = True
        self.client.antiRole = True
        self.client.antiChannel = True
        self.client.antiRoleCreation = True
        self.client.antiChannelCreation = True

    @tasks.loop(seconds=30)
    async def clean_mods(self):
        await self.client.wait_until_ready()
        self.client.bans = {}
        self.client.kicks = {}
        self.client.channels = {}
        self.client.roles = {}
        self.client.channelscreated = {}
        self.client.rolescreated = {}
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot Is Ready")
        self.client.bans = {}
        self.client.kicks = {}
        self.client.channels = {}
        self.client.roles = {}
        self.client.channelscreated = {}
        self.client.rolescreated = {}
        self.client.whitelist = []
        self.clean_mods.start()

    @commands.Cog.listener()
    async def on_member_ban(self, guild, member):
        if self.client.antiBan == True:
            logs = await guild.audit_logs(limit=1, action=discord.AuditLogAction.ban).flatten()
            logs = logs[0]
            if logs.target.id != member.id or logs.user.id in self.client.whitelist: return
            if guild.id not in self.client.bans:
                self.client.bans[guild.id] = {}
            if logs.user.id not in self.client.bans[guild.id]:
                self.client.bans[guild.id][logs.user.id] = 1
            else:
                self.client.bans[guild.id][logs.user.id] += 1
            if self.client.bans[guild.id][logs.user.id] >= 5:
                await logs.user.ban(reason="Mass Banning")

    @commands.Cog.listener()
    async def on_member_kick(self, guild, member):
        if self.client.antiKick == True:
            logs = await guild.audit_logs(limit=1, action=discord.AuditLogAction.kick).flatten()
            logs = logs[0]
            if logs.target.id != member.id or logs.user.id in self.client.whitelist: return
            if guild.id not in self.client.kicks:
                self.client.kicks[guild.id] = {}
            if logs.user.id not in self.client.kicks[guild.id]:
                self.client.kicks[guild.id][logs.user.id] = 1
            else:
                self.client.kicks[guild.id][logs.user.id] += 1
            if self.client.kicks[guild.id][logs.user.id] >= 5:
                await logs.user.ban(reason="Mass Kicking")
 
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        if self.client.antiRole == True:
            guild = role.guild
            logs = await guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete).flatten()
            logs = logs[0]
            if logs.target.id != role.id or logs.user.id in self.client.whitelist: return
            if guild.id not in self.client.roles:
                self.client.roles[guild.id] = {}
            if logs.user.id not in self.client.roles[guild.id]:
                self.client.roles[guild.id][logs.user.id] = 1
            else:
                self.client.roles[guild.id][logs.user.id] += 1
            if self.client.roles[guild.id][logs.user.id] >= 5:
                await logs.user.ban(reason="Mass Role Deletion")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if self.client.antiChannel == True:
            guild = channel.guild
            logs = await guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete).flatten()
            logs = logs[0]
            if logs.target.id != channel.id or logs.user.id in self.client.whitelist: return
            if guild.id not in self.client.channels:
                self.client.channels[guild.id] = {}
            if logs.user.id not in self.client.channels[guild.id]:
                self.client.channels[guild.id][logs.user.id] = 1
            else:
                self.client.channels[guild.id][logs.user.id] += 1
            if self.client.channels[guild.id][logs.user.id] >= 5:
                await logs.user.ban(reason="Mass Channel Deletion")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if self.client.antiChannelCreation == True:
            guild = channel.guild
            logs = await guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create).flatten()
            logs = logs[0]
            if logs.target.id != channel.id or logs.user.id in self.client.whitelist: return
            if guild.id not in self.client.channelscreated:
                self.client.channelscreated[guild.id] = {}
            if logs.user.id not in self.client.channelscreated[guild.id]:
                self.client.channelscreated[guild.id][logs.user.id] = 1
            else:
                self.client.channelscreated[guild.id][logs.user.id] += 1
            if self.client.channelscreated[guild.id][logs.user.id] >= 5:
                await logs.user.ban(reason="Mass Channel Creation")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        if self.client.antiRoleCreation == True:
            guild = role.guild
            logs = await guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create).flatten()
            logs = logs[0]
            if logs.target.id != role.id or logs.user.id in self.client.whitelist: return
            if guild.id not in self.client.rolescreated:
                self.client.rolescreated[guild.id] = {}
            if logs.user.id not in self.client.rolescreated[guild.id]:
                self.client.rolescreated[guild.id][logs.user.id] = 1
            else:
                self.client.rolescreated[guild.id][logs.user.id] += 1
            if self.client.rolescreated[guild.id][logs.user.id] >= 5:
                await logs.user.ban(reason="Mass Role Creation")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if self.client.antiBot == True and member.bot == True:
            await member.ban(reason="Anti-Bot")

    @commands.group(
        name="antibot",
        description="Turns anti-bot on or off",
        invoke_without_command=True,
        usage="`.antibot on/off`"
    )
    async def antibot(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                colour=discord.Colour.from_rgb(182,7,7),
                description="Doesn't Allow Bots to Join the Server.",
                timestamp=ctx.message.created_at
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif"
            )
            embed.set_author(
                name='Anti-Bot Commands',
                icon_url=ctx.author.avatar_url
            )
            embed.add_field(
                name='**.antibot on**',
                value='Turns on Anti-Bot',
                inline=False
                )
            embed.add_field(
                name='**.antibot off**',
                value='Turns off Anti-Bot',
                inline=False
            )
            extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
            embed.set_footer(
                text='Developed By skeet#1500 | Server Prefix: ' +
                ' and '.join(extras)
            )
            await ctx.send(embed=embed)
        
    @antibot.command(name='on')
    async def antibot_on(self, ctx):
        await ctx.message.delete()
        if ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_embed('Only the Server Owner can use this Command.'))
        elif self.client.antiBot == True:
            await ctx.send(embed=create_embed('Anti-Bot is Already Enabled!'))
        else:
            self.client.antiBot = True
            await ctx.send(embed=create_embed('Anti-Bot Enabled!'))
    
    @antibot.command(name='off')
    async def antibot_off(self, ctx):
        await ctx.message.delete()
        if ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_embed('Only the Server Owner can use this Command.'))
        elif self.client.antiBot == False:
            await ctx.send(embed=create_embed('Anti-Bot is Already Disabled!'))
        else:
            self.client.antiBot = False
            await ctx.send(embed=create_embed('Anti-Bot Disabled!'))
            
    @commands.group(
        name="antiban",
        description="Turns Anti-Ban on or off.",
        invoke_without_command=True,
        usage="`.antiban on/off`"
    )
    async def antiban(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                colour=discord.Colour.from_rgb(182,7,7),
                description="Doesn't Allow Mass-Banning.",
                timestamp=ctx.message.created_at
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif"
            )
            embed.set_author(
                name='Anti-Ban Commands',
                icon_url=ctx.author.avatar_url
            )
            embed.add_field(
                name='**.antiban on**',
                value='Turns on Anti-Ban',
                inline=False
                )
            embed.add_field(
                name='**.antiban off**',
                value='Turns off Anti-Ban',
                inline=False
            )
            extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
            embed.set_footer(
                text='Developed By skeet#1500 | Server Prefix: ' +
                ' and '.join(extras)
            )
            await ctx.send(embed=embed)
        
    @antiban.command(name='on')
    async def antiban_on(self, ctx):
        await ctx.message.delete()
        if ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_embed('Only the Server Owner can use this Command.'))
        elif self.client.antiBan == True:
            await ctx.send(embed=create_embed('Anti-Ban is Already Enabled!'))
        else:
            self.client.antiBan = True
            await ctx.send(embed=create_embed('Anti-Ban Enabled!'))
    
    @antiban.command(name='off')
    async def antiban_off(self, ctx):
        await ctx.message.delete()
        if ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_embed('Only the Server Owner can use this Command.'))
        elif self.client.antiBan == False:
            await ctx.send(embed=create_embed('Anti-Ban is Already Disabled!'))
        else:
            self.client.antiBan = False
            await ctx.send(embed=create_embed('Anti-Ban Disabled!'))
    
    @commands.group(
        name="antikick",
        description="Turns Anti-Kick on or off.",
        invoke_without_command=True,
        usage="`.antikick on/off`"
    )
    async def antikick(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                colour=discord.Colour.from_rgb(182,7,7),
                description="Doesn't Allow Mass-Kicking.",
                timestamp=ctx.message.created_at
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif"
            )
            embed.set_author(
                name='Anti-Kick Commands',
                icon_url=ctx.author.avatar_url
            )
            embed.add_field(
                name='**.antikick on**',
                value='Turns on Anti-Kick',
                inline=False
                )
            embed.add_field(
                name='**.antikick off**',
                value='Turns off Anti-Kick',
                inline=False
            )
            extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
            embed.set_footer(
                text='Developed By skeet#1500 | Server Prefix: ' +
                ' and '.join(extras)
            )
            await ctx.send(embed=embed)
            
    @antikick.command(name='on')
    async def antikick_on(self, ctx):
        await ctx.message.delete()
        if ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_embed('Only the Server Owner can use this Command.'))
        elif self.client.antiKick == True:
            await ctx.send(embed=create_embed('Anti-Kick is Already Enabled!'))
        else:
            self.client.antiKick = True
            await ctx.send(embed=create_embed('Anti-Kick Enabled!'))
    
    @antikick.command(name='off')
    async def antikick_off(self, ctx):
        await ctx.message.delete()
        if ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_embed('Only the Server Owner can use this Command.'))
        elif self.client.antiKick == False:
            await ctx.send(embed=create_embed('Anti-Kick is Already Disabled!'))
        else:
            self.client.antiKick = False
            await ctx.send(embed=create_embed('Anti-Kick Disabled!'))
    
    @commands.group(
        name="antiroledel",
        description="Turns Anti-RoleDel on or off.",
        invoke_without_command=True,
        usage="`.antiroledel on/off`"
    )
    async def antiroledel(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                colour=discord.Colour.from_rgb(182,7,7),
                description="Doesn't Allow Mass Role Deletion.",
                timestamp=ctx.message.created_at
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif"
            )
            embed.set_author(
                name='Anti-RoleDel Commands',
                icon_url=ctx.author.avatar_url
            )
            embed.add_field(
                name='**.antiroledel on**',
                value='Turns on Anti-RoleDel',
                inline=False
                )
            embed.add_field(
                name='**.antiroledel off**',
                value='Turns off Anti-RoleDel',
                inline=False
            )
            extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
            embed.set_footer(
                text='Developed By skeet#1500 | Server Prefix: ' +
                ' and '.join(extras)
            )
            await ctx.send(embed=embed)
    
    @antiroledel.command(name='on')
    async def antiroledel_on(self, ctx):
        await ctx.message.delete()
        if ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_embed('Only the Server Owner can use this Command.'))
        elif self.client.antiRole == True:
            await ctx.send(embed=create_embed('Anti-Role Deletion is Already Enabled!'))
        else:
            self.client.antiRole = True
            await ctx.send(embed=create_embed('Anti-Role Deletion Enabled!'))

    @antiroledel.command(name='off')
    async def antiroledel_off(self, ctx):
        await ctx.message.delete()
        if ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_embed('Only the Server Owner can use this Command.'))
        elif self.client.antiRole == False:
            await ctx.send(embed=create_embed('Anti-Role Deletion is Already Disabled!'))
        else:
            self.client.antiRole = False
            await ctx.send(embed=create_embed('Anti-Role Deletion Disabled!'))
    
    @commands.group(
        name="antichandel",
        description="Turns Anti-ChanDel on or off.",
        invoke_without_command=True,
        usage="`.antichandel on/off`"
    )
    async def antichandel(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                colour=discord.Colour.from_rgb(182,7,7),
                description="Doesn't Allow Mass Channel Deletion.",
                timestamp=ctx.message.created_at
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif"
            )
            embed.set_author(
                name='Anti-RoleChan Commands',
                icon_url=ctx.author.avatar_url
            )
            embed.add_field(
                name='**.antichandel on**',
                value='Turns on Anti-ChanDel',
                inline=False
                )
            embed.add_field(
                name='**.antichandel off**',
                value='Turns off Anti-ChanDel',
                inline=False
            )
            extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
            embed.set_footer(
                text='Developed By skeet#1500 | Server Prefix: ' +
                ' and '.join(extras)
            )
            await ctx.send(embed=embed)
    
    @antichandel.command(name='on')
    async def antichandel_on(self, ctx):
        await ctx.message.delete()
        if ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_embed('Only the Server Owner can use this Command.'))
        elif self.client.antiChannel == True:
            await ctx.send(embed=create_embed('Anti-Channel Deletion is Already Enabled!'))
        else:
            self.client.antiChannel = True
            await ctx.send(embed=create_embed('Anti-Channel Deletion Enabled!'))
    
    @antichandel.command(name='off')
    async def antichandel_off(self, ctx):
        await ctx.message.delete()
        if ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_embed('Only the Server Owner can use this Command.'))
        elif self.client.antiChannel == False:
            await ctx.send(embed=create_embed('Anti-Channel Deletion is Already Disabled!'))
        else:
            self.client.antiChannel = False
            await ctx.send(embed=create_embed('Anti-Channel Deletion Disabled!'))
    
    @commands.group(
        name="antirolecreation",
        description="Turns Anti-RoleCreation on or off.",
        invoke_without_command=True,
        usage="`.antirolecreation on/off`"
    )
    async def antirolecreation(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                colour=discord.Colour.from_rgb(182,7,7),
                description="Doesn't Allow Mass Role Creation.",
                timestamp=ctx.message.created_at
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif"
            )
            embed.set_author(
                name='Anti-RoleCreation Commands',
                icon_url=ctx.author.avatar_url
            )
            embed.add_field(
                name='**.antirolecreation on**',
                value='Turns on Anti-RoleCreation',
                inline=False
                )
            embed.add_field(
                name='**.antirolecreation off**',
                value='Turns off Anti-RoleCreation',
                inline=False
            )
            extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
            embed.set_footer(
                text='Developed By skeet#1500 | Server Prefix: ' +
                ' and '.join(extras)
            )
            await ctx.send(embed=embed)
    
    @antirolecreation.command(name='on')
    async def antirolecreation_on(self, ctx):
        await ctx.message.delete()
        if ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_embed('Only the Server Owner can use this Command.'))
        elif self.client.antiRoleCreation == True:
            await ctx.send(embed=create_embed('Anti-Role Creation is Already Enabled!'))
        else:
            self.client.antiRoleCreation = True
            await ctx.send(embed=create_embed('Anti-Role Creation Enabled!'))
    
    @antirolecreation.command(name='off')
    async def antirolecreation_off(self, ctx):
        await ctx.message.delete()
        if ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_embed('Only the Server Owner can use this Command.'))
        elif self.client.antiRoleCreation == False:
            await ctx.send(embed=create_embed('Anti-Role Creation is Already Disabled!'))
        else:
            self.client.antiRoleCreation = False
            await ctx.send(embed=create_embed('Anti-Role Creation Disabled!'))
    
    @commands.group(
        name="antichancreation",
        description="Turns Anti-ChanCreation on or off.",
        invoke_without_command=True,
        usage="`.antichancreation on/off`"
    )
    async def antichancreation(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                colour=discord.Colour.from_rgb(182,7,7),
                description="Doesn't Allow Mass Channel Creation.",
                timestamp=ctx.message.created_at
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif"
            )
            embed.set_author(
                name='Anti-RoleCreation Commands',
                icon_url=ctx.author.avatar_url
            )
            embed.add_field(
                name='**.antichancreation on**',
                value='Turns on Anti-ChanCreation',
                inline=False
                )
            embed.add_field(
                name='**.antichancreation off**',
                value='Turns off Anti-ChanCreation',
                inline=False
            )
            extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
            embed.set_footer(
                text='Developed By skeet#1500 | Server Prefix: ' +
                ' and '.join(extras)
            )
            await ctx.send(embed=embed)
    
    @antichancreation.command(name="on")
    async def antichancreation_on(self, ctx):
        await ctx.message.delete()
        if ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_embed('Only the Server Owner can use this Command.'))
        elif self.client.antiChannelCreation == True:
            await ctx.send(embed=create_embed('Anti-Channel Creation is Already Enabled!'))
        else:
            self.client.antiChannelCreation = True
            await ctx.send(embed=create_embed('Anti-Channel Creation Enabled!'))
    
    @antichancreation.command(name='off')
    async def antichancreation_off(self, ctx):
        await ctx.message.delete()
        if ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_embed('Only the Server Owner can use this Command.'))
        elif self.client.antiChannelCreation == False:
            await ctx.send(embed=create_embed('Anti-Channel Creation is Already Disabled!'))
        else:
            self.client.antiChannelCreation = False
            await ctx.send(embed=create_embed('Anti-Channel Creation Disabled!'))
    
    @commands.group(
        name="whitelist",
        description="Removes or Adds a member to the Whitelist.",
        invoke_without_command=True,
        usage="`.whitelist add/remove [@user]`"
    )
    async def whitelist(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                colour=discord.Colour.from_rgb(182,7,7),
                description="Whitelist certain users.",
                timestamp=ctx.message.created_at
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/720812237794574347/767694660805197834/ezgif.com-gif-maker_5.gif"
            )
            embed.set_author(
                name='Whitelist Commands',
                icon_url=ctx.author.avatar_url
            )
            embed.add_field(
                name='**.whitelist add [@member]**',
                value='Adds a member to the Whitelist.',
                inline=False
                )
            embed.add_field(
                name='**.whitelist remove [@member]**',
                value='Removes a member from the Whitelist',
                inline=False
            )
            extras = guildcol.find_one({'guild_id': ctx.guild.id})['prefixes']
            embed.set_footer(
                text='Developed By skeet#1500 | Server Prefix: ' +
                ' and '.join(extras)
            )
            await ctx.send(embed=embed)
            
    @whitelist.command(name='show')
    async def whitelist_show(self, ctx):
        embed = discord.Embed(colour=discord.Colour.from_rgb(182,7,7), title="Whitelisted Users", description="")
        embed.description = ",\n".join([f'<@{i}>' for i in self.client.whitelist])
        await ctx.send(embed=embed)
        
    @whitelist.command(name='add')
    async def whitelist_add(self, ctx, i: discord.Member):
        if ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_embed('Only the Server Owner can use this Command.'))
        else:
            self.client.whitelist.append(i.id)
            await ctx.send(embed=create_embed(f'Added {i.mention} to the whitelist'))
    
    @whitelist.command(name='remove')
    async def whitelist_remove(self, ctx, i: discord.Member):
        if ctx.author != ctx.guild.owner:
            await ctx.send(embed=create_embed('Only the Server Owner can use this Command.'))
        else:
            self.client.whitelist.remove(i.id)
            await ctx.send(embed=create_embed(f'Removed {i.mention} from the whitelist'))
        
def setup(client):
    client.add_cog(AntiNuke(client))
