#!/usr/bin/env python3

import os
import mysql.connector
import discord
from dotenv import load_dotenv
from discord.ext import commands
#from sqlalchemy import engine, create_engine
#from sqlalchemy.orm import sessionmaker
from datetime import datetime
from tabulate import tabulate
from datetime import date

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
DATABASE_USERNAME = os.getenv('DATABASE_USERNAME')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')

# Connect to database
mydb = mysql.connector.connect(
  host="localhost",
  user=DATABASE_USERNAME,
  passwd=DATABASE_PASSWORD,
  database="discordbot"
)
mycursor = mydb.cursor()

description = 'GVLARP Renfield Bot'
bot = commands.Bot(command_prefix='.', description=description)



# Connect to Discord when ready
@bot.event
async def on_ready():
	print(bot.user.id)
	print(bot.user.name)
	print('---------------')
	print('Renfield is at your service!')

# Ping the bot
@bot.command(name='ping', help='Is Renfield listening?')
async def ping(ctx):
	'''Check that Renfield is listening'''
	author = ctx.message.author.display_name
	#server = ctx.message.guild.name
	await ctx.send('Yes, Master {}, I am listening!'.format(author))
 
@bot.command(name='signin', help='Sign In to the event')
async def signin(ctx, *, player: str=""):
	# TODO: fix - signing in to no/deleted event
	# TODO: set display name to be the character name
	author = ctx.message.author.display_name
	nameid = ctx.message.author.id
	# add them to the members table if they don't exist
	count = 0
	try:
		sql = "select count(member_id) from members where name = '{}'".format(nameid)
		mycursor.execute(sql)
		countall = mycursor.fetchall()
		count = countall[0][0]
		#await ctx.send('Congratulations Master. I checked for your code name {} on the members list.'.format(nameid))
	except Exception as e:
		print(e)
		await ctx.send('I\'m sorry, Master {}, I was unable to check your name on the member list.'.format(nameid))	
	
	member_id = 0
	if count == 0 and player == "":
		await ctx.send('I\'m sorry, Master, please let me know your Out Of Character name for the membership records')
	elif count == 0:
		#Add to member table
		try:
			sql = "INSERT INTO members (name, playername, wordpress_id) VALUES (%s, %s, %s)"
			val = (nameid, player, "")
			mycursor.execute(sql, val)
			mydb.commit()
			member_id = mycursor.lastrowid
			#await ctx.send('Thank you, Master. I have added your name to the members list.')
		except Exception as e:
			print(e)
			await ctx.send('I\'m sorry, Master, I was unable to add your name to the member list.')

	else:

		# or get their member_id from the the table
		try:
			sql = "select member_id from members where name = '{}'".format(nameid)
			mycursor.execute(sql)
			member_ids = mycursor.fetchall()
			member_id = member_ids[0][0]
			#await ctx.send('Thank you, Master. I have confirmed that you are a member with membership number {}.'.format(member_id))	
		except Exception as e:
			print(e)
			await ctx.send('I\'m sorry, Master, I was unable to find your membership number.')

	if member_id > 0:
		
		# Is there an event today and has it started?
		isevent = 0
		try:
			sql = "select * from events where now() >= eventdate and now() < cast((eventdate + interval 1 day) as date) ORDER BY eventdate LIMIT 1"
			mycursor.execute(sql)
			events = mycursor.fetchall()
			#await ctx.send("Thank you, Master, the {} event is in progress.".format(events[0][1]))
			isevent = len(events)
		except Exception as e:
			print(e)
			await ctx.send('I\'m sorry, Master, I could not read the diary to check for an event today.')
			isevent = -1
			
		# Yes? Sign-in
		if isevent > 0:
		
			eventid = events[0][0]

			# Have you already signed in?
			signedin = 0
			try:
				sql = "select count(member_id) from attendance, events where events.id = attendance.event_id and attendance.member_id = %s and events.id = '%s'"
				val = (member_id, eventid)
				mycursor.execute(sql, val)
				out = mycursor.fetchall()
				signedin = out[0][0]
			except Exception as e:
				print(e)
				await ctx.send('I\'m sorry, Master, I\'m unable to confirm if you have already signed in.')


			if signedin == 0:
				try:
					sql = "INSERT INTO attendance (member_id, event_id, displayname) VALUES (%s, %s, %s)"
					#await ctx.send(sql)
					#await ctx.send(events)
					val = (member_id, events[0][0], author)
					mycursor.execute(sql, val)
					mydb.commit()
					await ctx.send('Thank you Master {}, I have recorded your attendance'.format(author))
				except Exception as e:
					print(e)
					await ctx.send('I\'m sorry, Master, I was unable to record your attendance.')
			
			else:
				await ctx.send("I see that you have already signed in to this event, Master.")

		elif isevent == -1:
			await ctx.send('Error detected')
		# No? Respond with error
		else:
			await ctx.send('I\'m sorry Master {}, there is no event currently in progress'.format(author))
	else:
		await ctx.send('I\'m sorry Master {}, your membership has not been confirmed'.format(author))
	

# @signin.error
# async def signin_error(ctx, error):
	# if isinstance(error, commands.MissingRequiredArgument):
		# await ctx.send("I'm sorry Master, Who should I say is attending the event?")


@bot.command(name='new', help='Schedule a new LARP event', usage='<name> dd/mm/yyyy [08:00pm]')
@commands.has_role('storytellers')
async def new(ctx, name: str, date: str, time: str='08:00pm'):
	author = ctx.message.author.display_name
	server = ctx.message.guild.name
	date_time = '{} {}'.format(date, time)
	# add to database
	dateok = 0
	try:
		event_date = datetime.strptime(date_time, '%d/%m/%Y %I:%M%p')
		dateok = 1
	except Exception as e:
		await ctx.send('I\'m sorry, Master, the format of the date and optional time is DD/MM/YYYY [08:00pm]')
		print(e)
	
	# check that event is not in the past
	present = datetime.now()
	if event_date.date() < present.date():
		await ctx.send('I\'m sorry, Master, event date you have specified is in the past.')
		dateok = 0
	
	# check event doesn't already exist
	isduplicate = 1
	try:
		sql = "SELECT COUNT(id) FROM events WHERE name = '{}'".format(name)
		mycursor.execute(sql)
		out = mycursor.fetchall()
		isduplicate = out[0][0]
	except Exception as e:
		await ctx.send('I\'m sorry, Master, I could not check if an event already exists with this name.')
		print(e)
	
	if isduplicate:
		await ctx.send('I\'m sorry, Master, I already have an event with this name.')
	
	if dateok and isduplicate == 0:
		try:
			sql = "INSERT INTO events (name, server, eventdate) VALUES (%s, %s, %s)"
			val = (name, server, event_date)
			mycursor.execute(sql, val)
			mydb.commit()
			await ctx.send('Thank you Master {}, I have recorded the {} event in the diary for {}'.format(author, name, event_date))
		except Exception as e:
			await ctx.send('I\'m sorry, Master, I could not complete your command')
			print(e)

@new.error
async def new_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		await ctx.send("I'm sorry Master, I need more information. Can you tell me the {} of the event?".format(error.param.name))
	


@bot.command(name='list', usage='[all | next | <event>]', brief='list game events and attendance', help='list game events and attendance.\n\nall\t: all events and attendance\nnext\t: next event\n<name>\t: list of attendees')
async def list(ctx, *, action: str='next'):
	'''Displays the list of current events
		example: .list
	'''
	# list	 - list next event
	# list all - list events and attendance numbers
	# list <event> - list who attended the event (ST Only)
	author = ctx.message.author.display_name
	guild = ctx.message.guild.name
	datetoday = date.today()
	try:
		if action == 'all':
			# list events and attendance numbers
			sql = """SELECT events.name, events.eventdate, count(attendance.member_id)
				FROM events
						LEFT JOIN attendance
						ON attendance.event_id = events.id
				WHERE server = '{}'
				GROUP BY events.id
				ORDER BY eventdate""".format(guild)
			mycursor.execute(sql)
			events = mycursor.fetchall()
			headers = ['Name', 'Date', 'Attendance']
			rows = [[e[0], e[1], e[2]] for e in events]
			table = tabulate(rows, headers)
			await ctx.send('```\n' + table + '```')
		elif action == 'next':
			# list next event
			headers = ['Name', 'Date']
			sql = "SELECT * FROM events WHERE server = '{}' ORDER BY eventdate LIMIT 1".format(guild)
			mycursor.execute(sql)
			events = mycursor.fetchall()
			await ctx.send("Master {}, the next event is {} and it takes place on the {}".format(author, events[0][1], events[0][3]))
		else:
			# TODO: account for when no one has signed in
			sql = """SELECT COUNT(attendance.id)
				FROM
					attendance, events
				WHERE
					attendance.event_id = events.id
					AND events.name = '{}'""".format(action)
			mycursor.execute(sql)
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
						events.server = '{}'
						AND events.name = '{}'
						AND events.id = attendance.event_id
						AND members.member_id = attendance.member_id
					ORDER BY attendance.displayname""".format(guild, action)
				#await ctx.send(sql)
				mycursor.execute(sql)
				events = mycursor.fetchall()
				headers = ['Character', 'Player']
				rows = [[e[0], e[1]] for e in events]
				table = tabulate(rows, headers)
				await ctx.send('```Attendance for the ' + action + ' event on the {}:\n\n'.format(events[0][2]) + table + '```')
			else:
				await ctx.send('```Attendance for the ' + action + ' event:\n\nNo attendees```')
	except Exception as e:
		await ctx.send("I'm sorry Master, I am unable to provide the event details you requested")
		print(e)


@bot.command(name='delete', help='Delete an event')
@commands.has_role('storytellers')
async def delete(ctx, name: str):
	author = ctx.message.author.display_name
	guild = ctx.message.guild.name
	# check if event exists before trying to delete it
	event_id = 0
	try:
		sql = "select id from events where name = '{}'".format(name)
		mycursor.execute(sql)
		events = mycursor.fetchall()
		event_id = events[0][0]
		#await ctx.send('I have found events ID {} with that name.'.format(event_id))
	except Exception as e:
		print(e)
		await ctx.send('I\'m sorry, Master {}, I was unable to check for that event.'.format(nameid))	

	if event_id > 0:
		# delete associated attendance as well
		try:
			sql = "DELETE FROM `attendance` WHERE event_id = '{}'".format(event_id)
			mycursor.execute(sql)
			mydb.commit()
			#await ctx.send('I have cleared the attendance list for the event. {} attendees have been removed'.format(mycursor.rowcount))
		except Exception as e:
			await ctx.send("I'm sorry Master, I am unable to clear the attendance list.")
			print(e)
		
		try:
			sql = "DELETE FROM `events` WHERE name = '{}'".format(name)
			mycursor.execute(sql)
			mydb.commit()
			await ctx.send('Of course Master {}, I have removed the {} event from the schedule.'.format(author, name))
		except Exception as e:
			await ctx.send("I'm sorry Master, I am unable to remove the event from the calendar.")
			print(e)
	else:
		await ctx.send('I\'m sorry, Master {}, the {} event does not exist'.format(author, name))	

@delete.error
async def delete_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		await ctx.send("I'm sorry Master, I need more information. Can you tell me the {} of the event?".format(error.param.name))



if __name__ == '__main__':
	try:
		bot.run(TOKEN)
	except Exception as e:
		print('Renfield is not waking up')
		print(e)
	finally:
		print('Renfield has gone back to bed')
		mycursor.close
		mydb.close

