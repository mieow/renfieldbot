import discord
import mysql.connector
from discord.ext import commands
from tabulate import tabulate


class Monitor(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None

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


def setup(bot):
	bot.add_cog(Monitor(bot))
