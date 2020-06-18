#!/usr/bin/env python3

import os
import mysql.connector
import discord
import renfield_sql
import logging

from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
DATABASE_USERNAME = os.getenv('DATABASE_USERNAME')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
DISCORDLOG = '/home/renfield/logs/discord.log'

logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)
handler = logging.FileHandler(filename=DISCORDLOG, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


description = 'GVLARP Renfield Bot'
bot = commands.Bot(command_prefix='.', description=description)
bot.load_extension("niceness")
bot.load_extension("events")
bot.load_extension("diceroller")
bot.load_extension("linears")
#bot.load_extension("monitor")


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

# Event
# discord.on_voice_state_update(member, before, after)
# VoiceState -> channel -> VoiceChannel
# check if before <> after
# then output to tannoy (with notification?)
@bot.event
async def on_voice_state_update(member, before, after):
	server = member.guild
	for outchannel in server.channels:
		if outchannel.name == "renfields-cubby-hole":
			categoryid = outchannel.category_id
			break
			
	# for outchannel in server.channels:
		# if outchannel.name == "jane-testing":
			# break
			
	aftername = ""
	afterid = 0
	beforename = ""
	beforeid = 0
	if after.channel is not None:
		aftername = after.channel.name
		afterid = after.channel.category_id
	if before.channel is not None:
		beforename = before.channel.name
		beforeid = before.channel.category_id
			
	quiet = 0
	if "quiet" in [y.name.lower() for y in member.roles]:
		quiet = 1
	if aftername == "Voice: Storytellers Only":
		quiet = 1
	if beforename == "Voice: Storytellers Only":
		quiet = 1
	if beforeid != categoryid and afterid != categoryid:
		quiet = 1
		
	if not quiet:
		if aftername != beforename:
			if beforename == "":
				await outchannel.send("{} has entered the {}".format(member.display_name, after.channel.name))
			elif aftername == "":
				await outchannel.send("{} has left the {}".format(member.display_name, before.channel.name))
			else:
				await outchannel.send("{} has moved from the {} to the {}.".format(member.display_name, before.channel.name, after.channel.name))
	

if __name__ == '__main__':
	try:
		bot.run(TOKEN)
	except Exception as e:
		print('Renfield is not waking up')
		print(e)
	finally:
		print('Renfield has gone back to bed')

