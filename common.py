import renfield_sql
import os
from discord.ext import commands
from cryptography.fernet import Fernet

def check_is_auth():
	def predicate(ctx):
		try:
			mydb = renfield_sql.renfield_sql()
			mycursor = mydb.connect()
			server = ctx.guild.name
			admin_role = mydb.get_bot_setting("admin_role", "storytellers", server)
			mydb.disconnect()
		except Exception as e:
			print(e)
		

		try:
			return ctx.author.guild_permissions.administrator or (admin_role.lower() in [y.name.lower() for y in ctx.author.roles])
		except Exception as e:
			print(e)

	return commands.check(predicate)

def check_restapi_active():
	def predicate(ctx):
		try:
			mydb = renfield_sql.renfield_sql()
			mycursor = mydb.connect()
			server = ctx.guild.name
			wordpress_site = mydb.get_bot_setting("wordpress_site", "none", server)
			mydb.disconnect()
			
			if wordpress_site == "none":
				return false
			else:
				return true
		except Exception as e:
			print(e)
		

	return commands.check(predicate)


# function to create & write encryption key
def write_key():
	if os.path.isfile("/home/renfield/.wp_key"):
		return "using existing key"
	else:
		key = Fernet.generate_key()
		with open("/home/renfield/.wp_key", "wb") as key_file:
			key_file.write(key)
		return "new key generated"
 
# function to read encryption key
def load_key():
	"""
	Loads the key named `secret.key` from the current directory.
	"""
	return open("/home/renfield/.wp_key", "rb").read()
	
# function to encode string
def str_encode(message):
	key = load_key()
	fernet = Fernet(key)
	return fernet.encrypt(message.encode())

# function to decode string
def str_decode(encMessage):
	key = load_key()
	fernet = Fernet(key)
	return fernet.decrypt(encMessage).decode()

def get_log_channel(server):
	logchannel = server.system_channel
	try:
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		cubbyhole = mydb.get_bot_setting("cubby-hole", "renfields-cubby-hole", server.name)
		mydb.disconnect()
		
		for outchannel in server.channels:
			if outchannel.name == cubbyhole:
				logchannel = outchannel
				break
				
	except Exception as e:
		print(e)

	return logchannel


