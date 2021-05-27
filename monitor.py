import discord
from discord.ext import commands
import mysql.connector
import os
import renfield_sql
from common import check_is_auth
from tabulate import tabulate
from dotenv import load_dotenv

load_dotenv()
LOG_HOME = os.getenv('LOG_HOME')
	
class Monitor(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		
	# def check_is_auth(self, ctx):
		# return "Coterie Members" in author.roles

	# @commands.command(name='test', help='Test command')
	# @check_is_auth()
	# async def test(self, ctx):
		# print(", ".join([str(r.name) for r in ctx.message.author.roles]))
		# print (ctx.message.author.guild_permissions.administrator or (admin_role.lower() in [y.name.lower() for y in ctx.message.author.roles]))
		# # try:
			# # voice_channel_list = ctx.guild.voice_channels

			# # #getting the members in the voice channel
			# # for voice_channels in voice_channel_list:
				# # #list the members if there are any in the voice channel
				# # if len(voice_channels.members) != 0:
					# # if len(voice_channels.members) == 1:
						# # await ctx.send("{} member in {}".format(len(voice_channels.members), voice_channels.name))
					# # else:
						# # await ctx.send("{} members in {}".format(len(voice_channels.members), voice_channels.name))
					# # for members in voice_channels.members:
						# # #if user does not have a nickname in the guild, send thier discord name. Otherwise, send thier guild nickname
						# # if members.nick == None:
							# # await ctx.send(members.name)
						# # else:
							# # await ctx.send(members.nick)
		# # except Exception as e:
			# # print(e)
			# # await ctx.send('ERROR')	

	@commands.Cog.listener()
	async def on_message(self, message):
		if message.author == self.bot.user:
			return
		server = message.guild.name
		#botname = "{}".format(self.bot.user.display_name).lower()
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
