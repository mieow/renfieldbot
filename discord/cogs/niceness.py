import discord
import mysql.connector
import renfield_sql
from discord.ext import commands
from tabulate import tabulate
from common import check_is_auth
from discord import app_commands


class Compliments(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None

	async def cog_app_command_error(self, ctx, error):
		if isinstance(error, discord.app_commands.CheckFailure):
			await ctx.response.send_message("I'm sorry Master. {}".format(error))
		else:
			await ctx.response.send_message("I'm sorry Master, the command failed.")
			print(error)

	@check_is_auth()
	@app_commands.command(name='addnice', description='Add a compliment')
	@app_commands.describe(compliment="Text of compliment to add")
	async def addnice(self, ctx, *, compliment: str):

		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		server = ctx.guild.name
		try:
			sql = "INSERT INTO niceness (compliment, server) VALUES (%s, %s)"
			val = (compliment, server)
			mycursor.execute(sql, val)
			mydb.commit()
			await ctx.response.send_message('Thank you Master, I shall remember that.')
		except Exception as e:
			await ctx.response.send_message('I\'m sorry, Master, my memory is failing me.')
			print(e)
		mydb.disconnect()

	@addnice.error
	async def addnice_error(ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send("I'm sorry Master, I need more information. Can you tell me the {}".format(error.param.name))

	@check_is_auth()
	@app_commands.command(name='listnice', description='List all the compliments')
	async def listnice(self, ctx):
		try:
			mydb = renfield_sql.renfield_sql()
			mycursor = mydb.connect()
			server = ctx.guild.name
		except Exception as e:
			await ctx.response.send_message("I'm sorry Master, something went wrong.")
			print(e)
		try:
			sql = "SELECT id, compliment FROM niceness WHERE server = %s ORDER BY compliment"
			val = (server,)
			
			mycursor.execute(sql, val)
	
			events = mycursor.fetchall()
			headers = ['ID', 'Compliment']
			rows = [[e[0], e[1]] for e in events]
			table = tabulate(rows, headers)
			
			f = open("/tmp/nice.txt", "w")
			f.write(table)
			f.close()
			
			with open('/tmp/nice.txt', 'rb') as fp:
				await ctx.response.send_message(file=discord.File(fp, 'nice.txt'))
			
			#await ctx.send('```\n' + table + '```')
		except Exception as e:
			await ctx.response.send_message("I'm sorry Master, I am unable to recall all the compliments.")
			print(e)
			print (mycursor.statement)
		mydb.disconnect()

	@check_is_auth()
	@app_commands.command(name='deletenice', description='Delete a compliments')
	@app_commands.describe(id="Compliment ID")
	async def deletenice(self, ctx, id: int):
		#mydb = self.bot.db
		#mycursor = mydb.cursor()
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		server = ctx.guild.name
		try:
			sql = "DELETE FROM `niceness` WHERE id = '%s' and server = %s"
			val = (id,server)
			mycursor.execute(sql, val)
			mydb.commit()
			await ctx.response.send_message('I have forgotten that compliment, Master.')
		except Exception as e:
			await ctx.response.send_message("I'm sorry Master, I cannot forget that compliment.")
			print(e)
		mydb.disconnect()


	# @deletenice.error
	# async def deletenice_error(ctx, error):
		# if isinstance(error, commands.MissingRequiredArgument):
			# await ctx.send("I'm sorry Master, I need more information. Can you tell me the {}".format(error.param.name))


	@app_commands.command(name='nice', description='Get a compliment')
	async def nice(self, ctx):
		mydb = renfield_sql.renfield_sql()
		server = ctx.guild.name
		author = ctx.user.display_name
		nice = mydb.get_nice(server)
		await ctx.response.send_message("Master {}. {}".format(author,nice))

async def setup(bot):
	await bot.add_cog(Compliments(bot))
