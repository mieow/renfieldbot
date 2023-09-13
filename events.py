import discord
from discord.ext import commands
from tabulate import tabulate
import mysql.connector
from datetime import date
from datetime import datetime
import renfield_sql
from common import check_is_auth
# from discord_slash import cog_ext, SlashContext
# from discord_slash.utils.manage_commands import create_option, create_choice
from discord import Embed, app_commands
from dotenv import load_dotenv
import os

load_dotenv()
GUILDID = int(os.getenv('DISCORD_GUILD_ID'))


class Events(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None
	
	@app_commands.command(name='signin', description='Sign In to the event')
	@app_commands.describe(player="Name of the player (not the character name)")
	async def signin(self, ctx, player: str=""):
		mydb = renfield_sql.renfield_sql()

		author = ctx.user.display_name
		nameid = ctx.user.id
		server = ctx.guild.name
				
		if player != "" and (author.lower() in player.lower() or player.lower() in author.lower()):
			await ctx.send("Wow, Master. That's so weird that your Discord nickname '{}' and your player name '{}' are so similar!".format(author, player))	
		
		memberinfo = mydb.add_member(nameid, player, server)
		member_id = memberinfo["member_id"]
		if memberinfo["message"] != "":
			await ctx.response.send_message(memberinfo["message"])

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
				
			
				else:
					textreply = "I see that you have already signed in to this event, Master."

				if signedin == 1:
					nice = mydb.get_nice(server)
					await ctx.response.send_message("{} I have to say... {}".format(textreply, nice))

			elif isevent == -1:
				await ctx.response.send_message('Error detected')
			# No? Respond with error
			else:
				await ctx.response.send_message('I\'m sorry Master {}, there is no event currently in progress'.format(author))
		else:
			await ctx.response.send_message('I\'m sorry Master {}, your membership has not been confirmed'.format(author))
		mydb.disconnect()
		

	# @signin.error
	# async def signin_error(ctx, error):
		# if isinstance(error, commands.MissingRequiredArgument):
			# await ctx.send("I'm sorry Master, Who should I say is attending the event?")

	@app_commands.command(name='new', description='Schedule a new LARP event')
	@app_commands.describe(
		eventname="Name of the event",
		date="Event date (DD/MM/YYYY)",
		time="Optional Start time (06:00pm default)"
	)
	@check_is_auth()
	async def new(self, ctx, eventname: str, date: str, time: str='06:00pm'):
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		author = ctx.user.display_name
		server = ctx.guild.name
		date_time = '{} {}'.format(date, time)
		
		# Check if user is allowed to use this command
		admin_role = mydb.get_bot_setting("admin_role", "storytellers", server)
		has_admin_role = (admin_role.lower() in [y.name.lower() for y in ctx.user.roles])
		if not (ctx.user.guild_permissions.administrator or has_admin_role):
			await ctx.response.send_message('I\'m sorry, Master, you do not have the authority to ask me to do that')
			return
		
		# add to database
		dateok = 0
		try:
			event_date = datetime.strptime(date_time, '%d/%m/%Y %I:%M%p')
			dateok = 1
		except Exception as e:
			await ctx.response.send_message('I\'m sorry, Master, the format of the date and optional time is DD/MM/YYYY [08:00pm]')
			print(e)
		
		if dateok:
			# check that event is not in the past
			present = datetime.now()
			if event_date.date() < present.date():
				await ctx.response.send_message('I\'m sorry, Master, event date you have specified is in the past.')
				dateok = 0
			
			# check event doesn't already exist
			mycursor = mydb.connect()
			isduplicate = 1
			try:
				sql = "SELECT COUNT(id) FROM events WHERE name = %s"
				mycursor.execute(sql, (eventname,))
				out = mycursor.fetchall()
				isduplicate = out[0][0]
			except Exception as e:
				await ctx.response.send_message('I\'m sorry, Master, I could not check if an event already exists with this name.')
				print(e)
			
			if isduplicate:
				await ctx.response.send_message('I\'m sorry, Master, I already have an event with this name.')
			
			if dateok and isduplicate == 0:
				try:
					sql = "INSERT INTO events (name, server, eventdate) VALUES (%s, %s, %s)"
					val = (mydb.connection._cmysql.escape_string(eventname), mydb.connection._cmysql.escape_string(server), event_date)
					mycursor.execute(sql, val)
					mydb.commit()
					await ctx.response.send_message('Thank you Master {}, I have recorded the {} event in the diary for {}'.format(author, eventname, event_date))
				except Exception as e:
					await ctx.response.send_message('I\'m sorry, Master, I could not complete your command')
					print(e)
		mydb.disconnect()

	async def cog_command_error(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.response.send_message("I'm sorry Master, I need more information. Can you tell me the {}".format(error.param.name))


	@app_commands.command(name='list', description='list game events and attendance')
	@app_commands.describe(
		action="Specify what event information to show",
		event="Name of event (Optional)"
	)
	@app_commands.choices(action=[
		app_commands.Choice(name="List all events", value="all"),
		app_commands.Choice(name="Show next event (default)", value="next"),
		app_commands.Choice(name="Show attendance list of a specific event", value="one"),
	])
	async def list(self, ctx, action: str='next', event: str=''):
		'''Displays the list of current events
			example: .list
		'''
		# TODO: NEXT EVENT DOESN'T SHOW NEXT ONE FROM NOW
		# list	 - list next event
		# list all - list events and attendance numbers
		# list <event> - list who attended the event (ST Only)
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		author = ctx.user.display_name
		nameid = ctx.user.id
		guild = ctx.guild.name
		datetoday = date.today()
		try:
			if action == 'all':
				# list events and attendance numbers
				sql = """SELECT events.name, events.eventdate, count(attendance.member_id)
					FROM events
							LEFT JOIN attendance
							ON attendance.event_id = events.id
					WHERE server = %s
					GROUP BY events.id
					ORDER BY eventdate"""
				mycursor.execute((sql), (mydb.connection._cmysql.escape_string(guild),))
				events = mycursor.fetchall()
				headers = ['Name', 'Date', 'Attendance']
				rows = [[e[0], e[1], e[2]] for e in events]
				table = tabulate(rows, headers)
				await ctx.response.send_message('```\n' + table + '```')
			elif action == 'next':
				# list next event
				headers = ['Name', 'Date']
				sql = "SELECT * FROM events WHERE server = %s AND now() < eventdate ORDER BY eventdate LIMIT 1"
				mycursor.execute((sql), (mydb.connection._cmysql.escape_string(guild),))
				events = mycursor.fetchall()
				await ctx.response.send_message("Master {}, the next event is {} and it takes place on the {}".format(author, events[0][1], events[0][3]))
			else:
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


	@app_commands.command(name='delete', description='Delete an event')
	@app_commands.describe(
		name="Event name to delete",
	)
	@check_is_auth()
	async def delete(self, ctx, name: str):
		mydb = renfield_sql.renfield_sql()
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
		else:
			await ctx.response.send_message('I\'m sorry, Master {}, the {} event does not exist'.format(author, name))	
		mydb.disconnect()

	# # @delete.error
	# # async def delete_error(ctx, error):
		# # if isinstance(error, commands.MissingRequiredArgument):
			# # await ctx.send("I'm sorry Master, I need more information. Can you tell me the {} of the event?".format(error.param.name))

	# async def cog_command_error(self, ctx, error):
		# if isinstance(error, commands.MissingRequiredArgument):
			# await ctx.send("I'm sorry Master, I need more information. Can you tell me the {}".format(error.param.name))


async def setup(bot):
	await bot.add_cog(Events(bot))
