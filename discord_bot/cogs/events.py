import discord
from discord.ext import commands
from tabulate import tabulate
import mysql.connector
from datetime import date
from datetime import datetime, timezone
from renfield_sql import check_is_auth, get_log_channel, update_event, get_nice, add_member, renfield_sql, get_bot_setting
from discord import Embed, app_commands
from dotenv import load_dotenv
import os
import pytz
from tempfile import gettempdir, mkstemp

class Events(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None
		
	async def cog_app_command_error(self, ctx, error):
		if isinstance(error, discord.app_commands.CheckFailure):
			await ctx.response.send_message("I'm sorry Master. {}".format(error))
		else:
			await ctx.response.send_message("I'm sorry Master, the command failed.")
			print(error)

	@commands.Cog.listener()
	async def on_scheduled_event_create(self, event):
		server = event.guild
		name = event.name
		mydb = renfield_sql()
		mycursor = mydb.connect()
		logchannel = get_log_channel(server)
		
		# check if event of the same name already exists before trying to add it
		event_count = 0
		try:
			sql = "select count(id) from events where name = %s and server = %s"
			val = (name, server.name)
			mycursor.execute(sql,val)
			#print(mycursor.statement)
			events = mycursor.fetchone()
			event_count = events[0]
			#await logchannel.send('Event creation: I have found {} events with name {} in this server.'.format(event_count, name))
		except Exception as e:
			print(mycursor.statement)
			print(e)
			await logchannel.send('I could not find event {} in my database - it is unique'.format(name))

		if event_count == 0:
			try:
				# Create event in the database
				sql = "INSERT INTO events (name, server, eventdate) VALUES (%s, %s, %s)"
				val = (name, server.name, event.start_time)
				mycursor.execute(sql, val)
				mydb.commit()
				await logchannel.send('I have recorded the new {} event in the diary for {}'.format(name, event.start_time))
			except Exception as e:
				await logchannel.send('I could not save the new {} event details into my memory'.format(name))
				print(e)
		else:
			await logchannel.send('An event already exists with the name "{}". I cannot add this to my database.'.format(name))

		#await logchannel.send("Event created")
		
	@commands.Cog.listener()
	async def on_scheduled_event_delete(self, event):
		server = event.guild
		logchannel = get_log_channel(server)
		
		mydb = renfield_sql()
		mycursor = mydb.connect()
		guild = event.guild.name
		name = event.name
		
		# check if event exists before trying to delete it
		event_count = 0
		try:
			sql = "select count(id) from events where name = %s and server = %s"
			val = (name, server.name)
			mycursor.execute(sql,val)
			events = mycursor.fetchone()
			event_count = events[0]
			await logchannel.send('Event deletion: I have found {} events name {} on this server.'.format(event_count, name))
		except Exception as e:
			print(e)
			print(mycursor.statement)
			await logchannel.send('I could not find event {} to delete in my database'.format(name))

		if event_count > 0:
		
			sql = "select id from events where name = %s and server = %s"
			mycursor.execute(sql,(name,server.name))
			events = mycursor.fetchone()
			event_id = events[0]
		
			# delete associated attendance as well
			try:
				sql = "DELETE FROM `attendance` WHERE event_id = %s"
				mycursor.execute(sql, (event_id, ))
				mydb.commit()
				#await logchannel.send('I have cleared the attendance list for the event. {} attendees have been removed'.format(mycursor.rowcount))
			except Exception as e:
				await logchannel.send("I'm sorry Master, I am unable to clear the attendance list for deleted event {}.".format(name))
				print(e)
			
			try:
				sql = "DELETE FROM `events` WHERE id = %s"
				mycursor.execute(sql, (event_id,))
				mydb.commit()
				await logchannel.send('I have removed the {} event from the schedule.'.format(name))
			except Exception as e:
				await logchannel.send("I am unable to remove event {} from the database.".format(name))
				print(e)

		mydb.disconnect()


	@commands.Cog.listener()
	async def on_scheduled_event_update(self, before, after):
		server = before.guild

		logchannel = get_log_channel(server)
		log_voice_channel = get_bot_setting("voice-activity", server.name)
		message = ""
		
		# Update the event name, if it has changed
		doupdate = 0
		if before.name != after.name:
			doupdate = 1
			message = message + "Event name changed from '{}' to '{}'. ".format(before.name, after.name)

		if before.start_time != after.start_time:
			doupdate = 1
			message = message + "Event '{}' start changed to {} (GMT/UTC). ".format(after.name, after.start_time)

		if doupdate:
			result = update_event(before.name, after.name, after.start_time, server.name)
			if result:
				message = message + "Event has been updated in the database."
			else:
				message = message + "Failed to update event '{}' in database.".format(after.name)
		else:
			message = message + "Event '{}' has been modified.".format(after.name)

		if log_voice_channel == "on":
			await logchannel.send(message)
	
	
	@app_commands.command(name='signin', description='Sign In to the event')
	@app_commands.describe(player="Name of the player (not the character name)")
	async def signin(self, ctx, player: str=""):

		author = ctx.user.display_name
		nameid = ctx.user.id
		server = ctx.guild.name
				
		if player != "" and (author.lower() in player.lower() or player.lower() in author.lower()):
			await ctx.send("Wow, Master. That's so weird that your Discord nickname '{}' and your player name '{}' are so similar!".format(author, player))	
		
		memberinfo = add_member(nameid, player, server)
		member_id = memberinfo["member_id"]
		if memberinfo["message"] != "":
			await ctx.response.send_message(memberinfo["message"])
			
		mydb = renfield_sql()
		mycursor = mydb.connect()
		if member_id > 0:
			
			# Is there an event today and has it started?
			isevent = 0
			try:
				sql = "select * from events where now() >= eventdate and now() < cast((eventdate + interval 1 day) as date) ORDER BY eventdate LIMIT 1"
				mycursor.execute(sql)
				events = mycursor.fetchall()
				#await ctx.channel.send("Thank you, Master, the {} event is in progress.".format(events[0][1]))
				isevent = len(events)
			except Exception as e:
				print(e)
				await ctx.response.send_message('I\'m sorry, Master, I could not read the diary to check for an event today.')
				isevent = -1
				
			# Yes? Sign-in
			if isevent > 0:
			
				eventid = events[0][0]

				# Have you already signed in?
				signedin = 0
				try:
					sql = "select count(member_id) from attendance, events where events.id = attendance.event_id and attendance.member_id = %s and events.id = %s"
					val = (member_id, eventid)
					mycursor.execute(sql, val)
					out = mycursor.fetchall()
					signedin = out[0][0]
				except Exception as e:
					print(e)
					await ctx.response.send_message('I\'m sorry, Master, I\'m unable to confirm if you have already signed in.')


				if signedin == 0:
					textreply = ""
					try:
						sql = "INSERT INTO attendance (member_id, event_id, displayname) VALUES (%s, %s, %s)"
						val = (member_id, events[0][0], author)
						mycursor.execute(sql, val)
						mydb.commit()
						signedin = 1
						textreply = 'Thank you Master {}, I have recorded your attendance.'.format(author)
					except Exception as e:
						print(e)
						textreply = 'I\'m sorry, Master, I was unable to record your attendance.'
				
					mydb.disconnect()
				
			
				else:
					textreply = "I see that you have already signed in to this event, Master."

				if signedin == 1:
					nice = get_nice(server)
					await ctx.response.send_message("{} I have to say... {}".format(textreply, nice))

			elif isevent == -1:
				await ctx.response.send_message('Error detected')
			# No? Respond with error
			else:
				await ctx.response.send_message('I\'m sorry Master {}, there is no event currently in progress'.format(author))
		else:
			await ctx.response.send_message('I\'m sorry Master {}, your membership has not been confirmed'.format(author))
		

	@check_is_auth()
	@app_commands.command(name='addevent', description='Schedule a new LARP event')
	@app_commands.describe(
		eventname="Name of the event",
		eventdate="Event date (DD/MM/YYYY)",
	)
	async def addevent(self, ctx, eventname: str, eventdate: str):
		author = ctx.user.display_name
		server = ctx.guild
		
		starttime = get_bot_setting("event_start", server.name)
		endtime = get_bot_setting("event_end", server.name)
		description = get_bot_setting("event_desc", server.name)
		location = get_bot_setting("event_location", server.name)
		
		startdatetime = '{} {}'.format(eventdate, starttime)		
		startdateok = 0
		try:
			event_start = datetime.strptime(startdatetime, '%d/%m/%Y %H:%M')
			startdateok = 1
		except Exception as e:
			await ctx.response.send_message('I\'m sorry, Master, the format of the start date is DD/MM/YYYY')
			print(e)
		enddatetime = '{} {}'.format(eventdate, endtime)
		enddateok = 0
		try:
			event_end = datetime.strptime(enddatetime, '%d/%m/%Y %H:%M')
			enddateok = 1
		except Exception as e:
			await ctx.response.send_message('I\'m sorry, Master, the format of the end date is DD/MM/YYYY')
			print(e)
		
		# add the timezone
		tz = pytz.timezone('UTC')
		event_start = tz.localize(event_start)
		event_end = tz.localize(event_end)
		
		if startdateok and enddateok:
			# check that event is not in the past
			present = datetime.now(tz=timezone.utc)
			if event_start < present:
				await ctx.response.send_message('I\'m sorry, Master, the event start date you have specified is in the past.')
				startdateok = 0
			if event_end < present:
				await ctx.response.send_message('I\'m sorry, Master, the event end date you have specified is in the past.')
				startdateok = 0
			if event_end < event_start:
				await ctx.response.send_message('I\'m sorry, Master, the event end {} is before the start {}.'.format(event_end, event_start))
				startdateok = 0
				
			# check event doesn't already exist
			mydb = renfield_sql()
			mycursor = mydb.connect()
			isduplicate = 1
			try:
				sql = "SELECT COUNT(id) FROM events WHERE name = %s and server = %s"
				mycursor.execute(sql, (eventname,server.name))
				out = mycursor.fetchall()
				isduplicate = out[0][0]
			except Exception as e:
				await ctx.response.send_message('I\'m sorry, Master, I could not check if an event already exists with this name.')
				print(e)
			
			if isduplicate:
				await ctx.response.send_message('I\'m sorry, Master, I already have an event with this name.')

			if startdateok and isduplicate == 0:
			
				if ctx.guild.me.guild_permissions.manage_events: 

					savedok = 0
					try:
						# Create event in Discord
						newevent = await server.create_scheduled_event(name=eventname, 
							start_time=event_start, 
							location=location, 
							end_time=event_end, 
							description=description,
							entity_type=discord.EntityType.external,
							privacy_level=discord.PrivacyLevel.guild_only)
						
						savedok = 1
						await ctx.response.send_message('Thank you, Master. I have added the {} event to my diary'.format(eventname))
					except Exception as e:
						await ctx.response.send_message('I\'m sorry, Master, I could not schedule event {} for {} to {}'.format(eventname, event_start, event_end))
						print(e)
					
					# on-create event will then save the new event to the database
					
				else:
					await ctx.response.send_message('I\'m sorry, Master, I do not have permission to manage events.')



	async def cog_command_error(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.response.send_message("I'm sorry Master, I need more information. Can you tell me the {}".format(error.param.name))


	@check_is_auth()
	@app_commands.command(name='list', description='list game events and attendance')
	async def list(self, ctx):
		'''Displays the list of current events
			example: .list
		'''

		mydb = renfield_sql()
		mycursor = mydb.connect()
		author = ctx.user.display_name
		nameid = ctx.user.id
		guild = ctx.guild.name
		datetoday = date.today()
		outputok = 1
		try:
			# list events and attendance numbers
			sql = """SELECT events.name, events.eventdate, count(attendance.member_id)
				FROM events
						LEFT JOIN attendance
						ON attendance.event_id = events.id
				WHERE server = %s
				GROUP BY events.id
				ORDER BY eventdate DESC"""
			mycursor.execute((sql), (guild,))
			events = mycursor.fetchall()
			headers = ['Name', 'Date', 'Attendance']
			rows = [[e[0], e[1], e[2]] for e in events]
			table = tabulate(rows, headers)
		except Exception as e:
			print(mycursor.statement)
			print(e)
			outputok = 0

		try:
			fd, output = mkstemp(suffix=".txt", prefix="events")
			with os.fdopen(fd, 'w') as file:
				file.write(table)

			with open(output, 'r') as fp:
				await ctx.response.send_message(content="Download full list", file=discord.File(fp, 'events.txt'))
			
			#os.close(fd)
			
		except Exception as e:
			await ctx.response.send_message("I'm sorry Master, I am unable to provide the event details you requested")
			print(mycursor.statement)
			print(e)
			outputok = 0
		
		# try:
			# sql = """SELECT events.name, events.eventdate, count(attendance.member_id)
				# FROM events
						# LEFT JOIN attendance
						# ON attendance.event_id = events.id
				# WHERE server = %s
				# GROUP BY events.id
				# ORDER BY eventdate DESC
				# LIMIT 10"""
			# mycursor.execute((sql), (guild,))
			# events = mycursor.fetchall()
			# headers = ['Name', 'Date', 'Attendance']
			# rows = [[e[0], e[1], e[2]] for e in events]
			# table = tabulate(rows, headers)

			# await ctx.channel.send('```\n' + table + '```')
			
		except Exception as e:
			await ctx.response.send_message("I'm sorry Master, I am unable to provide the event details you requested")
			print(mycursor.statement)
			print(e)
			outputok = 0
			
		mydb.disconnect()
				

	@check_is_auth()
	@app_commands.command(name='attendance', description='List attendance at an event')
	@app_commands.describe(
		event="Name of event"
	)
	async def attendance(self, ctx, event: str):

		mydb = renfield_sql()
		mycursor = mydb.connect()
		author = ctx.user.display_name
		nameid = ctx.user.id
		guild = ctx.guild.name
		datetoday = date.today()
		try:

			# TODO: account for when no one has signed in
			sql = """SELECT COUNT(attendance.id)
				FROM
					attendance, events
				WHERE
					attendance.event_id = events.id
					AND events.name = %s"""

			mycursor.execute((sql), (event,))
			countall = mycursor.fetchall()
			count = countall[0][0]
							
			if count > 0:
				# list users who attended
				sql = """SELECT attendance.displayname, members.playername, events.eventdate
					FROM 
						events,
						attendance,
						members
					WHERE 
						events.server = %s
						AND events.name = %s
						AND events.id = attendance.event_id
						AND members.member_id = attendance.member_id
					ORDER BY attendance.displayname"""

				mycursor.execute((sql), (guild, event))
				events = mycursor.fetchall()
				headers = ['Character', 'Player']
				rows = [[e[0], e[1]] for e in events]
				table = tabulate(rows, headers)
				await ctx.response.send_message('```Attendance for the ' + event + ' event on the {}:\n\n'.format(events[0][2]) + table + '```')
			else:
				await ctx.response.send_message('```Attendance for the ' + event + ' event:\n\nNo attendees```')
		except Exception as e:
			await ctx.response.send_message("I'm sorry Master, I am unable to provide the event details you requested")
			print(e)
		mydb.disconnect()


	@check_is_auth()
	@app_commands.command(name='delete', description='Delete an event (from the database only)')
	@app_commands.describe(
		name="Event name to delete",
	)
	async def delete(self, ctx, name: str):
		mydb = renfield_sql()
		mycursor = mydb.connect()
		author = ctx.user.display_name
		guild = ctx.guild.name
		nameid = ctx.user.id
		
		# check if event exists before trying to delete it
		event_id = 0
		try:
			sql = "select id from events where name = %s"
			mycursor.execute(sql,(name,))
			events = mycursor.fetchall()
			event_id = events[0][0]
			#await ctx.response.send_message('I have found events ID {} with that name.'.format(event_id))
		except Exception as e:
			print(e)
			await ctx.response.send_message('I\'m sorry, Master {}, I was unable to check for that event.'.format(nameid))	

		if event_id > 0:
			# delete associated attendance as well
			try:
				sql = "DELETE FROM `attendance` WHERE event_id = '{}'".format(event_id)
				mycursor.execute(sql)
				mydb.commit()

				#await ctx.response.send_message('I have cleared the attendance list for the event. {} attendees have been removed'.format(mycursor.rowcount))
			except Exception as e:
				await ctx.response.send_message("I'm sorry Master, I am unable to clear the attendance list.")
				print(e)
			
			try:
				sql = "DELETE FROM `events` WHERE name = '{}'".format(name)
				mycursor.execute(sql)
				mydb.commit()
				await ctx.response.send_message('Of course Master {}, I have removed the {} event from the schedule.'.format(author, name))
			except Exception as e:
				await ctx.response.send_message("I'm sorry Master, I am unable to remove the event from the calendar.")
				print(e)
		#else:
		#	await ctx.response.send_message('I\'m sorry, Master {}, the {} event does not exist'.format(author, name))	
		mydb.disconnect()



async def setup(bot):
	await bot.add_cog(Events(bot))
