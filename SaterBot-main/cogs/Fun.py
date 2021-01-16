import discord
import time
import pymongo
import emoji
import os
import re
import urllib
import asyncio
import secrets
import unicodedata
import io
import functools
import aiohttp
import random
import colorthief
import requests
import safygiphy
from io import BytesIO
from datetime import datetime
from helper import *
from discord.ext import commands
from discord.ext.commands import clean_content
from utils import cache, http, default, argparser
from ext import embedtobox

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
        
class Fun(commands.Cog, name='Fun'):
    def __init__(self, client):
        self.client = client
        self.messages = {}
        self.session = aiohttp.ClientSession()
    
    async def randomimageapi(self, ctx, url, endpoint):
        try:
            r = await http.get(url, res_method="json", no_cache=True)
        except aiohttp.ClientConnectorError:
            return await ctx.send(embed=create_embed("The API seems to be down..."))
        except aiohttp.ContentTypeError:
            return await ctx.send(embed=create_embed("The API returned an error or didn't return JSON..."))
        await ctx.send(r[endpoint])
    
    @commands.Cog.listener()
    async def on_message_delete(self, message): 
        if message.guild is None: 
            return

        if message.author.bot: 
            return

        if not message.content: 
            return 

        self.messages[message.channel.id] = message

    @commands.command(
        name='snipe',
        description='Sends most recent deleted message.',
        usage='`.snipe`'
    )
    async def snipe(self, ctx): 
        message = self.messages.get(ctx.channel.id)
        if message is None: 
            await ctx.send(embed=create_embed('No recently deleted messages found'))
        else:
            ma = str(message.author)
            mc = message.content
            embed = discord.Embed(colour=discord.Colour.from_rgb(182,7,7), description=f"{mc}", timestamp=message.created_at)
            embed.set_author(name=f"{ma}", icon_url=message.author.avatar_url)
            await ctx.send(embed=embed)
     
    @commands.command(
        name="enlarge",
        description = "Enlarges the specified emoji.",
        usage = "`.enlarge <emoji>`",
        aliases=['bigemoji']
    )
    async def enlarge(self, ctx, emoji):
        try:
            if emoji[0] == '<':
                name = emoji.split(':')[1]
                emoji_name = emoji.split(':')[2][:-1]
                anim = emoji.split(':')[0]
                if anim == '<a':
                    url = f'https://cdn.discordapp.com/emojis/{emoji_name}.gif'
                else:
                    url = f'https://cdn.discordapp.com/emojis/{emoji_name}.png'
                try:
                    await ctx.send(url)
                except Exception as e:
                    print(e)
                    async with self.session.get(url) as resp:
                        if resp.status != 200:
                            await ctx.send(embed=create_embed('Error: Emote not found.'))
                            return
                        img = await resp.read()

                    kwargs = {'parent_width': 1024, 'parent_height': 1024}
                    convert = False
                    task = functools.partial(bigEmote.generate, img, convert, **kwargs)
                    task = self.bot.loop.run_in_executor(None, task)
                    try:
                        img = await asyncio.wait_for(task, timeout=15)
                    except asyncio.TimeoutError:
                        await ctx.send(embed=create_embed("Error: Timed Out. Try again in a few seconds"))
                        return
                    await ctx.send(file=discord.File(img, filename=name + '.png'))
            
        except Exception as e:
            await ctx.send(embed=create_embed(f"Error, couldn't send emote.\n{e}"))
    
    @commands.command(
        name="combine",
        description="Combines 2 names together.",
        usage="`.combine <name1> <name2>`"
    )
    async def combine(self, ctx, name1: clean_content, name2: clean_content):
        name1letters = name1[:round(len(name1) / 2)]
        name2letters = name2[round(len(name2) / 2):]
        ship = "".join([name1letters, name2letters])
        emb = discord.Embed(colour=discord.Colour.from_rgb(182,7,7), description = f"{ship}")
        emb.set_author(name=f"{name1} + {name2}")
        await ctx.send(embed=emb)
    
    @commands.command(aliases=['8ball'])
    async def eightball(self, ctx, *, _ballInput: clean_content):
        choiceType = random.choice(["(Affirmative)", "(Non-committal)", "(Negative)"])
        if choiceType == "(Affirmative)":
            prediction = random.choice(["It is certain ", 
                                        "It is decidedly so ", 
                                        "Without a doubt ", 
                                        "Yes, definitely ", 
                                        "You may rely on it ", 
                                        "As I see it, yes ",
                                        "Most likely ", 
                                        "Outlook good ", 
                                        "Yes ", 
                                        "Signs point to yes "]) + ":8ball:"

            emb = (discord.Embed(title="Question: {}".format(_ballInput), colour=discord.Colour.from_rgb(182,7,7), description=prediction))
        elif choiceType == "(Non-committal)":
            prediction = random.choice(["Reply hazy try again ", 
                                        "Ask again later ", 
                                        "Better not tell you now ", 
                                        "Cannot predict now ", 
                                        "Concentrate and ask again "]) + ":8ball:"
            emb = (discord.Embed(title="Question: {}".format(_ballInput), colour=discord.Colour.from_rgb(182,7,7), description=prediction))
        elif choiceType == "(Negative)":
            prediction = random.choice(["Don't count on it ", 
                                        "My reply is no ", 
                                        "My sources say no ", 
                                        "Outlook not so good ", 
                                        "Very doubtful "]) + ":8ball:"
            emb = (discord.Embed(title="Question: {}".format(_ballInput), colour=discord.Colour.from_rgb(182,7,7), description=prediction))
        emb.set_author(name='Magic 8 Ball', icon_url='https://www.horoscope.com/images-US/games/game-magic-8-ball-no-text.png')
        await ctx.send(embed=emb)
    
    @commands.command(aliases=['gayscanner', 'gay'])
    async def gayrate(self, ctx, *, user: clean_content=None):
        if not user:
            user = ctx.author.name
        gayness = random.randint(0,100)
        emb = discord.Embed(description=f"Gayrate of **{user}**", colour=discord.Colour.from_rgb(182,7,7))
        emb.add_field(name="**Gayrate:**", value=f"{gayness}% gay")
        emb.set_author(name="Gayrate Machine™", icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/ICA_flag.svg/2000px-ICA_flag.svg.png")
        await ctx.send(embed=emb)
    
    @commands.command(
        name="urban",
        description="Sends the definition of the specified word.",
        usage="`.urban [word]`"
    )
    async def urban(self, ctx, *, search: commands.clean_content):
        async with ctx.channel.typing():
            try:
                url = await http.get(f'https://api.urbandictionary.com/v0/define?term={search}', res_method="json")
            except Exception:
                return await ctx.send(embed=create_embed("Urban API returned invalid data... might be down atm."))

            if not url:
                return await ctx.send(embed=create_embed("I think the API broke..."))

            if not len(url['list']):
                return await ctx.send(embed=create_embed("Couldn't find your search in the dictionary..."))

            result = sorted(url['list'], reverse=True, key=lambda g: int(g["thumbs_up"]))[0]

            definition = result['definition']
            if len(definition) >= 1000:
                definition = definition[:1000]
                definition = definition.rsplit(' ', 1)[0]
                definition += '...'

            await ctx.send(embed=create_embed(f"**📚 Definitions for {result['word']}\nDefinition: {definition}**"))
    
    @commands.command(
        name="cat",
        description="Sends a random image of a cat.",
        usage="`.cat`"
    )
    async def cat(self, ctx):
        await self.randomimageapi(ctx, 'https://api.alexflipnote.dev/cats', 'file')
                                              
    @commands.command(
        name="dog",
        description="Sends a random image of a dog.",
        usage="`.dog`"
    )
    async def dog(self, ctx):
        await self.randomimageapi(ctx, 'https://api.alexflipnote.dev/dogs', 'file')
    
    @commands.command(
        name="duck",
        description="Sends a random image of a duck.",
        usage="`.duck`"
    )
    async def duck(self, ctx):
        await self.randomimageapi(ctx, 'https://random-d.uk/api/v1/random', 'url')
    
    @commands.command(
        name="coffee",
        description="Sends a random image of a coffee.",
        usage="`.coffee`"
    )
    async def coffee(self, ctx):
        await self.randomimageapi(ctx, 'https://coffee.alexflipnote.dev/random.json', 'file')
    
    @commands.command(
        name="coinflip",
        description="Flips a coin.",
        usage="`.coinflip`",
        aliases=['flip', 'coin']
    )
    async def coinflip(self, ctx):
        coinsides = ['Heads', 'Tails']
        await ctx.send(embed=create_embed(f"**{ctx.author.name}** flipped a coin and got **{random.choice(coinsides)}**!"))
    
    @commands.command(
        name="respect",
        description="Pays respect to the specified user.",
        usage="`.respect [@user] [reason]`"
    )
    async def respect(self, ctx, *, text: commands.clean_content = None):
        hearts = ['❤', '💛', '💚', '💙', '💜']
        reason = f"for **{text}** " if text else ""
        await ctx.send(embed=create_embed(f"**{ctx.author.name}** has paid their respect {reason}{random.choice(hearts)}"))
    
    @commands.command(
        name="reverse",
        description="Reverses your message.",
        usage="`.reverse` [message]`"
    )
    async def reverse(self, ctx, *, text: str):
        t_rev = text[::-1].replace("@", "@\u200B").replace("&", "&\u200B")
        await ctx.send(embed=create_embed(f"🔁 {t_rev}"))
    
    @commands.command(
        name="password",
        description="Generates a random password.",
        usage="`.password [length]`"
    )
    async def password(self, ctx, nbytes: int = 18):
        if nbytes not in range(3, 1401):
            return await ctx.send(embed=create_embed("I only accept any numbers between 3-1400"))
        if hasattr(ctx, 'guild') and ctx.guild is not None:
            await ctx.send(f"Sending you a private message with your random generated password **{ctx.author.name}**")
        await ctx.author.send(f"🎁 **Here is your password:**\n{secrets.token_urlsafe(nbytes)}")
    
    @commands.command(
        name="hotrate",
        description="Shows you how hot the specified user is.",
        usage="`.hotrate [@user]`",
        aliases=['howhot', 'hot']
    )
    async def hotrate(self, ctx, *, user: discord.Member = None):
        """ Returns a random percent for how hot is a discord user """
        user = user or ctx.author

        random.seed(user.id)
        r = random.randint(1, 100)
        hot = r / 1.17

        emoji = "💔"
        if hot > 25:
            emoji = "❤"
        if hot > 50:
            emoji = "💖"
        if hot > 75:
            emoji = "💞"

        await ctx.send(embed=create_embed(f"**{user.name}** is **{hot:.2f}%** hot {emoji}"))
    
    @commands.command(
        name="slot",
        description="Rolls a slotmachine",
        usage="`.slot`",
        aliases=['slots', 'bet']
    )
    async def slot(self, ctx):
        emojis = "🍎🍊🍐🍋🍉🍇🍓🍒"
        a = random.choice(emojis)
        b = random.choice(emojis)
        c = random.choice(emojis)

        slotmachine = f"**[ {a} {b} {c} ]\n{ctx.author.name}**,"

        if (a == b == c):
            await ctx.send(embed=create_embed(f"{slotmachine} All matching, you won! 🎉"))
        elif (a == b) or (a == c) or (b == c):
            await ctx.send(embed=create_embed(f"{slotmachine} 2 in a row, you won! 🎉"))
        else:
            await ctx.send(embed=create_embed(f"{slotmachine} No match, you lost 😢"))
    
    @commands.command(
        name="dick",
        description="Sends the mentioned user's dick size.",
        usage="`.dick [@user]`",
        aliases=['dong', 'penis']
    )
    async def dick(self, ctx, *, user: discord.Member = None):
        await ctx.message.delete()
        if user is None:
            user = ctx.author
        size = random.randint(1, 15)
        dong = ""
        for _i in range(0, size):
            dong += "="
        em = discord.Embed(description=f"8{dong}D", colour=discord.Colour.from_rgb(182,7,7))
        em.set_author(name=f"{user}'s Dick Size", icon_url=user.avatar_url)
        await ctx.send(embed=em)
    
    @commands.command(
        name="gif",
        description="Sends a random gif with the given tag.",
        usage="`.gif [tag]`"
    )
    async def gif(self, ctx, *, tag):
        g = safygiphy.Giphy()
        tag = tag.lower()
        gif = g.random(tag=tag)
        colour = discord.Colour.from_rgb(182,7,7)
        em = discord.Embed(colour=colour)
        em.set_image(url=str(gif.get('data', {}).get('image_original_url')))
        try:
            await ctx.send(embed=em)
        except discord.HTTPException:
            em_list = await embedtobox.etb(em)
            for page in em_list:
                await ctx.send(page)  
    
    @staticmethod
    def generate(img, convert, **kwargs):
        img = io.BytesIO(img)
        return img
            
def setup(client):
    client.add_cog(Fun(client))
