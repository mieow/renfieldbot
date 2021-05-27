import discord
import mysql.connector
import renfield_sql
from discord.ext import commands
from tabulate import tabulate
from common import check_is_auth


class Compliments(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None


	@commands.command(name='addnice', help='Add a compliment')
	#@commands.has_role('storytellers')
	@check_is_auth()
	async def addnice(self, ctx, *, compliment):
		#mydb = self.bot.db
		#mycursor = mydb.cursor()
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		server = ctx.message.guild.name
		try:
			sql = "INSERT INTO niceness (compliment, server) VALUES (%s, %s)"
			val = (compliment, server)
			mycursor.execute(sql, val)
			mydb.commit()
			await ctx.send('Thank you Master, I shall remember that.')
		except Exception as e:
			await ctx.send('I\'m sorry, Master, my memory is failing me.')
			print(e)
		mydb.disconnect()

	@addnice.error
	async def addnice_error(ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send("I'm sorry Master, I need more information. Can you tell me the {}".format(error.param.name))

	@commands.command(name='listnice', help='List all the compliments')
	#@commands.has_role('storytellers')
	@check_is_auth()
	async def listnice(self, ctx):
		#mydb = self.bot.db
		#mycursor = mydb.cursor()
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		server = ctx.message.guild.name
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
				await ctx.send(file=discord.File(fp, 'nice.txt'))
			
			#await ctx.send('```\n' + table + '```')
		except Exception as e:
			await ctx.send("I'm sorry Master, I am unable to recall all the compliments.")
			print(e)
			print (mycursor.statement)
		mydb.disconnect()

	@commands.command(name='deletenice', help='Delete a compliments')
	#@commands.has_role('storytellers')
	@check_is_auth()
	async def deletenice(self, ctx, ID: int):
		#mydb = self.bot.db
		#mycursor = mydb.cursor()
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		server = ctx.message.guild.name
		try:
			sql = "DELETE FROM `niceness` WHERE id = '%s' and server = %s"
			val = (ID,server)
			mycursor.execute(sql, val)
			mydb.commit()
			await ctx.send('I have forgotten that compliment, Master.')
		except Exception as e:
			await ctx.send("I'm sorry Master, I cannot forget that compliment.")
			print(e)
		mydb.disconnect()


	@deletenice.error
	async def deletenice_error(ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send("I'm sorry Master, I need more information. Can you tell me the {}".format(error.param.name))


	@commands.command(name='nice', help='Get a compliment')
	async def nice(self, ctx):
		mydb = renfield_sql.renfield_sql()
		server = ctx.message.guild.name
		author = ctx.message.author.display_name
		nice = mydb.get_nice(server)
		await ctx.send("Master {}. {}".format(author,nice))

def setup(bot):
	bot.add_cog(Compliments(bot))
