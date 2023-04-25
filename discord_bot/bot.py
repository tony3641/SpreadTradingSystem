import os
import discord
from dotenv import load_dotenv
from ib_insync import *
from numpy import double
import numpy as np
import math
from datetime import datetime
from account_management import *


ib = IB()
#ib.disconnect()
util.startLoop()
ib.connect('127.0.0.1', 4001, clientId=0)
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    print(message.content)
    if message.author == client.user:
        return

    if message.content.startswith('!account'):
        output=query_account_info_return_str(ib)
        #print(output)
        response = f"{output}"
        await message.channel.send(response)
        
    if message.content.startswith('!index'):
        output=get_index_quote_return_str(ib)
        response = f"{output}"
        await message.channel.send(response)
   
client.run(TOKEN)
