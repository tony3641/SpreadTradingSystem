import asyncio
import nest_asyncio
nest_asyncio.apply()
import discord
import logging
from dotenv import load_dotenv
import os
import signal
import sys
import time
from ib_insync import *
from discord.ext import commands
from command_handler import process_command
from account_management_util import TradingClient
from trading_util import *

trading_client = TradingClient()
discord_bot_token = None
bot = None

#ctrl-c handling
def signal_handler(sig, frame):
    logger.critical("ctrl-c detected.")
    if trading_client.IBClient is not None:
        logger.critical("IB session closed.")
        trading_client.IBClient.disconnect()
    sys.exit()
    
signal.signal(signal.SIGINT, signal_handler)

#logging initialization
log_folder = 'logs'
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
log_file_path = os.path.join(log_folder, 'trading_system.log')
logger = logging.getLogger("Trading System")
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

#init IB session
client_id_arr = [1, 2, 3]
for client_id in client_id_arr:
    try:
        trading_client.IBClient = IB()
        trading_client.IBClient.connect('127.0.0.1', 8331, clientId=client_id)
        logger.critical("IB session created, client ID = %d", client_id)
        break
    except Exception as e:
        logger.critical("IB client ID %d not available, trying next possible ID.", client_id)
        time.sleep(1)
        
with open('watch.txt', 'r') as file:
    for line in file:
        symbol, contract_type = line.strip().split()
        _, ticker = get_ticker_info(trading_client.IBClient, symbol, contract_type)
        trading_client.watchList.append(ticker)

# CLI Listener
async def cli_listener():
    while True:
        command = await asyncio.to_thread(input, "trade_sys>")
        command = command.strip()
        if command:
            logger.info(f"Get message from CLI: {command}")
            response = process_command(command, trading_client)
            print(response)            

# Discord Bot Setup
load_dotenv()
discord_bot_token = os.getenv('DISCORD_TOKEN')
if discord_bot_token is None:
    logger.error("Failed to load discord bot token!")
else:
    logger.critical("Discord bot token load successful")
intents = discord.Intents.default()
intents.message_content = True
trading_client.DiscordBot = commands.Bot(command_prefix=".", intents=intents)

@trading_client.DiscordBot.event
async def on_ready():
    logger.info("Discord connection established.")
    for guild in trading_client.DiscordBot.guilds:
        logger.info(f"Discord server : {guild.name}")
        for channel in guild.channels:
            if channel.name == "lost-alert":
                trading_client.BotAlertChannel = channel
                logger.info("Valid Discord alert channel found.")
            elif channel.name == "command":
                trading_client.BotCommandChannel = channel
                logger.info("Valid Discord command channel found.")
            

@trading_client.DiscordBot.event
async def on_message(message):
    logger.info("Get message from Discord bot.")
    if message.author == trading_client.DiscordBot.user:
        return
    if message.channel.name == trading_client.BotCommandChannel.name:
        logger.info(f"Get message from Discord channel {message.channel.name}: {message.content}")
        response = process_command(message.content, trading_client)
        await message.channel.send(response)

async def main():
    task_discord = asyncio.create_task(trading_client.DiscordBot.start(discord_bot_token))
    task_cli = asyncio.create_task(cli_listener())
    await asyncio.gather(task_discord, task_cli)

if __name__ == "__main__":
    logger.critical("Trading system launched.")
    asyncio.run(main())
