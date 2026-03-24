import logging

import discord
from discord.ext import commands
from discord.utils import get
import mariadb
import os
from tabulate import tabulate
from renfield_sql import get_bot_setting, save_bot_setting, renfield_sql, check_is_auth, check_restapi_active, get_link, save_link, add_member, get_wordpress_id
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
from requests_oauthlib import OAuth1
from urllib.parse import parse_qs

# https://developer.wordpress.org/rest-api/extending-the-rest-api/adding-custom-endpoints/

CALLBACK_URL = os.getenv('CALLBACK_URL')

	
class WordPressAPI(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		
	async def cog_app_command_error(self, ctx, error):
		if isinstance(error, discord.app_commands.CheckFailure):
			await ctx.response.send_message("I'm sorry Master. {}".format(error))
		else:
			await ctx.response.send_message("I'm sorry Master, the command failed.")
			print(error)
		
	@check_restapi_active()
	@app_commands.command(name="link", description="Link Discord Account to Wordpress Account")
	async def link(self, ctx):
		author = ctx.user.display_name
		nameid = ctx.user.id
		server = ctx.guild.name
		
		wordpress_site = get_bot_setting("wordpress_site", server)
		consumer_key = get_bot_setting("consumer_key", server)
		consumer_secret = get_bot_setting("consumer_secret", server)
		complete = False

		if wordpress_site == "none" or consumer_key == "none" or consumer_secret == "none":
			await ctx.response.send_message("I'm sorry Master, This Discord server has not been configured to link to a Wordpress Site")
			return
		else:

			# Send a HEAD request to the Wordpress site to check if it's reachable
			try:
				response = requests.head(wordpress_site, timeout=5)
				if response.status_code >= 400:
					await ctx.response.send_message(f"I'm sorry Master, I can't seem to reach the Wordpress site at {wordpress_site}. Please check the URL and that the site is up.")
					return
			except requests.RequestException as e:
				await ctx.response.send_message(f"I'm sorry Master, I can't seem to reach the Wordpress site at {wordpress_site}. Please check the URL and that the site is up. Error: {str(e)}")
				return
			
			logging.info(f"Successfully reached Wordpress site at {wordpress_site}. Status code: {response.status_code}")
			
			# Get the API endpoint from the response headers (if available) or assume it's at /wp-json/
			header_link = response.headers.get('Link', f"{wordpress_site}/wp-json/")
			api_endpoint = None
			if 'rel="https://api.w.org/"' in header_link:
				# Extract the URL from the Link header
				parts = header_link.split(',')
				for part in parts:
					if 'rel="https://api.w.org/"' in part:
						# find "link" and extract the URL between <>
						start = part.find('<') + 1
						end = part.find('>', start)
						if start > 0 and end > start:
							api_endpoint = part[start:end]

						break
			if not api_endpoint:
				api_endpoint = f"{wordpress_site}/wp-json/"
				print("API endpoint not found in headers, defaulting to: {}".format(api_endpoint))

			logging.info(f"Using API endpoint: {api_endpoint}")
			save_bot_setting("wordpress_api_endpoint", api_endpoint, server)

			# Check response from API endpoint
			try:
				api_response = requests.get(api_endpoint, timeout=5)
				if api_response.status_code >= 400:
					await ctx.response.send_message(f"I'm sorry Master, I can't seem to reach the Wordpress API endpoint at {api_endpoint}. Please check that the API is available. Status code: {api_response.status_code}")
					return
			except requests.RequestException as e:
				await ctx.response.send_message(f"I'm sorry Master, I can't seem to reach the Wordpress API endpoint at {api_endpoint}. Please check that the API is available. Error: {str(e)}")
				return
			
			logging.info(f"Successfully reached Wordpress API endpoint at {api_endpoint}. Status code: {api_response.status_code}")
			try:
				api_json = api_response.json()
			except json.JSONDecodeError:
				logging.warning("No JSON body in response.")
				await ctx.response.send_message(f"I'm sorry Master, I was able to reach the Wordpress API endpoint at {api_endpoint}, but the response did not contain valid JSON. Please check that the API is working correctly.")
				return

			method = None
			if api_json and 'authentication' in api_json:
				auth_methods = api_json['authentication']
				if 'application-passwords' in auth_methods:
					method = 'application-passwords'
					logging.info(f"Application Password authentication is supported by the Wordpress site.")
					authorize_url = api_json['authentication']['application-passwords']['endpoints']['authorization']

				if 'oauth1' in auth_methods:
					method = 'oauth1'
					logging.info(f"OAuth1 authentication is supported by the Wordpress site.")
					request_url = api_json['authentication']['oauth1']['request']
					authorize_url = api_json['authentication']['oauth1']['authorize']
					access_url = api_json['authentication']['oauth1']['access']
				
					# save access_url to bot settings so that harker can use it to exchange the request token for an access token after the user authorizes the app
					save_bot_setting("oauth_access_url", access_url, server)
				else:
					logging.warning(f"Could not determine supported authentication methods from API response.")
					await ctx.response.send_message(f"I'm sorry Master, I was able to reach the Wordpress API endpoint at {api_endpoint}, but I could not determine the supported authentication methods from the response. Please check that the API is working correctly and supports either Application Passwords or OAuth1 authentication.")
					return
			else:
				logging.warning(f"No authentication information found in API response.")
				await ctx.response.send_message(f"I'm sorry Master, I was able to reach the Wordpress API endpoint at {api_endpoint}, but it did not contain information about supported authentication methods. Please check that the API is working correctly and supports either Application Passwords or OAuth1 authentication.")
				return

			# Check available namespaces for OAuth1 endpoints
			if api_json and 'namespaces' in api_json:
				namespaces = api_json['namespaces']
				vampirens = None
				wpns = None
				for ns in namespaces:
					if ns == 'vampire-character/v1':
						logging.info("Custom namespace for vampire character plugin is available. Proceeding with linking.")
						save_bot_setting("character_api_namespace", ns, server)
						vampirens = ns
					if 'wp/v2' in ns:
						logging.info("Default Wordpress API namespace is available: {}".format(ns))
						save_bot_setting("wordpress_users_namespace", ns, server)
						wpns = ns

				if vampirens is None:
					logging.warning("No Vampire API namespaces found in API response. Linking may fail.")
					await ctx.response.send_message(f"I'm sorry Master, I couldn't find the Vampire Character API namespace I need. Please check that the vampire character plugin is installed and active on the Wordpress site.")
					return
				if wpns is None:
					logging.warning("No Wordpress Users API namespaces found in API response. Linking may fail.")
					await ctx.response.send_message(f"I'm sorry Master, I couldn't find the Wordpress Users API namespace I need. Please check that the Wordpress users endpoint is available on the site.")
					return
				
				# get the routes for the vampire character plugin 
				routes = api_json['routes']
				for route in routes:
					if wpns in route and 'users/me' in route:
						logging.info("Found API route for getting wordpress user information: {}".format(route))
						# contatenate with API endpoint and save to bot settings so that harker can use it to get the user's wordpress username after they authorize the app
						url = api_endpoint + route
						# remove any double slashes from the url
						url = url.replace('//', '/')
						url = url.replace(':/', '://')
						save_bot_setting("wordpress_users_api_route", url, server)
						break
			else:
				logging.warning("No namespaces information found in API response. Linking may fail.")
				await ctx.response.send_message(f"I'm sorry Master, I I could not fine the API namespaces in the response from the Wordpress API endpoint at {api_endpoint}. Please check that the API is working correctly and that the vampire character plugin is installed and active on the Wordpress site.")
				return

			if method == 'application-passwords':
				# Do stuff
				await ctx.response.send_message("Application Passwords authentication is not supported.")
				return
			elif method == 'oauth1':
				
				# send POST request to Wordpress API /oauth1/request endpoint 
				try:
					auth = OAuth1(client_key=consumer_key, client_secret=consumer_secret, callback_uri=CALLBACK_URL)
					response = requests.post(url=request_url, auth=auth)
				except Exception as e:
					print(f"An error occurred while initiating OAuth1 flow: {str(e)}")

				logging.info(f"Received response from OAuth1 request token endpoint with status code {response.status_code}")
				if response.status_code == 200:
					credentials = parse_qs(response.content)
					# print the credentials for debugging
					logging.debug(f"Received OAuth1 request token response: {credentials}")
					for key, value in credentials.items():
						logging.debug(f"{key}: {value[0]}")

					if b'oauth_token' in credentials and b'oauth_token_secret' in credentials:

						oauth_token_binary = credentials[b'oauth_token'][0]
						oauth_token_secret_binary = credentials[b'oauth_token_secret'][0]
						# convert from binary to string
						oauth_token = oauth_token_binary.decode('utf-8')
						oauth_token_secret = oauth_token_secret_binary.decode('utf-8')
						logging.debug(f"Received request token: {oauth_token}")
						logging.debug(f"Received request token secret: {oauth_token_secret}")

						user_auth_url = f"{authorize_url}?oauth_token={oauth_token}"
						user_auth_url += f"&oauth_token_secret={oauth_token_secret}"

						# Save the request token and secret in the database linked to the user and server, so we can verify it when they come back from authorizing the app
						status = save_link(nameid, "[placeholder]", server, oauth_token, oauth_token_secret, "pending")
						if not status:
							logging.error("Failed to save OAuth1 request token and secret to the database.")
							await ctx.response.send_message(f"I'm sorry Master, I failed to save the OAuth1 request token. Please try again.")
							return
						await ctx.response.send_message(f"To link your account, please visit the following URL to authorize the application: {user_auth_url}", ephemeral=True)
					else:
						logging.error(f"OAuth1 request token response did not contain expected parameters. Response content: {response.content}")
						await ctx.response.send_message(f"I'm sorry Master, I failed to initiate the OAuth1 authentication flow. The response from the Wordpress site did not contain the expected parameters. Please check that the API is working correctly and supports OAuth1 authentication.")
						return
				else:
					logging.error(f"Failed to initiate OAuth1 flow with status code {response.status_code}: {response.text}")
					await ctx.response.send_message(f"I'm sorry Master, I failed to initiate the OAuth1 authentication flow. The response from the Wordpress site did not contain the expected parameters. Please check that the API is working correctly and supports OAuth1 authentication.")
					return

		
		# 	status = save_link(nameid, wordpress_id, wordpress_secret, server)
		# 	if status:
		# 		# check link
		# 		wpinfo = curl_get_me(nameid, server)
		# 		if "code" in wpinfo:
		# 			code = wpinfo["code"]
		# 			if code == 'rest_not_logged_in':
		# 				await ctx.response.send_message('I\'m sorry Master, I don\'t seem to be able to log in to the Wordpress Site for you')
		# 			elif code == 'invalid_username':
		# 				await ctx.response.send_message('I\'m sorry Master, That login name seems to be wrong. Is it spelled correctly?')
		# 			elif code == 'incorrect_password':
		# 				await ctx.response.send_message('I\'m sorry Master, That password is incorrect. You need a special "Application Password" and not your normal site login password. Go to {}/wp-admin/profile.php to create one.'.format(wordpress_site))
		# 			else:
		# 				await ctx.response.send_message('I\'m sorry Master, I recieved this error message when I tried to connect: {}'.format(wpinfo))
		# 		else:
		# 			# add to any server roles that match their WP account role names
		# 			wproles = wpinfo["roles"]
		# 			for wprole in wproles:
		# 				for r in ctx.guild.roles:
		# 					if wprole.upper() == r.name.upper():
		# 						member = ctx.user
		# 						role = get(member.guild.roles, name=r.name)
		# 						await member.add_roles(role)
					
		# 			# Get the info on the character
		# 			charinfo = get_my_character(nameid, server)
		# 			if "code" in charinfo:
		# 				await ctx.response.send_message('I\'m sorry Master, I failed to read your character {}'.format(charinfo["message"]))
		# 			else:
		# 				#pprint.pprint(charinfo)
						
		# 				# add/update Player Name in member table
		# 				memberinfo = add_member(nameid, charinfo["result"]["player"], server)
						
		# 				# set nickname (but not for the server owners or admins)
		# 				if ctx.guild.me.guild_permissions.manage_nicknames:
		# 					if ctx.user.guild_permissions.administrator:
		# 						await ctx.response.send_message('Account has been linked')
		# 					else:
		# 						nickname = charinfo["result"]["display_name"]
		# 						if charinfo["result"]["pronouns"] != "":
		# 							nickname += " (" + charinfo["result"]["pronouns"] + ")"
		# 						try:
		# 							await ctx.user.edit(nick=nickname)
		# 							await ctx.response.send_message('Thank you {}. I have connected to your wordpress account. Your Discord server nickname has been set to {}.'.format(charinfo["result"]["player"], nickname))
		# 						except Exception as e:
		# 							print(e)
		# 							await ctx.response.send_message('Failed to set nickname. Check that the bot has permission to manage nicknames.'.format(charinfo["result"]["player"], nickname))
		# 				else:
		# 					await ctx.response.send_message('Character has been linked, but I don\'t have permission on this server to set your nickname.'.format(charinfo["result"]["player"], nickname))


		# 	else:
		# 		await ctx.response.send_message("I\'m sorry Master, I can't seem to remember that. Something went wrong.")

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
	result = curl_get("wp/v2/users/me", server)
	return result["code"] != 'rest_not_logged_in'

# Function to run curl GET
def curl_get(endpoint, server, nameid: str=""):
	wordpress_api_endpoint = get_bot_setting("wordpress_api_endpoint", server)
	
	auth = None
	if nameid != "":
		info = get_link(nameid, server)
		if info["status"] != "linked":
			result = {}
			result["code"] = "account_not_linked"
			return result
		else:
			wordpress_id = urllib.parse.quote(info["wordpress_id"])
			secret = info["secret"]
			token = info["token"]
	else:
		result = {}
		result["code"] = "no_wordpress_id"
		return result

	consumer_key = get_bot_setting("consumer_key", server)
	consumer_secret = get_bot_setting("consumer_secret", server)

	if not consumer_key or not consumer_secret:
		result = {}
		result["code"] = "no_consumer_keys"
		return result
	
	auth = OAuth1(client_key=consumer_key, client_secret=consumer_secret, resource_owner_key=token, resource_owner_secret=secret)
	
	apiurl = "{}{}".format(wordpress_api_endpoint, endpoint)

	logging.info(f"Making authenticated request to Wordpress API at {apiurl} with OAuth1 authentication for user {wordpress_id}")
	#print("consumers: {} {}".format(consumer_key, consumer_secret))
	#print("token and secret: {} {}".format(token, secret))
	#print("API URL: {}".format(apiurl))
	
	try:
		response = requests.get(apiurl, auth=auth)
		if response.status_code == 200:
			try:
				result = response.json()
			except json.JSONDecodeError:
				result = {}
				result["code"] = "json_parse_error"
				result["error"] = f"Failed to parse JSON response. Response content: {response.text}"
		else:
			try:
				error_info = response.json()
				result = {}
				result["code"] = error_info.get('code', f'http_{response.status_code}_error')
				result["error"] = f"HTTP {response.status_code} error: {error_info.get('message', 'No error message provided')}"
			except json.JSONDecodeError:
				result = {}
				result["code"] = response.status_code
				result["error"] = f"HTTP {response.status_code} error: No error message provided"
	except requests.RequestException as e:
		result = {}
		result["code"] = "request_failed"
		result["error"] = str(e)
	
	return result

# Get info on wordpress user
def curl_get_me(nameid, server):
	#curl https://gvlarp.com/wp-json/wp/v2/users/me
	
	result = curl_get("wp/v2/users/me?context=edit", server, nameid)
		
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
				characterinfo["message"] = 'I\'m sorry Master, I recieved this error message when I tried to connect: {}'.format(wpresult)
			
		else:
			meok = 1
		
		if meok:
			uri = "vampire-character/v1/character/me"
			result = curl_get(uri, server, nameid)

			# # character isn't linked?
			# # password is wrong
			if "code" in result:
				characterinfo["code"] = result["code"]
				if result["code"] == 'no_character':
					characterinfo["message"] = "Wordpress account {} does not have a character associated with it.".format(wpresult["username"])
				
				else:
					characterinfo["message"] = "Username {}, ID {}, uri {}, code '{}': Error: {}".format(wpresult["username"], wpresult["id"], uri, result["code"], result["error"])
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
			
			uri = "vampire-character/v1/character/{}".format(id)
			result = curl_get(uri, server, nameid)

			if "code" in result:
				characterinfo["code"] = result["code"]
				if result["code"] == 'rest_forbidden':
					characterinfo["message"] = "I'm sorry, your linked Wordpress account needs to be a Storyteller or admin account."
				elif result["code"] == 'account_not_linked':
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
					uri = "/vampire-character/v1/character/wpid?wordpress_id={}".format(urllib.parse.quote(wordpress_id))
					result = curl_get(uri, server, nameid)
					if "code" in result:
						characterinfo["code"] = result["code"]
						if result["code"] == 'no_character':
							characterinfo["message"] = "Wordpress account {} does not have a character associated with it.".format(wordpress_id)
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
			uri = "vampire-character/v1/character/wpid?wordpress_id={}".format(urllib.parse.quote(wordpress_id))
			result = curl_get(uri, server, nameid)

			if "code" in result:
				if result["code"] == 'rest_forbidden':
					characterinfo["code"] = result["code"]
					characterinfo["message"] = "Your Wordpress account does not have permission to access this information."
				elif result["code"] == 'no_character':
				
					# for everything else, we'll need a list of the active characters
					uri = "vampire-character/v1/character/"
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
						uri = "vampire-character/v1/character/{}".format(id)
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
						uri = "wp/v2/users?context=edit"
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
							uri = "wp/v2/users/{}?context=edit".format(userinfo["id"])
							fulluser = curl_get(uri, server, nameid)
								
						if matchexact == 1:
							
							uri = "/vampire-character/v1/character/wpid?wordpress_id={}".format(urllib.parse.quote(fulluser["username"]))
							result = curl_get(uri, server, nameid)
						
							gotchar = 1
							characterinfo["result"] = result["result"]
						elif matchclose == 1:
							uri = "/vampire-character/v1/character/wpid?wordpress_id={}".format(urllib.parse.quote(fulluser["username"]))
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