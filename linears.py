import discord
import mysql.connector
from discord.ext import commands
import renfield_sql


class Linears(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None

	# start chat logging
	# stop chat logging
	# download log
	# remind that logging is happening
	# clear log
	
	# create new linear
	@commands.command(name='addlinear', help='Add channels for a linear')
	@commands.has_role('storytellers')
	async def addlinear(self, ctx,):
		server = ctx.message.guild

		# get the category for linears
		
		# set channel name based on the date
		channelname = "linear-channel"
		
		# check if channel already exists
		
		# create text channel
		#await server.create_text_channel(channelname, category=)

		# start logging?
		
		# create voice channel
		
	# remove linear
	

def setup(bot):
	bot.add_cog(Linears(bot))
