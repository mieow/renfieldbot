import discord
from discord import ui
from .logger import log
from renfield_sql import get_bot_setting, save_link, get_link, add_member
import urllib
import pycurl
import certifi
import json
from io import BytesIO


# Modal for collecting WordPress Application Password
class WordpressModal(ui.Modal, title="WordPress Linking\n(Do /link-help For Help)"):
	username = ui.TextInput(label="Username", placeholder="Enter your WordPress username", required=True)
	application_password = ui.TextInput(label="Application Password", placeholder="Enter your WordPress Application Password", required=True)

	def __init__(self, user):
		super().__init__()
		self.user = user

	async def on_submit(self, ctx: discord.Interaction):
		log.info(f'Username from user: {self.user.name} - {self.username}')
		await ctx.response.defer()

		# Attempt to connect to WordPress
		connected = await connect_to_wordpress(login_name=self.username.value, application_pass=self.application_password.value, ctx=ctx)

		if connected:
			message = "Connected to WordPress"
		else:
			message = "Failed to connect to WordPress."

		await ctx.followup.send(connected)

# Function to connect to WordPress using provided credentials
async def connect_to_wordpress(login_name: str, application_pass: str, ctx: discord.Interaction):
	"""
	Simulates connecting to a WordPress account with provided credentials.

	Args:
		login_name (str): The WordPress login name.
		application_pass (str): The WordPress application password.

	Returns:
		bool: True if the connection is successful, False otherwise.
	"""
	try:
		# Assuming these functions are defined somewhere in your code
		nameid = ctx.user.id
		server = ctx.guild.name
		wordpress_site = get_bot_setting("wordpress_site", server)

		# Save link to database or configuration
		status = save_link(nameid, login_name, application_pass, server)

		if status:
			# Check if the connection was successful
			wpinfo = curl_get_me(nameid, server)

			if "code" in wpinfo:
				code = wpinfo["code"]

				if code == 'rest_not_logged_in':
					return "I couldn't log in to the WordPress site."
				elif code == 'invalid_username':
					return("Invalid username. Please double-check the spelling.")
				elif code == 'incorrect_password':
					return(f"The password is incorrect. Visit {wordpress_site}/wp-admin/profile.php to create an Application Password.")
				else:
					return(f"Error: {wpinfo}")
			else:
				# Add roles based on WordPress data
				roles = wpinfo["roles"]
				for role in roles:
					for r in ctx.guild.roles:
						if role.upper() == r.name.upper():
							member = ctx.user
							role = get(ctx.guild.roles, name=r.name)
							await member.add_roles(role)

				# Get character info
				charinfo = get_my_character(nameid, server)

				if "code" in charinfo:
					return(f"Failed to retrieve character: {charinfo['message']}")
				else:
					# Update player name in the database and set nickname
					memberinfo = add_member(nameid, charinfo["result"]["player"], server)
					if ctx.guild.me.guild_permissions.manage_nicknames:
						nickname = charinfo["result"]["display_name"]
						if charinfo["result"]["pronouns"]:
							nickname += f" ({charinfo['result']['pronouns']})"
						try:
							await ctx.user.edit(nick=nickname)
							return 'Account has been linked successfully.'
						except discord.Forbidden:
							return 'I do not have permission to change nicknames in this server.'
						except discord.HTTPException as e:
							return f"An HTTP error occurred: {e}"
						except Exception as e:
							return f"An unexpected error occurred: {e}"
					else:
						return('Could not set nickname due to permission issues.')
	except Exception as error:
		log.error(f"Error connecting to WordPress: {error}")
		return("An error occurred while connecting to WordPress.")

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
