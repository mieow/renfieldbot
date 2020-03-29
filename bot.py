# bot.py
import os

import discord
from dotenv import load_dotenv
from discord.ext import commands
from sqlalchemy import engine, create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from tabulate import tabulate

from models import Base, Event, Member, Attendance

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

engine = create_engine('sqlite:///event-bot.db', echo=False)
Session = sessionmaker(bind=engine)
session = Session()


# If table doesn't exist, Create the database
if not engine.dialect.has_table(engine, 'event'):
    Base.metadata.create_all(engine)



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
async def signin(ctx, character):
    # set display name to be the character name
    author = ctx.message.author.display_name
	# What is today's date?
	# Is there an event today and has it started?
	# Yes? Sign-in
    await ctx.send('Thank you Master {}, I have recorded your attendance'.format(author))
	# No? Respond with error

@bot.command(name='new', help='Start a new LARP event: .new <name> dd/mm/yyyy <time>')
@commands.has_role('storytellers')
async def new(ctx, name: str, date: str, time: str='08:00pm'):
    author = ctx.message.author.display_name
    server = ctx.message.guild.name
    date_time = '{} {}'.format(date, time)
    try:
        event_date = datetime.strptime(date_time, '%d/%m/%Y %I:%M%p')
        event = Event(name=name, server=server, date=event_date)
        session.add(event)
        session.commit()
        await ctx.send('Thank you Master {}, I have recorded the {} event in the diary for {}'.format(author, name, event.date))
    except Exception as e:
        await ctx.send('I\'m sorry, Master, I could not complete your command')
        print(e)

@new.error
async def new_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("I'm sorry Master, I need more information. Can you tell me the {} of the event?".format(error.param.name))



@bot.command(name='list', help='list game events')
async def list(ctx):
    '''Displays the list of current events
        example: ?list
    '''
	# list     - list next event
	# list all - list events and attendance numbers
	# list <event> - list who attended the event (ST Only)
    try:
        events = session.query(Event).order_by(Event.date).all()
        headers = ['Name', 'Date', 'Server']
        rows = [[e.name, e.date, e.server] for e in events]
        table = tabulate(rows, headers)
        await ctx.send('```\n' + table + '```')
    except Exception as e:
        await ctx.send("I'm sorry Master, I am unable to list the upcoming events.")
        print(e)


@bot.command(name='delete', help='Delete an event: .delete <event>')
@commands.has_role('storytellers')
async def delete(ctx, name: str):
        await ctx.send('Of course Master {}, I will remove the {} event from the schedule.'.format(author, name, event.date))

@delete.error
async def delete_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("I'm sorry Master, I need more information. Can you tell me the {} of the event?".format(error.param.name))

	
# create tables for signing
# - attendance: who has signed in
# - list: by default, only show next event
# - del: delete an event (st only)
# - signin: sign in to today's event



if __name__ == '__main__':
    try:
        bot.run(TOKEN)
    except Exception as e:
        print('Renfield is not waking up')
        print(e)
    finally:
        print('Renfield has gone back to bed')
        session.close()

