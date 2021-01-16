# Imports
import asyncio
import math
import os
import discord
import pymongo
import youtube_dl
from googleapiclient.discovery import build
from discord.ext import commands
from youtube_dl import utils
from helper import *

# Suppress annoying console message
youtube_dl.utils.bug_reports_message = lambda: ''

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


# Helper to create audio player
def create_ytdl_source(source, volume=0.5):
    player = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(
            source,
            before_options=" -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 1",
            options='-vn'
        ),
        volume=volume
    )
    return player


# Ensure user is connected to voice
def ensure_voice():
    async def predicate(ctx):
        if ctx.author.voice == None:
            await ctx.send(
                embed=create_embed(
                    'You must be connected to a voice channel to use this command'
                )
            )
            return False
        else:
            return True
    return commands.check(predicate)


class Music(commands.Cog, name='Music'):
    def __init__(self, client):
        self.client = client
        self.opts = {
            "default_search": "ytsearch",
            'format': 'bestaudio/best/bestvideo',
            'quiet': True,
            'noplaylist': False,
            # 'extract_flat': 'in_playlist',
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'no_warnings': True,
            'include_ads': False,
            'skip_download': True,
            'source_address': '0.0.0.0'
        }
        self.youtube_service = build(
            'youtube',
            'v3',
            developerKey=os.environ.get('Youtube_API')
        )

    def extract_info(self, url, ctx):
        try:
            with youtube_dl.YoutubeDL(self.opts) as ydl:
                info = ydl.extract_info(
                    url+' ',
                    download=False
                )
        except (utils.ExtractorError, utils.DownloadError, utils.UnavailableVideoError) as error:
            asyncio.run_coroutine_threadsafe(
                ctx.send(
                    embed=create_embed(
                        'There is an error with Youtube service, please try again'
                    ), delete_after=10
                ), self.client.loop
            )
        return info

    def ensure_bot_alone(self, ctx):
        if ctx.voice_client == None:
            return True
        elif ctx.voice_client != None:
            if len(ctx.voice_client.channel.members) == 1:
                return True
            else:
                if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                    return False
                else:
                    return True

    def play_song(self, guild):
        item = queuecol.find_one({'guild_id': guild.id})
        pointer = item['pointer']
        text_channel = self.client.get_channel(item['text_channel'])
        restart = False
        for i in range(3):
            try:
                with youtube_dl.YoutubeDL(self.opts) as ydl:
                    info = ydl.extract_info(
                        item['queue'][pointer]['url']+' ',
                        download=False
                    )
            except (utils.ExtractorError, utils.DownloadError, utils.UnavailableVideoError) as error:
                asyncio.run_coroutine_threadsafe(
                    text_channel.send(
                        embed=create_embed(
                            'There is an error with Youtube service, retrying'
                        ),
                        delete_after=10
                    ), self.client.loop
                )
                restart = True
            else:
                restart = False
                break
        if restart:
            asyncio.run_coroutine_threadsafe(
                text_channel.send(
                    embed=create_embed(
                        'There is an error with Youtube service, bot is being restarted'
                    ),
                    delete_after=10
                ), self.client.loop
            )
            os._exit(0)
        volume = item['volume']
        voice = guild.voice_client
        source = create_ytdl_source(info['url'], volume)
        try:
            asyncio.run_coroutine_threadsafe(
                text_channel.send(
                    embed=create_embed(
                        f'**Now playing**: [{info["title"]}]({info["webpage_url"]})'
                    ),
                    delete_after=info['duration']
                ), self.client.loop
            )
        except:
            pass

        def after_playing(error):
            queue = queuecol.find_one({'guild_id': guild.id})
            if queue['size'] == 0:
                asyncio.run_coroutine_threadsafe(
                    voice.disconnect(),
                    self.client.loop,
                )
                queuecol.delete_one({'guild_id': guild.id})
            elif queue['loop'] == 'all':
                if queue['pointer'] == queue['size']-1:
                    queuecol.update_one(
                        {'guild_id': guild.id},
                        {
                            '$set': {
                                'pointer': 0
                            }
                        }
                    )
                else:
                    queuecol.update_one(
                        {'guild_id': guild.id},
                        {
                            '$inc': {
                                'pointer': 1
                            }
                        }
                    )
                self.play_song(guild)
            elif queue['loop'] == 'off':
                if queue['pointer'] == queue['size']-1:
                    asyncio.run_coroutine_threadsafe(
                        voice.disconnect(),
                        self.client.loop,
                    )
                    queuecol.delete_one({'guild_id': guild.id})
                else:
                    queuecol.update_one(
                        {'guild_id': guild.id},
                        {
                            '$inc': {
                                'pointer': 1
                            }
                        }
                    )
                    self.play_song(guild)
            else:
                self.play_song(guild)

        voice.play(source, after=after_playing)

    @commands.command(
        name='voiceping',
        description='Calculate the current voice client latency',
        usage='`.voiceping`'
    )
    @ensure_voice()
    @blacklist_check()
    async def voiceping(self, ctx, arg=None):
        if arg != None:
            await ctx.send(
                embed=create_embed(
                    'This command does not take in any other argument'
                )
            )
        else:
            voice = ctx.voice_client
            if voice != None:
                time = int(voice.latency*1000)
                await ctx.send(
                    embed=create_embed(
                        f'The voice client ping is {time} ms!'
                    ),
                    delete_after=10
                )
            else:
                await ctx.send(
                    embed=create_embed(
                        'Bot was not connected to any voice channel'
                    ),
                    delete_after=10
                )

    @commands.command(
        name='join',
        aliases=['j', 'connect', ],
        description='Connect to your current voice channel',
        usage='`.join`'
    )
    @ensure_voice()
    @blacklist_check()
    async def join(self, ctx, arg=None):
        if arg != None:
            await ctx.send(
                embed=create_embed(
                    'This command does not take in any other argument'
                )
            )
        else:
            channel = ctx.author.voice.channel
            voice = ctx.voice_client
            if voice != None:
                if self.ensure_bot_alone(ctx):
                    await voice.move_to(channel)
                    queuecol.update_one(
                        {'guild_id': ctx.guild.id},
                        {
                            '$set': {
                                'voice_channel': voice.channel.id
                            }
                        }
                    )
                    await ctx.send(
                        embed=create_embed(
                            f'Bot connected to **{channel}**'
                        ),
                        delete_after=10
                    )
                else:
                    await ctx.send(
                        embed=create_embed(
                            'Please wait until other members are done listening to music'
                        ),
                        delete_after=10
                    )
            else:
                voice = await channel.connect(reconnect=True)
                if queuecol.find_one({'guild_id': ctx.guild.id}) != None:
                    queuecol.delete_one({'guild_id': ctx.guild.id})
                queuecol.insert_one(
                    {
                        'guild_id': ctx.guild.id,
                        'text_channel': ctx.channel.id,
                        'voice_channel': voice.channel.id,
                        'state': None,
                        'loop': 'off',
                        'volume': 0.5,
                        'pointer': 0,
                        'size': 0,
                        'queue': [],
                    }
                )
                await ctx.send(
                    embed=create_embed(
                        f'Bot connected to **{channel}**'
                    ),
                    delete_after=10
                )

    @commands.command(
        name='leave',
        aliases=['dc', 'disconnect'],
        description='Disconnect from the voice channel',
        usage='`.leave`'
    )
    @blacklist_check()
    async def leave(self, ctx, arg=None):
        if arg != None:
            await ctx.send(
                embed=create_embed(
                    'This command does not take in any other argument'
                ),
                delete_after=10
            )
        else:
            voice = ctx.voice_client
            if voice != None:
                if len(ctx.voice_client.channel.members) == 1:
                    queuecol.update_one(
                        {'guild_id': ctx.guild.id},
                        {
                            '$set': {
                                'size': 0
                            }
                        }
                    )
                    voice.stop()
                    await voice.disconnect()
                    if queuecol.find_one({'guild_id': ctx.guild.id}) != None:
                        queuecol.delete_one({'guild_id': ctx.guild.id})
                    await ctx.send(
                        embed=create_embed(
                            f'Bot disconnected from **{voice.channel}**'
                        ),
                        delete_after=10
                    )

                else:
                    if voice.channel == ctx.author.voice.channel:
                        queuecol.update_one(
                            {'guild_id': ctx.guild.id},
                            {
                                '$set': {
                                    'size': 0
                                }
                            }
                        )
                        voice.stop()
                        await voice.disconnect()
                        if queuecol.find_one({'guild_id': ctx.guild.id}) != None:
                            queuecol.delete_one({'guild_id': ctx.guild.id})
                        await ctx.send(
                            embed=create_embed(
                                f'Bot disconnected from **{voice.channel}**'
                            ),
                            delete_after=10
                        )
                    else:
                        await ctx.send(
                            embed=create_embed(
                                'Please wait until other members are done listening to music'
                            ),
                            delete_after=10
                        )
            else:
                await ctx.send(
                    embed=create_embed(
                        'Bot was not connected to any voice channel'
                    ),
                    delete_after=10
                )

    @commands.command(
        name='play',
        aliases=['p', ],
        description='Play music from Youtube',
        usage='`.play [url or song name]`'
    )
    @ensure_voice()
    @blacklist_check()
    async def play(self, ctx, *, url: str):
        text_channel = ctx.channel
        channel = ctx.author.voice.channel
        voice = ctx.voice_client
        if voice != None:  # Bot already in voice channel
            if voice.channel != channel:  # User in a different channel
                if self.ensure_bot_alone(ctx):   # Check if bot is available
                    info = self.extract_info(url, ctx)
                    # Delete the current queue
                    if voice.is_playing() or voice.is_paused():
                        queuecol.update_one(
                            {'guild_id': ctx.guild.id},
                            {
                                '$set': {
                                    'size': 0,
                                }
                            }
                        )
                        voice.stop()
                        voice = await channel.connect(reconnect=True)
                    else:
                        # Move the bot to the new channel
                        queuecol.delete_one({'guild_id': ctx.guild.id})
                        await voice.move_to(channel)
                        # Create a new queue
                        queuecol.insert_one(
                            {
                                'guild_id': ctx.guild.id,
                                'text_channel': ctx.channel.id,
                                'voice_channel': voice.channel.id,
                                'state': 'Playing',
                                'loop': 'off',
                                'volume': 0.5,
                                'pointer': 0,
                                'size': 0,
                                'queue': [],
                            }
                        )
                        # Check if ytdl gives a playlist
                        if "_type" in info and info["_type"] == "playlist":
                            # The playlist is not supported
                            if 'title' not in info['entries'][0]:
                                await ctx.send(
                                    embed=create_embed(
                                        'This playlist link is not supported'
                                    ),
                                    delete_after=10
                                )
                            else:
                                # The playlist only have one song
                                if len(info['entries']) == 1:
                                    # Get song metadata
                                    song_info = info['entries'][0]
                                    # Insert the song into queue
                                    queuecol.update_one(
                                        {'guild_id': ctx.guild.id},
                                        {
                                            '$push': {
                                                'queue': {
                                                    'url': song_info['webpage_url'],
                                                    'title': song_info['title']
                                                }
                                            },
                                            '$inc': {
                                                'size': 1
                                            },
                                        }
                                    )
                                else:
                                    # Insert all songs into queue
                                    for song in info['entries']:
                                        queuecol.update_one(
                                            {'guild_id': ctx.guild.id},
                                            {
                                                '$push': {
                                                    'queue': {
                                                        'url': song['webpage_url'],
                                                        'title': song['title']
                                                    }
                                                },
                                                '$inc': {
                                                    'size': 1
                                                }
                                            }
                                        )
                                    await ctx.send(
                                        embed=create_embed(
                                            f'{len(info["entries"])} songs from [link]({url}) added to queue'
                                        ),
                                        delete_after=10
                                    )
                        else:
                            # Insert song from an url
                            queuecol.update_one(
                                {'guild_id': ctx.guild.id},
                                {
                                    '$push': {
                                        'queue': {
                                            'url': info['webpage_url'],
                                            'title': info['title']
                                        }
                                    },
                                    '$inc': {
                                        'size': 1
                                    }
                                }
                            )
                            # Start playing
                        self.play_song(ctx.guild)
                else:  # Bot is not available
                    await ctx.send(
                        embed=create_embed(
                            'Please wait until other members are done listening to music'
                        ),
                        delete_after=10
                    )
            else:  # User in the same channel as bot
                if voice.is_playing() or voice.is_paused():  # Bot is playing music
                    info = self.extract_info(url, ctx)
                    # Check if ytdl gives a playlist
                    if "_type" in info and info["_type"] == "playlist":
                        # The playlist is not supported
                        if 'title' not in info['entries'][0]:
                            await ctx.send(
                                embed=create_embed(
                                    'This playlist link is not supported'
                                ),
                                delete_after=10
                            )
                        else:
                            # The playlist only have one song
                            if len(info['entries']) == 1:
                                # Get song metadata
                                song_info = info['entries'][0]
                                # Insert the song into queue
                                queuecol.update_one(
                                    {'guild_id': ctx.guild.id},
                                    {
                                        '$push': {
                                            'queue': {
                                                'url': song_info['webpage_url'],
                                                'title': song_info['title']
                                            }
                                        },
                                        '$inc': {
                                            'size': 1
                                        }
                                    }
                                )
                                await ctx.send(
                                    embed=create_embed(
                                        f'Song [{song_info["title"]}]({song_info["webpage_url"]}) added to queue'
                                    ),
                                    delete_after=10
                                )
                            else:
                                # Insert all songs into queue
                                for song in info['entries']:
                                    queuecol.update_one(
                                        {'guild_id': ctx.guild.id},
                                        {
                                            '$push': {
                                                'queue': {
                                                    'url': song['webpage_url'],
                                                    'title': song['title']
                                                }
                                            },
                                            '$inc': {
                                                'size': 1
                                            }
                                        }
                                    )
                                await ctx.send(
                                    embed=create_embed(
                                        f'{len(info["entries"])} songs added to queue'
                                    ),
                                    delete_after=10
                                )
                    else:
                        # Insert song from an url
                        queuecol.update_one(
                            {'guild_id': ctx.guild.id},
                            {
                                '$push': {
                                    'queue': {
                                        'url': info['webpage_url'],
                                        'title': info['title']
                                    }
                                },
                                '$inc': {
                                    'size': 1
                                }
                            }
                        )
                        await ctx.send(
                            embed=create_embed(
                                f'Song [{info["title"]}]({info["webpage_url"]}) added to queue'
                            ),
                            delete_after=10
                        )
                else:  # Bot is not playing any music
                    info = self.extract_info(url, ctx)
                    # Check if ytdl gives a playlist
                    if "_type" in info and info["_type"] == "playlist":
                        # The playlist is not supported
                        if 'title' not in info['entries'][0]:
                            await ctx.send(
                                embed=create_embed(
                                    'This playlist link is not supported'
                                ),
                                delete_after=10
                            )
                        else:
                            # The playlist only have one song
                            if len(info['entries']) == 1:
                                # Get song metadata
                                song_info = info['entries'][0]
                                # Insert the song into queue
                                queuecol.update_one(
                                    {'guild_id': ctx.guild.id},
                                    {
                                        '$push': {
                                            'queue': {
                                                'url': song_info['webpage_url'],
                                                'title': song_info['title']
                                            }
                                        },
                                        '$inc': {
                                            'size': 1
                                        }
                                    }
                                )
                            else:
                                # Insert all songs into queue
                                for song in info['entries']:
                                    queuecol.update_one(
                                        {'guild_id': ctx.guild.id},
                                        {
                                            '$push': {
                                                'queue': {
                                                    'url': song['webpage_url'],
                                                    'title': song['title']
                                                }
                                            },
                                            '$inc': {
                                                'size': 1
                                            }
                                        }
                                    )
                                await ctx.send(
                                    embed=create_embed(
                                        f'{len(info["entries"])} songs from [link]({url}) added to queue'
                                    ),
                                    delete_after=10
                                )
                    else:
                        # Insert song from an url
                        queuecol.update_one(
                            {'guild_id': ctx.guild.id},
                            {
                                '$push': {
                                    'queue': {
                                        'url': info['webpage_url'],
                                        'title': info['title']
                                    }
                                },
                                '$inc': {
                                    'size': 1
                                }
                            }
                        )
                    # Start playing
                    self.play_song(ctx.guild)
        else:  # Bot is not connected to any voice channel
            # Connects bot to a voice channel
            voice = await channel.connect(reconnect=True)
            info = self.extract_info(url, ctx)
            # Create a new queue
            if queuecol.find_one({'guild_id': ctx.guild.id}) != None:
                queuecol.delete_one({'guild_id': ctx.guild.id})
            queuecol.insert_one(
                {
                    'guild_id': ctx.guild.id,
                    'text_channel': ctx.channel.id,
                    'voice_channel': voice.channel.id,
                    'state': 'Playing',
                    'loop': 'off',
                    'volume': 0.5,
                    'pointer': 0,
                    'size': 0,
                    'queue': [],
                }
            )
            # Check if ytdl gives a playlist
            if "_type" in info and info["_type"] == "playlist":
                # The playlist is not supported
                if 'title' not in info['entries'][0]:
                    await ctx.send(
                        embed=create_embed(
                            'This playlist link is not supported'
                        ),
                        delete_after=10
                    )
                else:
                    if len(info['entries']) == 1:  # The playlist only have one song
                        # Get song metadata
                        song_info = info['entries'][0]
                        # Insert the song into queue
                        queuecol.update_one(
                            {'guild_id': ctx.guild.id},
                            {
                                '$push': {
                                    'queue': {
                                        'url': song_info['webpage_url'],
                                        'title': song_info['title']
                                    }
                                },
                                '$inc': {
                                    'size': 1
                                }
                            }
                        )
                    else:
                        # Insert all songs into queue
                        for song in info['entries']:
                            queuecol.update_one(
                                {'guild_id': ctx.guild.id},
                                {
                                    '$push': {
                                        'queue': {
                                            'url': song['webpage_url'],
                                            'title': song['title']
                                        }
                                    },
                                    '$inc': {
                                        'size': 1
                                    }
                                }
                            )
                        await ctx.send(
                            embed=create_embed(
                                f'{len(info["entries"])} songs from [link]({url}) added to queue'
                            ),
                            delete_after=10
                        )
            else:
                # Insert song from an url
                queuecol.update_one(
                    {'guild_id': ctx.guild.id},
                    {
                        '$push': {
                            'queue': {
                                'url': info['webpage_url'],
                                'title': info['title']
                            }
                        },
                        '$inc': {
                            'size': 1
                        }
                    }
                )
            # Start playing
            self.play_song(ctx.guild)

    @commands.command(
        name='pause',
        aliases=['pau', 'pa'],
        description='Pauses the music',
        usage='`.pause`'
    )
    @ensure_voice()
    @blacklist_check()
    async def pause(self, ctx, arg=None):
        if arg != None:
            await ctx.send(
                embed=create_embed(
                    'This command does not take in any other argument'
                ),
                delete_after=10
            )
        else:
            channel = ctx.author.voice.channel
            voice = ctx.voice_client
            if voice != None:
                if voice.channel == channel:
                    if voice.is_playing():
                        voice.pause()
                        queuecol.update_one(
                            {'guild_id': ctx.guild.id},
                            {
                                '$set': {
                                    'state': 'Paused'
                                }
                            }
                        )
                        await ctx.send(
                            embed=create_embed(
                                'Music paused'
                            ),
                            delete_after=10
                        )
                    elif voice.is_paused():
                        await ctx.send(
                            embed=create_embed(
                                'Cannot pause while bot was already paused'
                            ),
                            delete_after=10
                        )
                    else:
                        await ctx.send(
                            embed=create_embed(
                                'Cannot pause while bot was not playing music'
                            ),
                            delete_after=10
                        )
                else:
                    await ctx.send(
                        embed=create_embed(
                            'Please wait until other members are done listening to music'
                        ),
                        delete_after=10
                    )
            else:
                await ctx.send(
                    embed=create_embed(
                        'Cannot pause while bot was not connected to any voice channel'
                    ),
                    delete_after=10
                )

    @commands.command(
        name='resume',
        aliases=['res', 're'],
        description='Resume the music',
        usage='`.resume`'
    )
    @ensure_voice()
    @blacklist_check()
    async def resume(self, ctx, arg=None):
        if arg != None:
            await ctx.send(
                embed=create_embed(
                    'This command does not take in any other argument'
                ),
                delete_after=10
            )
        else:
            channel = ctx.author.voice.channel
            voice = ctx.voice_client
            if voice != None:
                if voice.channel != channel:
                    await ctx.send(
                        embed=create_embed(
                            'Please wait until other members are done listening to music'
                        ),
                        delete_after=10
                    )
                else:
                    if voice.is_paused():
                        voice.resume()
                        queuecol.update_one(
                            {'guild_id': ctx.guild.id},
                            {
                                '$set': {
                                    'state': 'Playing'
                                }
                            }
                        )
                        await ctx.send(
                            embed=create_embed(
                                'Resumed music'
                            ),
                            delete_after=10
                        )
                    elif voice.is_playing():
                        await ctx.send(
                            embed=create_embed(
                                'Cannot resume if music is already playing'
                            ),
                            delete_after=10
                        )
                    else:
                        item = queuecol.find_one({'guild_id': ctx.guild.id})
                        if len(item['queue']) > 0:
                            self.play_song(ctx.guild)
                            queuecol.update_one(
                                {'guild_id': ctx.guild.id},
                                {
                                    '$set': {
                                        'state': 'Playing'
                                    }
                                }
                            )
                            await ctx.send(
                                embed=create_embed(
                                    'Resumed music'
                                ),
                                delete_after=10
                            )
                        else:
                            await ctx.send(
                                embed=create_embed(
                                    'Cannot resume if there is no music to play'
                                ),
                                delete_after=10
                            )
            else:
                item = queuecol.find_one({'guild_id': ctx.guild.id})
                if item == None:
                    await ctx.send(
                        embed=create_embed(
                            'Cannot resume while bot was not connected to any voice channel'
                        ),
                        delete_after=10
                    )
                else:
                    guild = self.client.get_guild(item['guild_id'])
                    channel = guild.get_channel(item['voice_channel'])
                    voice = await channel.connect(reconnect=True)
                    self.play_song(ctx.guild)
                    await ctx.send(
                        embed=create_embed(
                            'Resumed music'
                        ),
                        delete_after=10
                    )

    @commands.command(
        name='stop',
        aliases=['s', 'st', ],
        description='Stop playing music',
        usage='`.stop`'
    )
    @ensure_voice()
    @blacklist_check()
    async def stop(self, ctx, arg=None):
        if arg != None:
            await ctx.send(
                embed=create_embed(
                    'This command does not take in any other argument'
                ),
                delete_after=10
            )
        else:
            channel = ctx.author.voice.channel
            voice = ctx.voice_client
            if voice != None:
                if voice.channel != channel:
                    await ctx.send(
                        embed=create_embed(
                            'Please wait until other members are done listening to music'
                        ),
                        delete_after=10
                    )
                else:
                    if voice.is_playing() or voice.is_paused():
                        queuecol.update_one(
                            {'guild_id': ctx.guild.id},
                            {
                                '$set': {
                                    'loop': 'off',
                                    'pointer': 0,
                                    'size': 0,
                                    'queue': [],
                                }
                            }
                        )
                        voice.stop()
                        await ctx.send(
                            embed=create_embed(
                                'Stopped playing music'
                            ),
                            delete_after=10
                        )
                    else:
                        await ctx.send(
                            embed=create_embed(
                                'Cannot stop if no music is playing'
                            ),
                            delete_after=10
                        )
            else:
                await ctx.send(
                    embed=create_embed(
                        'Cannot stop while bot was not connected to any voice channel'
                    ),
                    delete_after=10
                )

    @commands.command(
        name='skip',
        aliases=['sk', 'next'],
        description='Skip to a song in the music queue',
        usage='`.skip [position]`'
    )
    @ensure_voice()
    @blacklist_check()
    async def skip(self, ctx, pos: int = None):
        channel = ctx.author.voice.channel
        voice = ctx.voice_client
        if voice != None:
            if voice.channel != channel:
                await ctx.send(
                    embed=create_embed(
                        'Please wait until other members are done listening to music'
                    ),
                    delete_after=10
                )
            else:
                item = queuecol.find_one({'guild_id': ctx.guild.id})
                pointer = item['pointer']
                queue = item['queue']
                if item['size'] == 0:
                    await ctx.send(
                        embed=create_embed(
                            'The music queue is empty'
                        ),
                        delete_after=10
                    )
                elif pos == None:
                    song = queue[pointer]
                    await ctx.send(
                        embed=create_embed(
                            f'Skipped [{song["title"]}]({song["url"]})'
                        ),
                        delete_after=10
                    )
                    voice.stop()
                elif pos < 1 or pos > item['size']:
                    await ctx.send(
                        embed=create_embed(
                            f'The queue only have {item["size"]} songs, but you specified more than that'
                        ),
                        delete_after=10
                    )
                else:
                    song = queue[pointer]
                    if item['loop'] == 'one':
                        queuecol.update_one(
                            {'guild_id': ctx.guild.id},
                            {
                                '$set': {
                                    'pointer': pos-1
                                }
                            }
                        )
                        await ctx.send(
                            embed=create_embed(
                                f'Skipped [{song["title"]}]({song["url"]})'
                            ),
                            delete_after=10
                        )
                    else:
                        queuecol.update_one(
                            {'guild_id': ctx.guild.id},
                            {
                                '$set': {
                                    'pointer': pos-2
                                }
                            }
                        )
                        await ctx.send(
                            embed=create_embed(
                                f'Skipped [{song["title"]}]({song["url"]})'
                            ),
                            delete_after=10
                        )
                    voice.stop()
        else:
            await ctx.send(
                embed=create_embed(
                    'Bot was not connected to any voice channel'
                ),
                delete_after=10
            )

    @commands.command(
        name='volume',
        description='Changes the volume (max=300)',
        aliases=['vol', ],
        usage='`.vol [volume]`'
    )
    @ensure_voice()
    @blacklist_check()
    async def volume(self, ctx, volume: int):
        if ctx.voice_client == None:
            await ctx.send(
                embed=create_embed(
                    'Bot was not connected to any voice channel'
                ),
                delete_after=10
            )
        else:
            channel = ctx.author.voice.channel
            voice = ctx.voice_client
            if voice.channel != channel:
                await ctx.send(
                    embed=create_embed(
                        'Please wait until other members are done listening to music'
                    ),
                    delete_after=10
                )
            elif volume == None:
                await ctx.send(
                    embed=create_embed(
                        'Please specify the volume that you want'
                    ),
                    delete_after=10
                )
            else:
                if 0 <= volume <= 300:
                    queuecol.update_one(
                        {'guild_id': ctx.guild.id},
                        {
                            '$set': {
                                'volume': volume/200,
                            }
                        }
                    )
                    voice.source.volume = volume/200
                    await ctx.send(
                        embed=create_embed(
                            f'Music volume changed to {volume}'
                        ),
                        delete_after=10
                    )
                else:
                    await ctx.send(
                        embed=create_embed(
                            'Volume cannot exceed 300'
                        ),
                        delete_after=10
                    )

    @commands.command(
        name='queue',
        aliases=['q', ],
        description='Display your current music queue',
        usage='`.queue [page]`'
    )
    @ensure_voice()
    @blacklist_check()
    async def queue(self, ctx, page: int = 1):
        channel = ctx.author.voice.channel
        voice = ctx.voice_client
        if voice != None:
            if voice.channel != channel:
                await ctx.send(
                    embed=create_embed(
                        'You are not using music'
                    ),
                    delete_after=10
                )
            else:
                item = queuecol.find_one({'guild_id': ctx.guild.id})
                if item['size'] == 0:
                    await ctx.send(
                        embed=create_embed(
                            'The music queue is empty'
                        ),
                        delete_after=10
                    )
                else:
                    queue = item['queue']
                    pointer = item['pointer']
                    info = queue[pointer]
                    pages = math.ceil(item['size']/10)
                    output = ''
                    if 1 <= page <= pages:
                        counter = 1 + (page-1)*10
                        for song in queue[(page-1)*10:page*10]:
                            output += f'{counter}. [{song["title"]}]({song["url"]})\n'
                            counter += 1
                        embed = discord.Embed(
                            colour=discord.Colour.from_rgb(182,7,7),
                            description=output,
                            title='**Music Queue**',
                            timestamp=ctx.message.created_at
                        )
                        embed.add_field(
                            name='Now Playing',
                            value=f"{pointer+1}. [{info['title']}]({info['url']})",
                            inline=False
                        )
                        embed.add_field(
                            name='Entries',
                            value=f"{item['size']}"
                        )
                        embed.add_field(
                            name='Repeating',
                            value=item['loop']
                        )
                        embed.add_field(
                            name='Volume',
                            value=f"{item['volume']*200}"
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
        else:
            await ctx.send(
                embed=create_embed(
                    'Bot was not connected to any voice channel'
                ),
                delete_after=10
            )

    @commands.command(
        name='dequeue',
        aliases=['rmq', 'rm'],
        description='Remove a song from the music queue',
        usage='`.dequeue [song position in music queue]`'
    )
    @ensure_voice()
    @blacklist_check()
    async def dequeue(self, ctx, position: int, arg=None):
        if arg != None:
            await ctx.send(
                embed=create_embed(
                    'This command only takes in one argument'
                ),
                delete_after=10
            )
        else:
            channel = ctx.author.voice.channel
            voice = ctx.voice_client
            if voice != None:
                if voice.channel != channel:
                    await ctx.send(
                        embed=create_embed(
                            'Please wait until other members are done listening to music'
                        ),
                        delete_after=10
                    )
                else:
                    item = queuecol.find_one({'guild_id': ctx.guild.id})
                    queue = item['queue']
                    if 1 <= position <= item['size']:
                        info = queue[position-1]
                        if item['pointer'] >= position-1:
                            queuecol.update_one(
                                {'guild_id': ctx.guild.id},
                                {
                                    '$unset': {
                                        f'queue.{position-1}': ''
                                    },
                                    '$inc': {
                                        'pointer': -1,
                                        'size': -1
                                    }
                                }
                            )
                        else:
                            queuecol.update_one(
                                {'guild_id': ctx.guild.id},
                                {
                                    '$unset': {
                                        f'queue.{position-1}': ''
                                    },
                                    '$inc': {
                                        'size': -1
                                    }
                                }
                            )
                        queuecol.update_one(
                            {'guild_id': ctx.guild.id},
                            {
                                '$pull': {
                                    'queue': None
                                }
                            }
                        )

                        await ctx.send(
                            embed=create_embed(
                                f'Song [{info["title"]}]({info["url"]}) removed from music queue'
                            ),
                            delete_after=10
                        )
                    else:
                        await ctx.send(
                            embed=create_embed(
                                f'The music queue have **{item["size"]}** songs, but you specified more than that!'
                            ),
                            delete_after=10
                        )
            else:
                await ctx.send(
                    embed=create_embed(
                        'Bot was not connected to any voice channel'
                    ),
                    delete_after=10
                )

    @commands.command(
        name='clearqueue',
        aliases=['flush', 'empty', 'clearq'],
        description='Clear the current queue',
        usage='`.clearqueue`'
    )
    @ensure_voice()
    @blacklist_check()
    async def clearqueue(self, ctx, arg=None):
        if arg != None:
            await ctx.send(
                embed=create_embed(
                    'This command does not take in any argument'
                ),
                delete_after=10
            )
        else:
            channel = ctx.author.voice.channel
            voice = ctx.voice_client
            if voice != None:
                if voice.channel != channel:
                    await ctx.send(
                        embed=create_embed(
                            'Please wait until other members are done listening to music'
                        ),
                        delete_after=10
                    )
                else:
                    queuecol.update_one(
                        {'guild_id': ctx.guild.id},
                        {
                            '$set': {
                                'pointer': 0,
                                'size': 0,
                                'queue': []
                            }
                        }
                    )
                    await ctx.send(
                        embed=create_embed(
                            'Queue cleared'
                        ),
                        delete_after=10
                    )
            else:
                await ctx.send(
                    embed=create_embed(
                        'Bot was not connected to any voice channel'
                    ),
                    delete_after=10
                )

    @commands.command(
        name='loop',
        aliases=['repeat', ],
        description='Toggle between looping all, one or off',
        usage='`.loop [all/one/off]`'
    )
    @ensure_voice()
    @blacklist_check()
    async def loop(self, ctx, arg='all'):
        channel = ctx.author.voice.channel
        voice = ctx.voice_client
        if voice != None:
            if voice.channel != channel:
                await ctx.send(
                    embed=create_embed(
                        'Please wait until other members are done listening to music'
                    ),
                    delete_after=10
                )
            else:
                queue = queuecol.find_one({'guild_id': ctx.guild.id})
                if arg == 'all':
                    queuecol.update_one(
                        {'guild_id': ctx.guild.id},
                        {
                            '$set': {
                                'loop': 'all'
                            }
                        }
                    )
                    await ctx.send(
                        embed=create_embed(
                            'Repeating all songs in the music queue'
                        ),
                        delete_after=10
                    )
                elif arg == 'one':
                    queuecol.update_one(
                        {'guild_id': ctx.guild.id},
                        {
                            '$set': {
                                'loop': 'one'
                            }
                        }
                    )
                    await ctx.send(
                        embed=create_embed(
                            'Repeating the current song in the music queue'
                        ),
                        delete_after=10
                    )
                elif arg == 'off':
                    queuecol.update_one(
                        {'guild_id': ctx.guild.id},
                        {
                            '$set': {
                                'loop': 'off'
                            }
                        }
                    )
                    await ctx.send(
                        embed=create_embed(
                            'Repeating song is now off'
                        ),
                        delete_after=10
                    )
                else:
                    await ctx.send(
                        embed=create_embed(
                            'Please use the correct argument'
                        ),
                        delete_after=10
                    )
        else:
            await ctx.send(
                embed=create_embed(
                    'Bot was not connected to any voice channel'
                ),
                delete_after=10
            )

    @commands.group(
        invoke_without_command=True,
        name='playlist',
        aliases=['pl', 'plist'],
        description='Access playlist features',
        usage='`.playlist [option]`'
    )
    @blacklist_check()
    async def playlist(self, ctx, page: int = 1):
        size = playlistcol.count_documents({'guild_id': ctx.guild.id})
        if size == 0:
            await ctx.send(
                embed=create_embed(
                    'There is no playlist created in this guild'
                ),
                delete_after=10
            )
        else:
            output = ''
            playlist_list = playlistcol.find({'guild_id': ctx.guild.id})
            pages = math.ceil(size/10)
            if 1 <= page <= pages:
                counter = 1+(page-1)*10
                for pl in playlist_list[(page-1)*10:page*10]:
                    output += f'{counter}. {pl["name"]}\n'
                    counter += 1
            embed = discord.Embed(
                colour=discord.Colour.from_rgb(182,7,7),
                description=output,
                title=f'**Playlists in {ctx.guild.name}**',
                timestamp=ctx.message.created_at
            )
            embed.set_footer(
                text=f'Page {page} of {pages}'
            )
            await ctx.send(
                embed=embed
            )

    @playlist.command(
        name='play',
        description='Add the playlist to queue and start playing',
        usage='`.playlist play [playlist name]`',
        aliases=['p', ]
    )
    @ensure_voice()
    @blacklist_check()
    async def playlist_play(self, ctx, *, name: str):
        playlist = playlistcol.find_one(
            {
                'guild_id': ctx.guild.id,
                'name': name
            }
        )
        if playlist == None:
            await ctx.send(
                embed=create_embed(
                    f'Playlist **{name}** not found'
                ),
                delete_after=10
            )
        else:
            text_channel = ctx.channel
            channel = ctx.author.voice.channel
            voice = ctx.voice_client
            if voice != None:
                if voice.channel != channel:
                    if self.ensure_bot_alone(ctx):
                        if voice.is_playing() or voice.is_paused():
                            queuecol.update_one(
                                {'guild_id': ctx.guild.id},
                                {
                                    '$set': {
                                        'size': 0,
                                    }
                                }
                            )
                            voice.stop()
                            voice = await channel.connect(reconnect=True)
                        else:
                            queuecol.delete_one({'guild_id': ctx.guild.id})
                            await voice.move_to(channel)
                        queuecol.insert_one(
                            {
                                'guild_id': ctx.guild.id,
                                'text_channel': ctx.channel.id,
                                'voice_channel': voice.channel.id,
                                'state': 'Playing',
                                'loop': 'off',
                                'volume': 0.5,
                                'pointer': 0,
                                'size': 0,
                                'queue': [],
                            }
                        )
                        queuecol.update_one(
                            {'guild_id': ctx.guild.id},
                            {
                                '$push': {
                                    'queue': {
                                        '$each': playlist['song_list']
                                    }
                                },
                                '$inc': {
                                    'size': playlist['size']
                                }
                            }
                        )
                        await ctx.send(
                            embed=create_embed(
                                f'Playlist **{name}** added to queue'
                            ),
                            delete_after=10
                        )
                        self.play_song(ctx.guild)
                    else:
                        await ctx.send(
                            embed=create_embed(
                                'Please wait until other members are done listening to music'
                            ),
                            delete_after=10
                        )
                else:
                    queuecol.update_one(
                        {'guild_id': ctx.guild.id},
                        {
                            '$push': {
                                'queue': {
                                    '$each': playlist['song_list']
                                }
                            },
                            '$inc': {
                                'size': playlist['size']
                            }
                        }
                    )
                    await ctx.send(
                        embed=create_embed(
                            f'Playlist **{name}** added to queue'
                        ),
                        delete_after=10
                    )
                    if voice.is_playing() == False and voice.is_paused() == False:
                        self.play_song(voice)
            else:
                voice = await channel.connect(reconnect=True)
                if queuecol.find_one({'guild_id': ctx.guild.id}) != None:
                    queuecol.delete_one({'guild_id': ctx.guild.id})
                queuecol.insert_one(
                    {
                        'guild_id': ctx.guild.id,
                        'text_channel': ctx.channel.id,
                        'voice_channel': voice.channel.id,
                        'state': 'Playing',
                        'loop': 'off',
                        'volume': 0.5,
                        'pointer': 0,
                        'size': 0,
                        'queue': [],
                    }
                )
                queuecol.update_one(
                    {'guild_id': ctx.guild.id},
                    {
                        '$push': {
                            'queue': {
                                '$each': playlist['song_list']
                            }
                        },
                        '$inc': {
                            'size': playlist['size']
                        }
                    }
                )
                await ctx.send(
                    embed=create_embed(
                        f'Playlist **{name}** added to queue'
                    ),
                    delete_after=10
                )
                self.play_song(ctx.guild)

    @playlist.command(
        name='create',
        description='Create a playlist',
        usage='`.playlist create [playlist name]`'
    )
    @blacklist_check()
    async def create(self, ctx, *, name: str):
        playlist = playlistcol.find_one(
            {
                'guild_id': ctx.guild.id,
                'name': name
            }
        )
        if playlist == None:
            playlistcol.insert_one(
                {
                    'guild_id': ctx.guild.id,
                    'name': name,
                    'size': 0,
                    'song_list': [],
                }
            )
            await ctx.send(
                embed=create_embed(
                    f'Playlist **{name}** created'
                ),
                delete_after=10
            )
        else:
            await ctx.send(
                embed=create_embed(
                    'A playlist with the same name already exist'
                ),
                delete_after=10
            )

    @playlist.command(
        name='delete',
        description='Delete an existing playlist',
        usage='`.playlist delete [playlist name]`',
        aliases=['del', ]
    )
    @blacklist_check()
    async def delete(self, ctx, *, name: str):
        playlist = playlistcol.find_one(
            {
                'guild_id': ctx.guild.id,
                'name': name
            }
        )
        if playlist == None:
            await ctx.send(
                embed=create_embed(
                    f'Playlist **{name}** not found'
                ),
                delete_after=10
            )
        else:
            playlistcol.delete_one(
                {
                    'guild_id': ctx.guild.id,
                    'name': name
                }
            )
            await ctx.send(
                embed=create_embed(
                    f'Playlist **{name}** deleted'
                ),
                delete_after=10
            )

    @playlist.command(
        name='add',
        description='Add a song to an existing playlist',
        usage='`.playlist add [playlist name] [song name or url]`'
    )
    @blacklist_check()
    async def add(self, ctx, name: str, *, url: str):
        playlist = playlistcol.find_one(
            {
                'guild_id': ctx.guild.id,
                'name': name
            }
        )
        if playlist != None:
            info = self.extract_info(url, ctx)
            if "_type" in info and info["_type"] == "playlist":
                if 'title' not in info['entries'][0]:
                    await ctx.send(
                        embed=create_embed(
                            'This playlist link is not supported'
                        ),
                        delete_after=10
                    )
                else:
                    if len(info['entries']) == 1:
                        song_info = info['entries'][0]
                        playlistcol.update_one(
                            {
                                'guild_id': ctx.guild.id,
                                'name': name
                            },
                            {
                                '$push': {
                                    'song_list': {
                                        'url': song_info['webpage_url'],
                                        'title': song_info['title']
                                    }
                                },
                                '$inc': {
                                    'size': 1
                                }
                            }
                        )
                        await ctx.send(
                            embed=create_embed(
                                f'Song [{song_info["title"]}]({song_info["webpage_url"]}) added to **{name}**'
                            ),
                            delete_after=10
                        )
                    else:
                        for song in info['entries']:
                            playlistcol.update_one(
                                {
                                    'guild_id': ctx.guild.id,
                                    'name': name
                                },
                                {
                                    '$push': {
                                        'song_list': {
                                            'url': song['webpage_url'],
                                            'title': song['title']
                                        }
                                    },
                                    '$inc': {
                                        'size': 1
                                    }
                                }
                            )
                        await ctx.send(
                            embed=create_embed(
                                f'{len(info["entries"])} songs added to **{name}**'
                            ),
                            delete_after=10
                        )
            else:
                playlistcol.update_one(
                    {
                        'guild_id': ctx.guild.id,
                        'name': name
                    },
                    {
                        '$push': {
                            'song_list': {
                                'url': info['webpage_url'],
                                'title': info['title']
                            }
                        },
                        '$inc': {
                            'size': 1
                        }
                    }
                )
                await ctx.send(
                    embed=create_embed(
                        f'Song [{info["title"]}]({info["webpage_url"]}) added to **{name}**'
                    ),
                    delete_after=10
                )
        else:
            await ctx.send(
                embed=create_embed(
                    f'Playlist **{name}** not found\nNote: Try adding " " to your playlist name if it contains multiple words'
                ),
                delete_after=10
            )

    @playlist.command(
        name='addqueue',
        description='Add the current queue into a playlist',
        usage='`.playlist addqueue [playlist name]`',
        aliases=['addq']
    )
    @blacklist_check()
    @ensure_voice()
    async def addqueue(self, ctx, name: str):
        playlist = playlistcol.find_one(
            {
                'guild_id': ctx.guild.id,
                'name': name
            }
        )
        if playlist != None:
            if ctx.voice_client != None:
                if ctx.voice_client.channel != ctx.author.voice.channel:
                    await ctx.send(
                        embed=create_embed(
                            'You have to be in the same channel as the bot to use this command'
                        ),
                        delete_after=10
                    )
                else:
                    queue = queuecol.find_one({'guild_id': ctx.guild.id})
                    if queue['size'] == 0:
                        await ctx.send(
                            embed=create_embed(
                                'The queue is empty'
                            ),
                            delete_after=10
                        )
                    else:
                        playlistcol.update_one(
                            {
                                'guild_id': ctx.guild.id,
                                'name': name
                            },
                            {
                                '$push': {
                                    'song_list': {
                                        '$each': queue['queue']
                                    }
                                },
                                '$inc': {
                                    'size': queue['size']
                                }
                            }
                        )
                        await ctx.send(
                            embed=create_embed(
                                f'{queue["size"]} songs from queue added to playlist {name}'
                            ),
                            delete_after=10
                        )
            else:
                await ctx.send(
                    embed=create_embed(
                        'Bot was not connected to any voice channel'
                    ),
                    delete_after=10
                )
        else:
            await ctx.send(
                embed=create_embed(
                    f'Playlist **{name}** not found\nNote: Try adding " " to your playlist name if it contains multiple words'
                ),
                delete_after=10
            )

    @playlist.command(
        name='remove',
        description='Remove a song from an existing playlist',
        usage='`.playlist remove [song number] [playlist name]`',
        aliases=['rm']
    )
    @blacklist_check()
    async def remove(self, ctx, position: int, *, name: str):
        playlist = playlistcol.find_one(
            {
                'guild_id': ctx.guild.id,
                'name': name
            }
        )
        if playlist != None:
            if 1 <= position <= playlist['size']:
                info = playlist['song_list'][position-1]
                playlistcol.update_one(
                    {
                        'guild_id': ctx.guild.id,
                        'name': name
                    },
                    {
                        '$unset': {
                            f'song_list.{position-1}': ''
                        },
                        '$inc': {
                            'size': -1
                        }
                    }
                )
                playlistcol.update_one(
                    {
                        'guild_id': ctx.guild.id,
                        'name': name
                    },
                    {
                        '$pull': {
                            'song_list': None
                        }
                    }
                )
                await ctx.send(
                    embed=create_embed(
                        f'Song [{info["title"]}]({info["url"]}) deleted from **{name}**'
                    ),
                    delete_after=10
                )
            else:
                await ctx.send(
                    embed=create_embed(
                        f'The playlist have **{playlist["size"]}** songs, but you specified more than that!'
                    )
                )
        else:
            await ctx.send(
                embed=create_embed(
                    f'Playlist **{name}** not found'
                )
            )

    @playlist.command(
        name='list',
        description='List the songs in an existing playlist',
        usage='`.playlist list [playlist name] [page]`',
        aliases=['ls']
    )
    @blacklist_check()
    async def _list(self, ctx, name: str, page: int = 1):
        playlist = playlistcol.find_one(
            {
                'guild_id': ctx.guild.id,
                'name': name
            }
        )
        if playlist != None:
            if playlist['size'] == 0:
                await ctx.send(
                    embed=create_embed(
                        'The playlist is empty'
                    ),
                    delete_after=10
                )
            else:
                output = ''
                song_list = playlist['song_list']
                pages = math.ceil(playlist['size']/10)
                if 1 <= page <= pages:
                    counter = 1 + (page-1)*10
                    for song in song_list[(page-1)*10:page*10]:
                        output += f'{counter}. [{song["title"]}]({song["url"]})\n'
                        counter += 1
                    embed = discord.Embed(
                        colour=discord.Colour.from_rgb(182,7,7),
                        description=output,
                        title=f'**{name}**',
                        timestamp=ctx.message.created_at
                    )
                    embed.add_field(
                        name='Entries',
                        value=f"{playlist['size']}"
                    )
                    embed.set_footer(
                        text=f'Page {page} of {pages} | use .playlist list [playlist name] [page]'
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
        else:
            ctx.send(
                embed=create_embed(
                    'The playlist does not exist\nNote: Try adding " " to your playlist name'
                )
            )

    # Event listener
    @commands.Cog.listener()
    async def on_ready(self):
        queues = queuecol.find()
        for queue in queues:
            guild = self.client.get_guild(queue['guild_id'])
            voice = guild.voice_client
            if voice == None:
                voice_channel = guild.get_channel(queue['voice_channel'])
                voice = await voice_channel.connect(reconnect=True)
                if queue['state'] == 'Playing':
                    if queue['size'] >= 1:
                        if queue['loop'] != 'one':
                            queuecol.update_one(
                                {'guild_id': guild.id},
                                {
                                    '$inc': {
                                        'pointer': -1
                                    }
                                }
                            )
                        self.play_song(guild)
                        text_channel = guild.get_channel(queue['text_channel'])
                        await text_channel.send(
                            embed=create_embed(
                                'Bot was restarted, playing from the most recent song in queue'
                            ),
                            delete_after=10
                        )
            else:
                if voice.is_paused():
                    if queue['state'] == 'Playing':
                        if queue['size'] >= 1:
                            voice.resume()
                elif not voice.is_playing():
                    if queue['state'] == 'Playing':
                        if queue['size'] >= 1:
                            self.play_song(guild)

    @commands.Cog.listener()
    async def on_disconnect(self):
        queues = queuecol.find()
        for queue in queues:
            guild = self.client.get_guild(queue['guild_id'])
            if guild.voice_client.is_playing():
                guild.voice_client.pause()

    @commands.Cog.listener()
    async def on_resumed(self):
        queues = queuecol.find()
        for queue in queues:
            guild = self.client.get_guild(queue['guild_id'])
            voice = guild.voice_client
            if voice == None:
                voice_channel = guild.get_channel(queue['voice_channel'])
                voice = await voice_channel.connect(reconnect=True)
                if queue['state'] == 'Playing':
                    if queue['size'] >= 1:
                        self.play_song(guild)
                        text_channel = guild.get_channel(queue['text_channel'])
                        await text_channel.send(
                            embed=create_embed(
                                'Bot was restarted, playing from the most recent song in queue'
                            ),
                            delete_after=10
                        )
            else:
                if voice.is_paused():
                    if queue['state'] == 'Playing':
                        if queue['size'] >= 1:
                            voice.resume()
                elif not voice.is_playing():
                    if queue['state'] == 'Playing':
                        if queue['size'] >= 1:
                            self.play_song(guild)

    # Error handler
    @play.error
    async def play_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                embed=create_embed(
                    'The play command also need a link or search keyword to work'
                ),
                delete_after=10
            )

    @dequeue.error
    async def dequeue_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=create_embed(
                    'Please use the correct argument'
                ),
                delete_after=10
            )

    @add.error
    async def add_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                embed=create_embed(
                    'Please specify the correct argument'
                )
            )


# Add cog
def setup(client):
    client.add_cog(Music(client))
