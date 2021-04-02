import discord
import mysql.connector
import os
from discord.ext import commands
from tabulate import tabulate
from dotenv import load_dotenv

load_dotenv()
LOG_HOME = os.getenv('LOG_HOME')


class Monitor(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name='test', help='Test command')
	async def test(self, ctx):
		try:
			voice_channel_list = ctx.guild.voice_channels

			#getting the members in the voice channel
			for voice_channels in voice_channel_list:
				#list the members if there are any in the voice channel
				if len(voice_channels.members) != 0:
					if len(voice_channels.members) == 1:
						await ctx.send("{} member in {}".format(len(voice_channels.members), voice_channels.name))
					else:
						await ctx.send("{} members in {}".format(len(voice_channels.members), voice_channels.name))
					for members in voice_channels.members:
						#if user does not have a nickname in the guild, send thier discord name. Otherwise, send thier guild nickname
						if members.nick == None:
							await ctx.send(members.name)
						else:
							await ctx.send(members.nick)
		except Exception as e:
			print(e)
			await ctx.send('ERROR')	

	# @commands.Cog.listener()
	# async def on_message(self, message):
		# if message.author == self.bot.user:
			# return
		# msgtst = message.content.lower()
		# if "renfield" in msgtst:
			# if "hello" in msgtst:
				# await message.channel.send("Hello {}.".format(message.author.display_name))
			# # elif "help" in msgtst:
				# # await message.channel.send("{}, you can type '.help' for a list of commands or look at the GV Discord Webpage https://www.gvlarp.com/resources/discord.".format(message.author.display_name))
			# # elif "thanks" in msgtst:
				# # await message.channel.send("You are welcome, {}".format(message.author.display_name))
			# # elif "thankyou" in msgtst:
				# # await message.channel.send("You are welcome, {}".format(message.author.display_name))
			# # else:
				# # await message.channel.send("Can I help you, {}?".format(message.author.display_name))

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
