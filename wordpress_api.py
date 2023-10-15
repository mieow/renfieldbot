import discord
from discord.ext import commands
from discord.utils import get
import mysql.connector
import os
from tabulate import tabulate
import renfield_sql
from common import check_is_auth, check_restapi_active
# from interactions import cog_ext, SlashContext
# from interactions.utils.manage_commands import create_option, create_choice
from discord import Embed, app_commands
from dotenv import load_dotenv
import pycurl
import certifi
from io import BytesIO
import json
import requests
import base64
import urllib.parse
import pprint

# https://developer.wordpress.org/rest-api/extending-the-rest-api/adding-custom-endpoints/

load_dotenv()
GUILDID = int(os.getenv('DISCORD_GUILD_ID'))

	
class WordPressAPI(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		
	@check_restapi_active()
	@app_commands.command(name="link", description="Link Discord Account to Wordpress Account")
	@app_commands.describe(
		wordpress_id="Wordpress Login Name",
		wordpress_secret="Wordpress Account Secret"
	)
	async def link(self, ctx, wordpress_id: str, wordpress_secret: str):
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		author = ctx.user.display_name
		nameid = ctx.user.id
		server = ctx.guild.name
		wordpress_site = mydb.get_bot_setting("wordpress_site", "none", server)
		
		if wordpress_site == "none":
			await ctx.response.send_message("I'm sorry Master, This Discord server has not been linked to a Wordpress Site")
		else:
			status = mydb.save_link(nameid, wordpress_id, wordpress_secret, server)
			if status:
				# check link
				wpinfo = curl_get_me(nameid, server)
				if "code" in wpinfo:
					code = wpinfo["code"]
					if code == 'rest_not_logged_in':
						await ctx.response.send_message('I\'m sorry Master, I don\'t seem to be able to log in to the Wordpress Site for you')
					elif code == 'invalid_username':
						await ctx.response.send_message('I\'m sorry Master, That login name seems to be wrong. Is it spelled correctly?')
					elif code == 'incorrect_password':
						await ctx.response.send_message('I\'m sorry Master, That password is incorrect. You need a special "Application Password" and not your normal site login password. Go to {}/wp-admin/profile.php to create one.'.format(wordpress_site))
					else:
						await ctx.response.send_message('I\'m sorry Master, I recieved this error message when I tried to connect: {}'.format(wpinfo))
				else:
					# add to any server roles that match their WP account role names
					wproles = wpinfo["roles"]
					for wprole in wproles:
						for r in ctx.guild.roles:
							if wprole.upper() == r.name.upper():
								member = ctx.user
								role = get(member.guild.roles, name=r.name)
								await member.add_roles(role)
					
					# Get the info on the character
					charinfo = get_my_character(nameid, server)
					if "code" in charinfo:
						await ctx.response.send_message('I\'m sorry Master, I failed to read your character {}'.format(charinfo["message"]))
					else:
						#pprint.pprint(charinfo)
						
						# add/update Player Name in member table
						memberinfo = mydb.add_member(nameid, charinfo["result"]["player"], server)
						
						# set nickname (but not for the server owners or admins)
						if ctx.guild.me.guild_permissions.manage_nicknames:
							if ctx.user.guild_permissions.administrator:
								await ctx.response.send_message('Account has been linked')
							else:
								nickname = charinfo["result"]["display_name"]
								if charinfo["result"]["pronouns"] != "":
									nickname += " (" + charinfo["result"]["pronouns"] + ")"
								try:
									await ctx.user.edit(nick=nickname)
									await ctx.response.send_message('Thank you {}. I have connected to your wordpress account. Your Discord server nickname has been set to {}.'.format(charinfo["result"]["player"], nickname))
								except Exception as e:
									print(e)
									await ctx.response.send_message('Failed to set nickname. Check that the bot has permission to manage nicknames.'.format(charinfo["result"]["player"], nickname))
						else:
							await ctx.response.send_message('Character has been linked, but I don\'t have permission on this server to set your nickname.'.format(charinfo["result"]["player"], nickname))


			else:
				await ctx.response.send_message("I\'m sorry Master, I can't seem to remember that. Something went wrong.")

	@link.error
	async def link_error(self, ctx, error):
		if isinstance(error, discord.Forbidden):
			await ctx.channel.send("I'm sorry, I don't have permission to modify your Roles on this Discord server.")
		else:
			await ctx.channel.send("I failed.")
			raise error

	@check_restapi_active()
	@app_commands.command(name="whoami", description="Report character information")
	async def whoami(self, ctx):
		nameid = ctx.user.id
		server = ctx.guild.name
		charinfo = get_my_character(nameid, server)
		
		if "code" in charinfo:
			await ctx.response.send_message(charinfo["message"])
		else:
		
			clan = charinfo["result"]["clan"]
			player = charinfo["result"]["player"]
			approved = charinfo["result"]["date_of_approval"]
			char_status = charinfo["result"]["char_status"]
			cname = charinfo["result"]["display_name"]
			
			pathrating = charinfo["result"]["path_rating"]
			path = charinfo["result"]["path_of_enlightenment"]
			maxwp = charinfo["result"]["willpower"]
			
			#pprint.pprint(charinfo["result"])
		
			await ctx.user.send("Hello {}. Your character is at {} on {} and has willpower {}. It was approved on {}.".format(player, pathrating, path, maxwp, approved))
			await ctx.response.send_message("Your {} character is called {} and is currently {}.".format(clan, cname, char_status))



	@check_restapi_active()
	@app_commands.command(name="whois", description="Report character information of a specific character")
	async def whois(self, ctx, character: str):
		nameid = ctx.user.id
		server = ctx.guild.name
		
		try:
			if is_storyteller(nameid, ctx.guild):
				charinfo = get_character(server, nameid, character)
				if "code" in charinfo:
					await ctx.response.send_message(charinfo["message"])
				else:
					clan = charinfo["result"]["clan"]
					player = charinfo["result"]["player"]
					approved = charinfo["result"]["date_of_approval"]
					char_status = charinfo["result"]["char_status"]
					cname = charinfo["result"]["display_name"]
					
					await ctx.response.send_message("Hello {}. The {} character is called {} and is currently {}. They were approved for play on {}.".format(player, clan,cname, char_status, approved))
			else:
				uri = "wp-json/vampire-character/v1/character/"
				list = curl_get(uri, server, nameid)
				await ctx.response.send_message("Show character summary")
		except Exception as e:
			print(e)

# Check Wordpress API connection
def curl_checkAPI(server):
	result = curl_get("wp-json/wp/v2/users/me", server)
	return result["code"] != 'rest_not_logged_in'

# Function to run curl GET
def curl_get(endpoint, server, nameid: str=""):
	mydb = renfield_sql.renfield_sql()
	wordpress_site = mydb.get_bot_setting("wordpress_site", "none", server)
	
	if nameid != "":
		info = mydb.get_link(nameid, server)
		if info["wordpress_id"] == "":
			result = {}
			result["code"] = "account_not_linked"
			return result
		else:
			wordpress_id = urllib.parse.quote(info["wordpress_id"])
			secret = info["secret"]
	
	apiurl = "{}/{}".format(wordpress_site, endpoint)

	
	buffer = BytesIO()
	c = pycurl.Curl()
	#initializing the request URL
	c.setopt(c.URL, apiurl)
	#setting options for cURL transfer  
	c.setopt(c.WRITEDATA, buffer)
	if nameid != "":
		c.setopt(c.USERPWD, '%s:%s' %(wordpress_id, secret))
	#c.setopt(c.VERBOSE, True)	
	#setting the file name holding the certificates
	c.setopt(c.CAINFO, certifi.where())
	runok = 0
	try:
		# perform file transfer
		c.perform()
		runok = 1
	except pycurl.error as exc:
		print( ValueError("Error %s (%s)" % (apiurl, exc)) )
	
	#Ending the session and freeing the resources
	c.close()
	
	if runok:
		#retrieve the content BytesIO
		body = buffer.getvalue()
		
		# extract JSON from body
		result = json.loads(body)
	else:
		result = {}
		result["code"] = "curl_failed"

	return result

# Get info on wordpress user
def curl_get_me(nameid, server):
	#curl https://gvlarp.com/wp-json/wp/v2/users/me
	
	result = curl_get("wp-json/wp/v2/users/me?context=edit", server, nameid)
		
	return result

def get_my_character(nameid: str, server: str):
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		wordpress_site = mydb.get_bot_setting("wordpress_site", "none", server)
		
		characterinfo = {}
		if wordpress_site == "none":
			characterinfo["code"] = "not_enabled"
			characterinfo["message"] = "This server is not linked to a Wordpress site"
			return characterinfo

		wpresult = curl_get_me(nameid, server)
		meok = 0
		if "code" in wpresult:
			characterinfo["code"] = wpresult["code"]
			code = wpresult["code"]
			if code == 'rest_not_logged_in':
				characterinfo["message"] = 'I\'m sorry Master, I don\'t seem to be able to log in to the Wordpress Site API for you'
			elif code == 'invalid_username':
				characterinfo["message"] = 'I\'m sorry Master, I can\'t log you in to the {} wordpress site. Does youe account still exist?'.format(wordpress_site)
			elif code == 'incorrect_password':
				characterinfo["message"] = 'I\'m sorry Master, That password is incorrect. You will need to set a new "Application Password" and then re-link your Discord account to your Wordpress account. Go to {}/wp-admin/authorize-application.php?app_name=Renfield to create one.'.format(wordpress_site)
			elif code == 'account_not_linked':
				characterinfo["message"] = 'I\'m sorry Master, you first need to use the /link command to link your account. Use this to get the application password: {}/wp-admin/authorize-application.php?app_name=Renfield'.format(wordpress_site)
			else:
				characterinfo["message"] = 'I\'m sorry Master, I recieved this error message when I tried to connect: {}'.format(wpinfo)
			
		else:
			meok = 1
		
		if meok:
			uri = "wp-json/vampire-character/v1/character/me"
			result = curl_get(uri, server, nameid)

			# # character isn't linked?
			# # password is wrong
			if "code" in result:
				characterinfo["code"] = result["code"]
				if result["code"] == 'no_character':
					characterinfo["message"] = "Wordpress account {} does not have a character associated with it.".format(wpresult["username"])
				else:
					characterinfo["message"] = "Username {}, ID {}, uri {}, code {}.".format(wpresult["username"], wpresult["id"], uri, result["code"])
			elif "name" not in result["result"]:
				characterinfo["code"] = "no_character_info"
				characterinfo["message"] = "Command succeeded but no character information returned"
			else:
				characterinfo["result"] = result["result"]

		return characterinfo

def get_character(server: str, nameid: str, character: str):
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		wordpress_site = mydb.get_bot_setting("wordpress_site", "none", server)
		
		characterinfo = {}
		if wordpress_site == "none":
			characterinfo["code"] = "not_enabled"
			characterinfo["message"] = "This server is not linked to a Wordpress site"
			return characterinfo
		
		# validate character input
		# Can be:
		#		actual database character ID 	- integer
		#		Discord @ mention 				- check mentions and if they are linked
		#		wordpress ID	 				- check against WP users
		#		SQL LIKE / Guess on name of active characters
		gotchar = 0
		if character.isnumeric():
			id = character
			
			uri = "wp-json/vampire-character/v1/character/{}".format(id)
			result = curl_get(uri, server, nameid)

			if "code" in result:
				characterinfo["code"] = result["code"]
				if result["code"] == 'rest_forbidden':
					characterinfo["message"] = "I'm sorry, your linked Wordpress account needs to be a Storyteller or admin account."
				elif code == 'account_not_linked':
					characterinfo["message"] = 'I\'m sorry Master, you first need to use the /link command to link your account. Use this to get the application password: {}/wp-admin/authorize-application.php?app_name=Renfield'.format(wordpress_site)
				else:
					characterinfo["message"] = "Query for {}, ID {}, failed.".format(character, id)
			else:
				gotchar = 1
				characterinfo["result"] = result["result"]
				

		elif "@" in character:
			character = character.replace("@","")
			character = character.replace("<","")
			character = character.replace(">","")
			
			if character.isnumeric():
				wordpress_id = mydb.get_wordpress_id(character, server)
				
				if wordpress_id:
					# now we have the wp ID, we can query for the character
					uri = "wp-json/vampire-character/v1/character/wpid?wordpress_id={}".format(urllib.parse.quote(wordpress_id))
					result = curl_get(uri, server, nameid)
					
					if "code" in result:
						characterinfo["code"] = result["code"]
						if result["code"] == 'no_character':
							characterinfo["message"] = "Wordpress account {} does not have a character associated with it.".format(wpresult["username"])
						elif result["code"] == 'rest_forbidden':
							characterinfo["message"] = "Your Wordpress account does not have permission to access this information."
						else:
							characterinfo["message"] = "Request to Wordpress site for character ID has failed: {}".format(result["code"])
					else:
						gotchar = 1
						characterinfo["result"] = result["result"]
						
				else:
					characterinfo["code"] = "no_wpid_from_at"
					characterinfo["message"] = "I could not get WP ID from @{} mention. This user needs to link their Discord account to the Wordpress site.".format(character)
			else:
				characterinfo["code"] = "no_discordod_from_at"
				characterinfo["message"] = "I could not get discord ID from @{} mention. Are you sure you specified a user?".format(character)
			
		else:
			# try getting the character info by running a query as if 'character' is a WP ID
			wordpress_id = character
			uri = "wp-json/vampire-character/v1/character/wpid?wordpress_id={}".format(urllib.parse.quote(wordpress_id))
			result = curl_get(uri, server, nameid)

			if "code" in result:
				if result["code"] == 'rest_forbidden':
					characterinfo["code"] = result["code"]
					characterinfo["message"] = "Your Wordpress account does not have permission to access this information."
				elif result["code"] == 'no_character':
				
					# for everything else, we'll need a list of the active characters
					uri = "wp-json/vampire-character/v1/character/"
					list = curl_get(uri, server, nameid)
										
					# does the character directly match an existing character?
					match = 0
					charinfo = []
					for chars in list["result"]:
						if chars["characterName"].upper() == character.upper():
							match += 1
							charinfo = chars
					
					if match == 1:
						# retrieve full character info
						id = charinfo["characterID"]
						uri = "wp-json/vampire-character/v1/character/{}".format(id)
						result = curl_get(uri, server, nameid)

						if "code" in result:
							characterinfo["code"] = result["code"]
							if result["code"] == 'rest_forbidden':
								characterinfo["message"] = "I'm sorry, your linked Wordpress account needs to be a Storyteller or admin account."
							else:
								characterinfo["message"] = "Query for {}, ID {}, failed.".format(character, id)
						else:
							gotchar = 1
							characterinfo["result"] = result["result"]
					elif match > 1:
						characterinfo["code"] = "multiple_match"
						characterinfo["message"] = "More than one active character is named {}".format(character)
					else:
					
						# query wordpress to get the list of display names
						# and try to match on that
						uri = "wp-json/wp/v2/users?context=edit"
						users = curl_get(uri, server, nameid)

						matchexact = 0
						matchclose = 0
						userinfo = []
						listofcloseusers = []
						for user in users:
						
							# does this user have a character?
							tmphaschar = 0
							for chars in list["result"]:
								if user["username"] == chars["wordpress_id"]:
									tmphaschar = 1
						
							if tmphaschar:
								#print("compare {} to {}".format(character.upper(), user["name"].upper()))
								if user["name"].upper() == character.upper():
									matchexact += 1
									userinfo = user
								elif character.upper() in user["name"].upper():
									matchclose += 1
									userinfo = user
									listofcloseusers.append(user["username"])
												
						# get full user info
						if (matchexact + matchclose) > 0:
							uri = "wp-json/wp/v2/users/{}?context=edit".format(userinfo["id"])
							fulluser = curl_get(uri, server, nameid)
								
						if matchexact == 1:
							
							uri = "wp-json/vampire-character/v1/character/wpid?wordpress_id={}".format(urllib.parse.quote(fulluser["username"]))
							result = curl_get(uri, server, nameid)
						
							gotchar = 1
							characterinfo["result"] = result["result"]
						elif matchclose == 1:
							uri = "wp-json/vampire-character/v1/character/wpid?wordpress_id={}".format(urllib.parse.quote(fulluser["username"]))
							result = curl_get(uri, server, nameid)
						
							gotchar = 1
							characterinfo["result"] = result["result"]
						elif (matchexact + matchclose) > 1:
						
							listofclose = []
							for chars in list["result"]:
								for username in listofcloseusers:
									if username == chars["wordpress_id"]:
										listofclose.append("{} ({})".format(username, chars["characterName"]))
						
							characterinfo["code"] = "multiple_close"
							characterinfo["message"] = "I found {} close matches for {}. Please try again with an exact name. Close matches are: {}".format(matchclose, character, ", ".join(listofclose))

						else:
							characterinfo["code"] = "no_match_close"
							characterinfo["message"] = "Could not identity a character from '{}'".format(character)
							#print(result)
				else:
					characterinfo["code"] = "wp_request_failed"
					characterinfo["message"] = "Request to Wordpress site for character ID has failed: {}".format(result["code"])

			else:
				gotchar = 1
				characterinfo["result"] = result["result"]
		
		return characterinfo
		
def is_storyteller(nameid, guild):
	wpinfo = curl_get_me(nameid, guild.name)
	if "code" in wpinfo:
		return 0
	else:
		wproles = wpinfo["roles"]
		for wprole in wproles:
			if wprole.upper() == "STORYTELLER" or wprole.upper() == "ADMINISTRATOR":
				return 1
	return 0

async def setup(bot):
	await bot.add_cog(WordPressAPI(bot))