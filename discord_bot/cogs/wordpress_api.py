import discord
from discord.ext import commands
from discord.utils import get
import mysql.connector
import os
from tabulate import tabulate
from renfield_sql import get_bot_setting, renfield_sql, check_is_auth, check_restapi_active, get_link, save_link, add_member, get_wordpress_id
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

from helper.logger import log
from helper.wordpress_api_data import WordpressModal
from helper.character_display import displayCharacter

# https://developer.wordpress.org/rest-api/extending-the-rest-api/adding-custom-endpoints/

	
class WordPressAPI(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		
	async def cog_app_command_error(self, ctx, error):
		if isinstance(error, discord.app_commands.CheckFailure):
			await ctx.response.send_message("I'm sorry Master. {}".format(error))
		else:
			await ctx.response.send_message("I'm sorry Master, the command failed.")
			print(error)

	@app_commands.command(name="link-help", description="Sends the User a DM on how to setup their application password")
	async def link_help(self, ctx):
		user = ctx.user
		server = ctx.guild.name
		await ctx.response.defer()
		try:
			static_file_location = os.getenv("STATIC_FILES")
			image1 = discord.File(static_file_location + "/Link_Instructions/Image#1.png")
			image2 = discord.File(static_file_location + "/Link_Instructions/Image#2.png")
			image3 = discord.File(static_file_location + "/Link_Instructions/Image#3.png")
      
			wordpress_site = get_bot_setting("wordpress_site", server)
			wordpress_site = wordpress_site + "wp-admin/profile.php"
			
			message1 = f'## Setting Up Your WordPress Account Application Password\nGo to {wordpress_site}\nScroll Down to Application Passwords'
			message2 = f'Enter into the a name for the password (Renfield is suggested for easy reminder)'
			message3 = f'Click "Add New Application Password"'
			message4 = f'Once the password is generated, click Copy, and it can be pasted into the textbox for /link\nEnjoy :D'
			await user.send(message1)
			await user.send(file=image1)
			await user.send(message2)
			await user.send(file=image2)
			await user.send(message3)
			await user.send(file=image3)
			await user.send(message4)
			await ctx.followup.send(f'Sent Instructions to {user.mention}')

		except Exception as e:
			log.error(e)
   
  
	@check_restapi_active()
	@app_commands.command(name="link", description="Link Discord Account to Wordpress Account (Do /link-help for help)")
	async def link_modal(self, ctx):
		user = ctx.user
		try:
			server = ctx.guild.name
			wordpress_site = get_bot_setting("wordpress_site", server)
		
			if wordpress_site == "none":
				await ctx.response.send_message("I'm sorry Master, This Discord server has not been linked to a Wordpress Site")
			else:
				wordpressModal = WordpressModal(user)
				await ctx.response.send_modal(wordpressModal)
		except Exception as e:
			log.error(f"Error in link_direct_message: {e}")
			await interaction.response.send_message("An error occurred while starting the linking process.", ephemeral=True)

	@link_modal.error
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
			cname = charinfo["result"]["name"]
			
			pathrating = charinfo["result"]["path_rating"]
			path = charinfo["result"]["path_of_enlightenment"]
			maxwp = charinfo["result"]["willpower"]
					
			await ctx.response.send_message("{} The {} is currently {}.".format(cname, clan, char_status))



	@check_restapi_active()
	#@app_commands.command(name="whois", description="Report character information of a specific character")
	async def whois(self, ctx, character: str):
		nameid = ctx.user.id
		server = ctx.guild.name
		
		try:
			charinfo = get_character(server, nameid, character)
			if "code" in charinfo:
				await ctx.response.send_message(charinfo["message"])
			else:
				if is_storyteller(nameid, ctx.guild.name):
					clan = charinfo["result"]["clan"]
					player = charinfo["result"]["player"]
					approved = charinfo["result"]["date_of_approval"]
					char_status = charinfo["result"]["char_status"]
					cname = charinfo["result"]["display_name"]
					
					await ctx.response.send_message("Hello {}. The {} character is called {} and is currently {}. They were approved for play on {}.".format(player, clan,cname, char_status, approved))
				else:
					clan = charinfo["result"]["clan"]
					player = charinfo["result"]["player"]
					char_status = charinfo["result"]["char_status"]
					cname = charinfo["result"]["display_name"]
					status = charinfo["result"]["backgrounds"][0]["level"]
					await ctx.response.send_message("Character {} is of clan {} and is {}. They have status {}.".format(cname, clan, char_status, status))
		except Exception as e:
			print(e)

# Check Wordpress API connection
def curl_checkAPI(server):
	result = curl_get("wp-json/wp/v2/users/me", server)
	return result["code"] != 'rest_not_logged_in'

# Function to run curl GET
def curl_get(endpoint, server, nameid: str=""):
	wordpress_site = get_bot_setting("wordpress_site", server)
	
	if nameid != "":
		info = get_link(nameid, server)
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
	
	
	if runok:
		#retrieve the content BytesIO
		body = buffer.getvalue()
		
		# extract JSON from body
		status = c.getinfo(c.RESPONSE_CODE)
		result = json.loads(body)
		# if status == 200:
		# else:
			# result = {}
			# result["code"] = "http_error"
			# result["error"] = body
			
	else:
		result = {}
		result["code"] = "curl_failed"
		
	#Ending the session and freeing the resources
	c.close()

	return result

# Get info on wordpress user
def curl_get_me(nameid, server):
	#curl https://gvlarp.com/wp-json/wp/v2/users/me
	
	result = curl_get("wp-json/wp/v2/users/me?context=edit", server, nameid)
		
	return result

def get_my_character(nameid: str, server: str):
		wordpress_site = get_bot_setting("wordpress_site", server)
		
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
		wordpress_site = get_bot_setting("wordpress_site", server)
		
		characterinfo = {}
		if wordpress_site == "none":
			characterinfo["code"] = "not_enabled"
			characterinfo["message"] = "This server is not linked to a Wordpress site"
			return characterinfo
		
		isST = is_storyteller(nameid, server);
		
		# validate character input
		# Can be:
		#		actual database character ID 	- integer
		#		Discord @ mention 				- check mentions and if they are linked
		#		wordpress ID	 				- check against WP users
		#		SQL LIKE / Guess on name of active characters
		gotchar = 0
		if isST and character.isnumeric():
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
				wordpress_id = get_wordpress_id(character, server)
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
						elif result["code"] == 'http_error':
							characterinfo["message"] = "There was a problem with the response from the website. See the Wordpress site admin to resolve the issue."
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
			
		elif isST:
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
		else:
			characterinfo["code"] = "failure"
			characterinfo["message"] = "Use the @ mention to get character information on a user"
		return characterinfo
		
def is_storyteller(nameid, server):
	wpinfo = curl_get_me(nameid, server)
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