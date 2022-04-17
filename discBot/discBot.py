import sqlite3
import string, json
import requests
import discord
from discord.utils import get
from discord.ext import commands,tasks
from secret import TwitchClientID, TwitchClientSecret,Channel, DiscordToken

isLive=False
#чтобы не было спама

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

#твич
twitch_client_id= TwitchClientID
twitch_client_secret= TwitchClientSecret
channel = Channel




#Используя АПИ Твича подключаемся к нему и парсим запросы
def Twitch_checkUser():
    body = {
        'client_id': twitch_client_id,
        'client_secret': twitch_client_secret,
        "grant_type": 'client_credentials'
    }
    r = requests.post('https://id.twitch.tv/oauth2/token', body)
    keys = r.json()

    headers = {
        'Client-ID': twitch_client_id,
        'Authorization': 'Bearer ' + keys['access_token']
    }

    stream = requests.get('https://api.twitch.tv/helix/streams?user_login=' + channel, headers=headers)
    stream_data = stream.json();


    if len(stream_data['data']) == 1:
        data = stream_data['data'][0]
        title=data['title']
        streamer=data['user_name']
        game=data['game_name']
        thumbnail_url=data['thumbnail_url']
        stream = (title,streamer,game,thumbnail_url)
        return stream
    else:
        stream = "OFFLINE"
        return stream


#создаем бд и запускаем уведомления твича
@bot.event
async def on_ready():
    print('Я снова тут!')
    global base, cur
    base = sqlite3.connect('heckfy.db')
    cur = base.cursor()
    if base:
        print('DataBase connected...OK')
    twitchNotifications.start()


#каждый 10 секунд делаем запрос на стрим
@tasks.loop(seconds=10)
async def twitchNotifications():
    global isLive
    stream=Twitch_checkUser()
    channel = bot.get_channel(965047886184341544)
    if stream!="OFFLINE":
        if isLive == False:
            isLive = True
            await channel.send('Дибил сейчас стримит! ')
    else:
        if isLive ==True:
            isLive=False
            await channel.send('Дибил сейчас отдыхает:) ')


# # Command to add Twitch usernames to the json.
# @bot.command(name='addtwitch', help='Adds your Twitch to the live notifs.', pass_context=True)
# async def add_twitch(ctx, twitch_name):
#     # Opens and reads the json file.
#     with open('streamers.json', 'r') as file:
#         streamers = json.loads(file.read())
#
#     # Gets the users id that called the command.
#     user_id = ctx.author.id
#     # Assigns their given twitch_name to their discord id and adds it to the streamers.json.
#     streamers[user_id] = twitch_name
#
#     # Adds the changes we made to the json file.
#     with open('streamers.json', 'w') as file:
#         file.write(json.dumps(streamers))
#     # Tells the user it worked.
#     await ctx.send(f"Added {twitch_name} for {ctx.author} to the notifications list.")

# бот подключается к голосовому каналу
@bot.command()
async def join(ctx):
    global voice
    channel = ctx.message.author.voice.channel
    voice=get(bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()


# Бот отключается от голосового канала
@bot.command()
async def leave(ctx):
    channel = ctx.message.author.voice.channel
    voice=get(bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_connected():
        await voice.disconnect()
    else:
        voice = await channel.connect()


# выдача роли мута
@bot.command()
async def mute(ctx,member:discord.Member):
    await ctx.message.delete()
    mute = discord.utils.get(ctx.message.guild.roles,name='mute')
    await member.add_roles(mute)


# снятие роли мута
@bot.command()
async def unmute(ctx,member:discord.Member):
    await ctx.message.delete()
    mute = discord.utils.get(ctx.message.guild.roles,name='mute')
    await member.remove_roles(mute)

# !youtube
@bot.command()
async def youtube(ctx):
    author = ctx.message.author
    await ctx.send(f'{author.mention}, https://www.youtube.com/channel/UCDVln2Hn5O93tHSSrjNjqgg')

# !vkgroup
@bot.command()
async def vkgroup(ctx):
    author = ctx.message.author
    await ctx.send(f'{author.mention}, https://vk.com/heckfystream')

# !vk
@bot.command()
async def vk(ctx):
    author = ctx.message.author
    await ctx.send(f'{author.mention},  https://vk.com/heckfysu')

# !stream
@bot.command()
async def stream(ctx):
    author = ctx.message.author
    await ctx.send(f'{author.mention},  https://www.twitch.tv/heckfyrog')

# !addons
@bot.command()
async def addons(ctx):
    author = ctx.message.author
    await ctx.send(f'{author.mention},https://drive.google.com/file/d/1jEl2igJcE4kXdoGhA9_7h'
                   f'WR5zoTTdryE/view?usp=sharing')


# !info
@bot.command()
async def info(ctx):
    author = ctx.message.author
    await ctx.send(f'{author.mention}, команды бота:\n1) !stream - ссылка на стрим\n2) !vk - ссылка на '
                   f'мою страницу Вконтакте\n3) !vkgroup'
                   f' - ссылка на мою группу Вконтакте\n4) !youtube - ссылка на мой YouTube\n5) !addons '
                   f'- ссылка на мои аддоны')



# выдача роли фолловера
role_id = 964547703482748959


@bot.event
async def on_member_join(member):
    await member.add_roles(member.guild.get_role(role_id))
    await member.send('Привет я тут присматриваю за порядком, если нужна информация то пиши !info')
    for ch in bot.get_guild(member.guild.id).channels:
        if ch.name == 'основной':
            await bot.get_channel(ch.id).send(f'{member.mention}, круто что ты с нами в лс инфо')

# проверка количества предупреждений !status
@bot.command()
async def status(ctx):
    base.execute('CREATE TABLE IF NOT EXISTS "{}"(userid INT, count INT)'.format(ctx.message.guild.name))
    base.commit()
    warning = cur.execute('SELECT * FROM "{}" WHERE userid == ? '.format(ctx.message.guild.name),
                          (ctx.message.author.id,)).fetchone()
    if warning == None:
        await ctx.send(f'{ctx.message.author.mention}, у Вас нет предупреждений!')
    else:
        await ctx.send(f'{ctx.message.author.mention}, количество Ваших предупреждений - {warning[1]}.')

# модерация с использованием файла цензуры, файл to_json конвертирует тхт в джсон
@bot.event
async def on_message(message):
    if {i.lower().translate(str.maketrans('', '', string.punctuation)) for i in message.content.split(' ')} \
            .intersection(set(json.load(open('cenz.json')))) != set():
        await message.channel.send(f'{message.author.mention} не пиши такое больше плиз')
        await message.delete()

        name = message.guild.name

        base.execute('CREATE TABLE IF NOT EXISTS"{}"(userid INT, count INT)'.format(name))
        base.commit()
        warning = cur.execute('SELECT * FROM "{}" WHERE userid == ? '.format(name), (message.author.id,)).fetchone()

        if warning == None:
            cur.execute('INSERT INTO "{}" VALUES(?,?)'.format(name), (message.author.id, 1))
            base.commit()
            await message.channel.send(f'{message.author.mention}, первое предупреждение, на  5е - БАН')

        elif warning[1] == 1:
            cur.execute('UPDATE "{}" SET count==? WHERE userid == ?'.format(name), (2, message.author.id))
            base.commit()
            await message.channel.send(f'{message.author.mention}, второе предупреждение, на 5е - БАН')

        elif warning[1] == 2:
            cur.execute('UPDATE "{}" SET count==? WHERE userid == ?'.format(name), (3, message.author.id))
            base.commit()
            await message.channel.send(f'{message.author.mention}, третье предупреждение, на 5е - БАН')

        elif warning[1] == 3:
            cur.execute('UPDATE "{}" SET count==? WHERE userid == ?'.format(name), (4, message.author.id))
            base.commit()
            await message.channel.send(f'{message.author.mention}, четвертое предупреждение, на 5е - БАН')

        elif warning[1] == 4:
            cur.execute('UPDATE "{}" SET count==? WHERE userid == ?'.format(name), (5, message.author.id))
            base.commit()
            await message.channel.send(f'{message.author.mention}, прощай друг!')
            await message.author.ban(reason='Нарушение правил')

    await bot.process_commands(message)

# обнуление предупреждений !reset
@bot.command()
async def reset(ctx):
    base.execute('DELETE FROM "{}" WHERE userid == ?'.format(ctx.message.guild.name),
                 (ctx.message.author.id,)).fetchone()
    base.commit()
    await ctx.channel.send(f'{ctx.author.mention}, твои предупреждения обнулены!')


bot.run(DiscordToken)
