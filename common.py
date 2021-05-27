import renfield_sql
from discord.ext import commands

#class common():

def check_is_auth():
	def predicate(ctx):
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		server = ctx.message.guild.name
		admin_role = mydb.get_bot_setting("admin_role", "storytellers", server)
		mydb.disconnect()
		return ctx.message.author.guild_permissions.administrator or (admin_role.lower() in [y.name.lower() for y in ctx.message.author.roles])
		#return admin_role.lower() in [y.name.lower() for y in ctx.message.author.roles]
	return commands.check(predicate)
