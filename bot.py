#!/usr/bin/env python3

import os
import mysql.connector
import discord
import renfield_sql
import logging
import wordpress_api

from dotenv import load_dotenv
from discord.ext import commands
from discord_slash import cog_ext, SlashCommand, SlashContext
from common import write_key

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
GUILDID = int(os.getenv('DISCORD_GUILD_ID'))
DATABASE_USERNAME = os.getenv('DATABASE_USERNAME')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
LOG_HOME = os.getenv('LOG_HOME')
DISCORDLOG = LOG_HOME + '/discord.log'

# BUGS
#
# - update character name in members table, as well as player name

# WISH LIST
#
# - able to be added to other servers
#		- check linear commands
#		- confirm other commands
#		- check category exists before trying to create a linear in it
#		- niceness - ensure ppl can only delete lines for their server
# - ST message Renfield privately and he says what they tell
# - send messages to other characters
#		- need to be able to ignore, and specify if delivery receipt allowed
# - sign in when you say hello and an event is on
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
# - reminder/reference: page nos, pools, diff, - player contributed
# - track damage taken
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

intents = discord.Intents.default()
intents.members = True

description = 'GVLARP Renfield Bot'
bot = commands.Bot(command_prefix='.', description=description, intents=intents)

slash = SlashCommand(bot, sync_commands=True, sync_on_cog_reload=True)

bot.load_extension("niceness")
bot.load_extension("events")
bot.load_extension("diceroller")
bot.load_extension("settings")
bot.load_extension("wordpress_api")


# Connect to Discord when ready
@bot.event
async def on_ready():
	print(bot.user.id)
	print(bot.user.name)
	print('---------------')
	print('Renfield is at your service!')
	print('Running with discord.py version: ' + discord.__version__)
	# create encryption key, if needed
	print('Encrypyion Key Generation: ' + write_key())

# Ping the bot
@slash.slash(name="hello", description="Get status of Renfield", guild_ids=[GUILDID,1144585195316584488])
async def _hello(ctx):
	'''Check that Renfield is listening'''
	author = ctx.author.display_name
	nameid = ctx.author.id
	server = ctx.guild.name
	mydb = renfield_sql.renfield_sql()
	wordpress_site = mydb.get_bot_setting("wordpress_site", "none", server)
	
	message = 'Yes, Master {}, I am at your command! This is the "{}" guild server.'.format(author,server)
	
	if wordpress_site != "none":
		if wordpress_api.curl_checkAPI(server):
			message = message + " I have failed to connect to the {} Wordpress site".format(wordpress_site)
		else:
			message = message + " I have successfully conencted to the Wordpress site."
		
	await ctx.send(message)
 

@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandNotFound):
		await ctx.send("I'm sorry Master, I do not know that command.")



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

# create an IAM role with polly access

# Log on with SSH to instance as ec2-user, with key pair
#     ec2-user> sudo -i

# Install extra OS Packages
#	  root> yum install libcurl-devel
#	  root> yum install gcc
#	  root> yum install -y openssl-devel
#	  root> yum install python3-devel

# Update OS packages
#     root> yum update

# Install ffmpeg

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
#     renfield> python3 -m pip install --upgrade discord-py-interactions
#     renfield> python3 -m pip install --upgrade pycurl
#     renfield> python3 -m pip install --upgrade certifi
#     renfield> python3 -m pip install --upgrade <module>
#     renfield> pip install cryptography
# pip install boto3

# set up directory structure
# upload python files
# export tables and data from old database
#	mysqldump -u root -p --add-drop-table discordbot > dump.sql
# read into new database
#   mysql  -u root -p discordbot < dump.sql
# set up bot as a service
# https://pythondiscord.com/pages/guides/python-guides/discordpy/


# Set AWS Polly
# https://docs.aws.amazon.com/polly/latest/dg/get-started-what-next.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html

# Invite the bot to your server: https://discord.com/api/oauth2/authorize?client_id=690906493742088242&permissions=1099511630848&scope=bot%20applications.commands
# add manage roles
