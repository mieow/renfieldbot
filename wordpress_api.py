import discord
from discord.ext import commands
from discord.utils import get
import mysql.connector
import os
from tabulate import tabulate
import renfield_sql
# from interactions import cog_ext, SlashContext
# from interactions.utils.manage_commands import create_option, create_choice
from discord import Embed, app_commands
from dotenv import load_dotenv
import pycurl
import certifi
from io import BytesIO
import json 

load_dotenv()
GUILDID = int(os.getenv('DISCORD_GUILD_ID'))

	
class WordPressAPI(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		
	@app_commands.command(name="link", description="Link Discord Account to Wordpress Account")
	@app_commands.describe(
		wordpress_id="Wordpress Login Name",
		wordpress_secret="Wordpress Account Secret"
	)
	async def link(self, ctx, wordpress_id: str="", wordpress_secret: str=""):
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
					wproles = wpinfo["roles"]
					for wprole in wproles:
						for r in ctx.guild.roles:
							if wprole.upper() == r.name.upper():
								member = ctx.author
								role = get(member.guild.roles, name=r.name)
								await member.add_roles(role)
								
				
					await ctx.response.send_message('Thank you {}. I have connected to your wordpress account.'.format(wpinfo["name"]))

			else:
				await ctx.response.send_message("I\'m sorry Master, I can't seem to remember that. Something went wrong.")

	@link.error
	async def link_error(self, ctx, error):
		if isinstance(error, discord.Forbidden):
			await ctx.send("I'm sorry, I don't have permission to modify your Roles on this Discord server.")
		else:
			await ctx.send("I failed.")
			raise error

def curl_example():
	buffer = BytesIO()
	c = pycurl.Curl()
	#initializing the request URL
	c.setopt(c.URL, 'https://www.scrapingbee.com/')
	#setting options for cURL transfer  
	c.setopt(c.WRITEDATA, buffer)
	#setting the file name holding the certificates
	c.setopt(c.CAINFO, certifi.where())
	# perform file transfer
	c.perform()
	#Ending the session and freeing the resources
	c.close()
	#retrieve the content BytesIO
	body = buffer.getvalue()
	#decoding the buffer 
	print(body.decode('iso-8859-1'))

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
		wordpress_id = info["wordpress_id"]
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
	# perform file transfer
	c.perform()
	#Ending the session and freeing the resources
	c.close()
	#retrieve the content BytesIO
	body = buffer.getvalue()
	
	# extract JSON from body
	result = json.loads(body)

	return result

# Get info on wordpress user
def curl_get_me(nameid, server):
	#curl https://gvlarp.com/wp-json/wp/v2/users/me
	
	result = curl_get("wp-json/wp/v2/users/me?context=edit", server, nameid)
		
	return result



async def setup(bot):
	await bot.add_cog(WordPressAPI(bot))