import discord
from discord.ext import commands
import mysql.connector
import os
import renfield_sql
#from common import check_is_auth
#from common import parse_command
from tabulate import tabulate
from dotenv import load_dotenv

load_dotenv()
HOMEGUILD = os.getenv('DISCORD_GUILD')
	
class Monitor(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		

	@commands.Cog.listener()
	async def on_message(self, message):
		if message.author == self.bot.user:
			return
		if message.author.dm_channel is not None and message.channel.id == message.author.dm_channel.id: # dm #only
		
			server = None	# name of server person sending message is logged into
			cname = ""		# name of character person sending message is logged in as
			vchannel = None	# voice channel person sending message is logged in to

			# is the message author currently logged in to any voice channels?
			# if so, I can use that to guess their character name
			# Get the list of mutual guilds
			mutual = message.author.mutual_guilds
			# go through each guild
			for mguild in mutual:
						
				# get the list of voice channels
				vchannels = mguild.voice_channels
				# go through each voice channel
				for vch in vchannels:
					# get the list of users in the voice channel
					members = vch.members
					# go through each voice channel
					for member in members:
						# is this user in this voice channel?
						if member.id == message.author.id:
							server = mguild
							vchannel - vch
							if member.nick is None:
								cname = member.name
							else:
								cname = member.nick
			
			
			# If they aren't in a voice channel, I can
			# see if they are in the main GV guild
			if vchannel is None:
				botguilds = self.bot.guilds
				for bguild in botguilds:
					print(bguild.name)
					if bguild.name == HOMEGUILD:
						#print("guild match")
						members = await bguild.fetch_members(limit=150).flatten()
						for member in members:
							print(member.name)
							# is this user in this guild?
							if member.id == message.author.id:
								server = bguild
								if member.nick is None:
									cname = member.name
								else:
									cname = member.nick
			
			if cname == "":
				await message.author.send("I'm listening, {}, but I can't find you in the {} server.".format(message.author.display_name, HOMEGUILD))
			else:
				await message.author.send("I'm listening, {}.".format(cname))

			# Now I know who I'm talking to and where they are connected from
			# I need to work out what they want.
			msg_info = parse_message(message)
			
			# command = help
			# - give them a list of the commands they can use, and the format
			
			# command = tell <name> "<message>"
			# - give a message to someone in PM
			# - Jack. I have a message from Esteban. "<message>"
			
			# command = speak / <server> / <channel> "<message>"
			# - talk into the channel and make Renfield say something verbatim
			# - Storyteller / channel owner only
			
			# command = block / <server> / <character> / <delivery_notification>
			# where <delivery_notification> is 'yes' or 'no' and indicates if you
			# want the sending character to know their message was not delivered
			# - block characters from sending you messages through Renfield
			

					
				#await client.send_message(message.channel, "3\n2\n\1\nTime's up!", tts=True)
				#https://stackoverflow.com/questions/50791247/can-an-automatic-voice-be-programmed-for-a-discord-music-bot
				#https://stackoverflow.com/questions/53604339/how-do-i-make-my-discord-py-bot-play-mp3-in-voice-channel
		
		elif not message.guild: # group dm only
			return
		else: # server text channel
			
			server = message.guild.name
			botname = "{}".format(message.guild.me.display_name).lower()
			msgtst = message.content.lower()
			if botname in msgtst:
				if "hello" in msgtst or "hi" in msgtst or "greetings" in msgtst or "good evening" in msgtst:
					try:
						mydb = renfield_sql.renfield_sql()
						nice = mydb.get_nice(server)
						await message.channel.send("Hello {}. {}".format(message.author.display_name, nice))
					except Exception as e:
						print(e)
				if "fuck you" in msgtst or "fuck off" in msgtst or "get fucked" in msgtst or "go fuck yourself" in msgtst:
					await message.channel.send("Fuck you too, {}.".format(message.author.display_name))
				# elif "help" in msgtst:
					# await message.channel.send("{}, you can type '.help' for a list of commands or look at the GV Discord Webpage https://www.gvlarp.com/resources/discord.".format(message.author.display_name))
				elif "thanks" in msgtst or "thank you" in msgtst:
					await message.channel.send("You are welcome, {}".format(message.author.display_name))
				# else:
					# await message.channel.send("Can I help you, {}?".format(message.author.display_name))


		# serverid  = message.guild.id
		# channelid = message.channel.id
		# logpath = LOG_HOME + "/{}/{}.log".format(serverid,channelid)
		# ensure_dir(logpath)
		# filesize = os.stat(logpath).st_size
		# f = open(logpath, "a")
		# f.write("{}: {}\n\n".format(message.author.display_name, message.content))
		# f.close
		# await message.channel.send("Log size {} bytes".format(filesize))


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def setup(bot):
	bot.add_cog(Monitor(bot))
