import discord
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv
from discord import Embed, app_commands
from datetime import datetime, date
import renfield_sql
import nacl
import asyncio
import botocore

from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import sys
import subprocess
from tempfile import gettempdir, mkstemp

load_dotenv()
GUILDID = int(os.getenv('DISCORD_GUILD_ID'))

# Create a client using the credentials and region defined in the [adminuser]
# section of the AWS credentials file (~/.aws/credentials).
session = Session(profile_name="default")
polly = session.client("polly")

	
class Voice(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		
	@app_commands.command(name="speak", description="Ask Renfield to speak into a voice channel")
	@app_commands.describe(
		channel="Name of voice channel",
		text="What you want the bot to say"
	)
	async def speak(self, ctx, channel: discord.VoiceChannel, text: str):
		server = ctx.guild
		mydb = renfield_sql.renfield_sql()
		myvoice = mydb.get_bot_setting("polly_voice", "Brian", server.name)
	
		# Verify voice channel exists
		found = 0
		try:
			for vc in server.voice_channels:
				vcname = "{}".format(vc.name)
				if vcname.upper() == channel.name.upper():
					found += 1
					vchannel = vc

		except Exception as e:
			await ctx.response.send_message('I\'m sorry, Master. I can\'t find the {} voice channel. Did you spell it correctly?'.format(channel.name))
			print(e)
		
		accessok = 0
		if found:
			client = discord.utils.get(self.bot.voice_clients, guild=server)
			# check channel permissions
			try:
				permissions = vchannel.permissions_for(server.me)
			except Exception as e:
				print(e)
			if not permissions.connect or not permissions.speak:
				await ctx.response.send_message("I don't have permission to join or speak in that voice channel.")
			else:
				accessok = 1
		
		if found and accessok:
			dt = datetime.now()
			ts = datetime.timestamp(dt)
			
			# Check monthly word count for Polly
			withinlimit = 0
			try:
		
				current = int(mydb.get_bot_setting("current_words", 0, "None"))
				limit = int(os.getenv('POLLY_WORD_LIMIT'))
				lastupdated = float(mydb.get_bot_setting("last_updated_words", 0, "None"))
				lastupdateddt = date.fromtimestamp(lastupdated)
				count = len(text.split())
				
				if lastupdateddt.strftime("%m-%Y") == dt.strftime("%m-%Y"):
					total = current + count
				else:
					total = count
				
				if limit > total:
					withinlimit = 1
					#await ctx.channel.send("Check passed = running total: {}, current: {}, limit: {}, word count in text: {}, character count: {}, last updated: {}".format(total, current, limit, count, len(text), lastupdateddt.strftime("%m-%Y")))
				else:
					await ctx.response.send_message("I believe in free speech!  If I use more than {} words in a month then it will cost money. You've just asked me to say {} words when I've already said {} this month!".format(limit, count, current))
			except Exception as e:
				print(e)
			
			if withinlimit:
				# Create the mp3
				mp3ok = 0
				try:
					# Request speech synthesis
					response = polly.synthesize_speech(Text=text, OutputFormat="mp3", VoiceId=myvoice, LexiconNames=["VTM"])
					mp3ok = 1
					
					# save monthly speech count
					mydb.save_bot_setting("current_words", total, "None")
					mydb.save_bot_setting("last_updated_words", ts, "None")
					
				except botocore.exceptions.ClientError as error:
					#An error occurred (ValidationException) when calling the SynthesizeSpeech operation: This voice does not support the selected engine: standard
					# The service returned an error, exit gracefully
					if error.response['Error']['Code'] == 'TextLengthExceededException':
						await ctx.response.send_message('I\'m sorry, Master. Please limit your message to 1500 characters from {}.'.format(len(text)))
					elif error.response['Error']['Code'] == 'EngineNotSupportedException':
						await ctx.response.send_message('I\'m sorry, Master. My voice named "{}" isn\' one of the standard voice options.'.format(len(myvoice)))
					elif error.response['Error']['Code'] == 'LexiconNotFoundException':
						await ctx.response.send_message('I\'m sorry, Master. I\'ve had a problem processing the custom lexicon of words')
					else:
						await ctx.response.send_message('I\'m sorry, Master. There seems to have been a problem working out how to say your message.')
					print(error)
				
				if mp3ok:
					audiook = 0
					if "AudioStream" in response:
						# Note: Closing the stream is important because the service throttles on the
						# number of parallel connections. Here we are using contextlib.closing to
						# ensure the close method of the stream object will be called automatically
						# at the end of the with statement's scope.
						with closing(response["AudioStream"]) as stream:
							fd, output = mkstemp(suffix=".mp3", prefix="speech")

							try:
								# Open a file for writing the output as a binary stream
								# with open(output, "wb") as file:
									# file.write(stream.read())
								with os.fdopen(fd, 'wb') as file:
									file.write(stream.read())						
								audiook = 1
							except IOError as error:
								# Could not write to file, exit gracefully
								print(error)
								await ctx.response.send_message('I\'m sorry, Master. I cannot remember what I was about to say.')

					else:
						# The response didn't contain audio data, exit gracefully
						await ctx.response.send_message("I\'m sorry, Master. I thought I had prepared the words to say but somehow I seem to be wrong.")
					
					if audiook:

						hasclient = 0
						if client:
							hasclient = 1
							if client.channel.name != vchannel.name:
								# need to move channels
								try:
									await client.move_to(vchannel)
								except Exception as e:
									await ctx.response.send_message('I\'m sorry, Master. I can\'t move to the {} voice channel.'.format(channel))
									print(e)	
								
						else:
							try:
								client = await vchannel.connect()
								hasclient = 1
							except Exception as e:
								await ctx.response.send_message('I\'m sorry, Master. I can\'t join the {} voice channel.'.format(channel))
								print(e)
											
						# play mp3
						if hasclient and client.is_connected():
							client.play(discord.FFmpegPCMAudio(
										#options="-v debug",
										options="-v quiet",
										executable="/usr/bin/ffmpeg",
										source=output
								)
							)

							await ctx.response.send_message('Message sent to {} channel by {}: {}'.format(channel, ctx.user.display_name, text))

							while client.is_playing():
								await asyncio.sleep(1)
							
							# Delete the file:
							try:
								os.remove(output)
							except Exception as e:
								await ctx.message.send('I\'m sorry, Master. I couldn\t remove the sound file after playing')
								print(e)

						else:
							await ctx.response.send_message('I\'m sorry, Master. I can\'t connect fully to the voice channel to play anything.'.format(channel))

		else:
			await ctx.response.send_message('I\'m sorry, Master. I can\'t find the {} voice channel.'.format(channel))
		


async def setup(bot):
	await bot.add_cog(Voice(bot))