#!/usr/bin/env python3

import os
import mysql.connector
import discord
import random

from dotenv import load_dotenv
from discord.ext import commands
#from sqlalchemy import engine, create_engine
#from sqlalchemy.orm import sessionmaker
from tabulate import tabulate
from datetime import date
from datetime import datetime

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
DATABASE_USERNAME = os.getenv('DATABASE_USERNAME')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')

description = 'GVLARP Renfield Bot'
bot = commands.Bot(command_prefix='.', description=description)
bot.load_extension("niceness")
bot.load_extension("events")
bot.load_extension("diceroller")

# Connect to database
mydb = mysql.connector.connect(
  host="localhost",
  user=DATABASE_USERNAME,
  passwd=DATABASE_PASSWORD,
  database="discordbot"
)
mycursor = mydb.cursor()
bot.db = mydb


# Connect to Discord when ready
@bot.event
async def on_ready():
	print(bot.user.id)
	print(bot.user.name)
	print('---------------')
	print('Renfield is at your service!')

# Ping the bot
@bot.command(name='hello', help='Is Renfield listening?')
async def ping(ctx):
	'''Check that Renfield is listening'''
	author = ctx.message.author.display_name
	#server = ctx.message.guild.name
	await ctx.send('Yes, Master {}, I am at your command!'.format(author))
 


@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandNotFound):
		await ctx.send("I'm sorry Master, I do not know that command. Say '.help' to find out what I can understand.")


if __name__ == '__main__':
	try:
		bot.run(TOKEN)
	except Exception as e:
		print('Renfield is not waking up')
		print(e)
	finally:
		print('Renfield has gone back to bed')
		mycursor.close
		mydb.close

