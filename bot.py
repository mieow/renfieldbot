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
LOG_HOME = os.getenv('LOG_HOME')
DISCORDLOG = LOG_HOME + '/discord.log'

# BUGS
#
# X messages should use current display name - is discord caching it?
# - update character name in members table, as well as player name

# WISH LIST
#
# - able to be added to other servers
#		- check linear commands
#		- confirm other commands
#		- check category exists before trying to create a linear in it
#		- niceness - ensure ppl can only delete lines for their server
# - ST message Renfield privately and he says what they tell
# X give compliment when you say hello
# - sign in when you say hello and an event is on
# X remove .hello
# - Settings
#		X set storyteller role (admin_role)
#		X set Linears category (linear_category)
#		X max number of linears (max_linears = 3)
#		- set room change announcements on/off
#		- set room announcement channel
#		- set honorific (honorific = Master)
#		- set error message (error_msg = I'm sorry
# - chat log
#		- start logging
#		- stop logging
#		- ensure file doesn't get too big
#		- download chat log
#		- remind x lines when logging is enabled
#		- list all channels in server that have logs
# - wordpress API link for access to character database
# - play mp3 at specified intervals
#
# send PM: await ctx.author.send('boop!')
# get PM:
#	@client.event
#	async def on_message(message):
#		if message.channel.id == message.author.dm_channel.id: # dm #only
#			# do stuff here #
#		elif not message.guild: # group dm only
#			# do stuff here #
#		else: # server text channel
#			# do stuff here #



# logger = logging.getLogger('discord')
# logger.setLevel(logging.DEBUG)
# handler = logging.FileHandler(filename=DISCORDLOG, encoding='utf-8', mode='w')
# handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
# logger.addHandler(handler)


description = 'GVLARP Renfield Bot'
bot = commands.Bot(command_prefix='.', description=description)
bot.load_extension("niceness")
bot.load_extension("events")
bot.load_extension("diceroller")
bot.load_extension("linears")
bot.load_extension("monitor")
bot.load_extension("settings")


# Connect to Discord when ready
@bot.event
async def on_ready():
	print(bot.user.id)
	print(bot.user.name)
	print('---------------')
	print('Renfield is at your service!')
	print('Running with discord.py version: ' + discord.__version__)

# # Ping the bot
# @bot.command(name='hello', help='Is the bot listening?')
# async def ping(ctx):
	# '''Check that Renfield is listening'''
	# author = ctx.message.author.display_name
	# #server = ctx.message.guild.name
	# await ctx.send('Yes, Master {}, I am at your command!'.format(author))
 


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


# # Logging
# @bot.event
# async def on_message(message):
	# if message.author == bot.user:
		# return
	

if __name__ == '__main__':
	try:
		bot.run(TOKEN)
	except Exception as e:
		print('Renfield is not waking up')
		print(e)
	finally:
		print('Renfield has gone back to bed')



#-------------------------------
# Launch instance
# - amazon Linux 2, 64bit (x86) (free tier)
# - t2.micro (free tier)
# - [ review and launch ]
# - Launch
# - existing key pair

# EC2 -> Elastic IPs
# - [Allocate Elastic IP address]

# Log on with SSH to instance as ec2-user, with key pair
#     ec2-user> sudo -i

# Update OS packages
#     root> yum update
#

# Add renfield user
#     root> adduser renfield
#     root> su - renfield
#     root> mkdir .ssh
#     root> chmod 700 .ssh
#     root> touch .ssh/authorized_keys
#     root> chmod 600 .ssh/authorized_keys
#     root> vi .ssh/authorized_keys
# Paste in renfield's public key

# Start up MariaDB as a service
#  https://techviewleo.com/how-to-install-mariadb-server-on-amazon-linux/
# 

# Set up MySQL Database
#     root> mysql -u root -p
# CREATE USER 'renfield'@'localhost' IDENTIFIED BY '6xFi*@8v4B6K';
# CREATE DATABASE discordbot;
# GRANT ALL PRIVILEGES ON *.* TO 'renfield'@'localhost';
# SHOW GRANTS FOR 'renfield'@'localhost';
# exit
#     root> mysql -u renfield -p discordbot
# ...

# Update python3
#     renfield> python3 -m pip install --upgrade pip
#     renfield> python3 -m pip list --outdated
#     renfield> python3 -m pip install --upgrade discord.py
#     renfield> python3 -m pip install --upgrade mysql-connector-python
#     renfield> python3 -m pip install --upgrade tabulate
#     renfield> python3 -m pip install --upgrade python-dotenv
#     renfield> python3 -m pip install --upgrade <module>

# set up directory structure
# upload python files
# export tables and data from old database
#	mysqldump -u root -p --add-drop-table discordbot > dump.sql
# read into new database
#   mysql  -u root -p discordbot < dump.sql
# set up bot as a service
# https://pythondiscord.com/pages/guides/python-guides/discordpy/
