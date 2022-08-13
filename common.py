import renfield_sql
from discord.ext import commands

#class common():

def check_is_auth():
	def predicate(ctx):
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		server = ctx.guild.name
		admin_role = mydb.get_bot_setting("admin_role", "storytellers", server)
		mydb.disconnect()
		return ctx.author.guild_permissions.administrator or (admin_role.lower() in [y.name.lower() for y in ctx.author.roles])
		#return admin_role.lower() in [y.name.lower() for y in ctx.author.roles]
	return commands.check(predicate)

# msg_info (dictionary) = {
#	"command" = help | tell | speak | ...,
#	"source" = {
#				"name" = <author>,
#				"server" = <server>,
#				"vchannel" = <channel>,
#				},
#	"target" = {
#				"name" = <target character>,
#				"server" = <server>,
#				"channel" = <channel>
#				}
#	"message" = <message text>,
#	"raw"     = <full message text, no processing>
#	"
# }
#def parse_message(???):
	# copy in code from monitor to work out source - i.e. who is sending msg