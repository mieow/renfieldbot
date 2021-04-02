import discord
import mysql.connector
from discord.ext import commands
import renfield_sql
from datetime import date
import re
from tabulate import tabulate

class Linears(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None


	
	# create new linear
	@commands.command(name='addlinear', 
		usage='[<linear-name>]',
		brief='Add a linear chat and voice channel',
		help='''
		
		Use this command to automatically create a voice and matching text
		chat channel for linears.
		
		Optionally specify a unique name for the linear by adding a name after the .addlinear command.
		
		''')
	@commands.has_role('storytellers')
	async def addlinear(self, ctx, prefix: str='linear'):
		server = ctx.message.guild
		#await ctx.send("Create linear for {}".format(server.name))

		# get the category for linears
		name = "Linears"
		category = discord.utils.get(ctx.guild.categories, name=name)
		#await ctx.send("Create linear in category {}".format(category.name))
		
		# set channel name based on the date
		today = date.today()
		d1 = today.strftime("%d-%b-%Y")
		txtchannelname = "{}-{}".format(prefix, d1).lower()
		voxchannelname = "voice-{}-{}".format(prefix, d1).lower()
		#await ctx.send("Create linear with name {}".format(channelname))
		
		# TEXT CHANNELS
		# check if channel already exists
		# check that there aren't too many linear channels
		found = 0
		mycount = 0
		try:
			tstchannel = discord.utils.get(server.text_channels, name=txtchannelname)
			if tstchannel is not None:
				found = 1
		
			for tstchannel in server.text_channels:
				#await ctx.send("Match {} with {}".format(tstchannel.name, txtchannelname))
				if tstchannel.category_id == category.id:
					mycount += 1
			if found == 1:
				await ctx.send("Channel {} already exists".format(txtchannelname))
			if mycount >= 3:
				await ctx.send("Too many text channels. Delete one first.".format(mycount,name))
		except Exception as e:
			await ctx.send('Error when validating channel creation')
			print(e)

		# create text channel
		if not found and mycount < 3:
			try:
				await server.create_text_channel(txtchannelname, category=category)
				await ctx.send("Created channel {}".format(txtchannelname))
			except Exception as e:
				await ctx.send('Error when creating text channel')
				print(e)

		
		# VOICE CHANNELS
		# check if channel already exists
		# check that there aren't too many linear channels
		found = 0
		mycount = 0
		try:
			tstchannel = discord.utils.get(server.voice_channels, name=voxchannelname)
			if tstchannel is not None:
				found = 1
		
			for tstchannel in server.voice_channels:
				if tstchannel.category_id == category.id:
					mycount += 1
			if found == 1:
				await ctx.send("Channel {} already exists".format(voxchannelname))
			if mycount >= 3:
				await ctx.send("Too many voice channels. Delete one first.".format(mycount,name))
		except Exception as e:
			await ctx.send('Error when validating channel creation')
			print(e)
		
		# create text channel
		if not found and mycount < 3:
			try:
				await server.create_voice_channel(voxchannelname, category=category)
				await ctx.send("Created channel {}".format(voxchannelname))
			except Exception as e:
				await ctx.send('Error when creating voice channel')
				print(e)

		# start logging
		
		
	# remove linear
	#-----------------
	
	
	# set bloodpool/willpower/initiative
	# TODO: MANUALLY SET CELERITY ACTIONS
	#----------------------------
	@commands.command(name='set', 
		usage='[<will | blood | init> <level>]',
		brief='Set stats and levels for your character',
		help='''
		
		Use this command to set your characters bloodpool, etc. for a linear.
		
		For example:
			.set willpower 6
			.set bloodpool 10
			.set initiative 12
			.set
			
		If you use the command by itself then Renfield will list all your current settings.
		''')
	async def set(self, ctx, setting_name : str="display", setting_level : int=0):
		author = ctx.message.author.display_name
		nameid = ctx.message.author.id
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		server = ctx.message.guild.name
		ok = 0
		if setting_name.lower() == "will" or setting_name.lower() == "willpower":
			setting_name = "Willpower"
		elif setting_name.lower() == "blood" or setting_name.lower() == "bloodpool":
			setting_name = "Bloodpool"
		elif setting_name.lower() == "init" or setting_name.lower() == "initiative":
			setting_name = "Initiative"
		elif setting_name.lower() == "display":
			setting_name = ""
			# show all current settings
			try:
				sql = "select setting_name, setting_level from linearsettings where name = %s and server = %s"
				val = ("{}".format(nameid), server)
				mycursor.execute(sql, val)
				settings = mycursor.fetchall()
				headers = ['Setting', 'Level']
				rows = [[e[0], e[1]] for e in settings]
				table = tabulate(rows, headers)
				ok = 1
				await ctx.send('```\n' + table + '```')
				
			except Exception as e:
				print(e)
				await ctx.send('Failed to retrieve current settings')	
			
		else:
			await ctx.send("I'm sorry Master {}, '{}' is not a valid setting. Please choose Willpower, Bloodpool or Initiative".format(author, setting_name))
			setting_name = ""
			
		
		# does this user already have an entry in the table
		count = 0
		if setting_name != "":
			ok = mydb.save_linear_setting(nameid, setting_name, setting_level, server)
			
			if ok:
				await ctx.send('Thank you {}, your {} is set to {}'.format(author, setting_name, setting_level))
			else:
				await ctx.send('I\'m sorry, Master {}, I am unable to record your {}'.format(author, setting_name))
		

		mydb.disconnect()


	# spend bloodpool/willpower/initiative
	# TODO: Update help for "on celerity"
	#----------------------------
	@commands.command(name='spend', 
		usage='<number> <blood | will> [on <celerity | potence | fortitude| text>]',
		brief='Spend blood and willpower',
		help='''
		
		Use this command to keep track of your bloodpool and willpower spends.
		
		For example:
		.spend 1 willpower
		.spend 1 bloodpool
		.spend 2 blood on celerity
		.spend 1 blood on potence
		.spend 1 blood on fortitude
		.spend 3 blood on [insert your own text here]
		
		Your current blood or willpower will be updated.  You can see your current totals by using the .set command without arguments.

		''')
	async def spend(self, ctx, amount : int=1, setting : str="blood", *, setting_detail: str=""):
		mydb = renfield_sql.renfield_sql()
		author = ctx.message.author.display_name
		nameid = ctx.message.author.id
		server = ctx.message.guild.name
		if setting.lower() == "will" or setting.lower() == "willpower":
			setting_name = "Willpower"
		elif setting.lower() == "blood" or setting.lower() == "bloodpool":
			setting_name = "Bloodpool"
		else:
			await ctx.send("I'm sorry Master {}, '{}' is not a valid setting. Please choose willpower or blood".format(author, setting))
			setting_name = ""

		if setting_detail != "":
			if setting_detail.startswith("on"):
				if setting_name == "Bloodpool" and "celerity" in setting_detail.lower():
					ok = mydb.save_linear_setting(nameid, "CelerityActions", amount, server)
					if ok:
						await ctx.send("Noting spend for extra Celerity actions")
				if setting_name == "Bloodpool" and "potence" in setting_detail.lower():
					ok = mydb.save_linear_setting(nameid, "Potence", amount, server)
					if ok:
						await ctx.send("Noting spend for Potence")
				if setting_name == "Bloodpool" and "fortitude" in setting_detail.lower():
					ok = mydb.save_linear_setting(nameid, "Fortitude", amount, server)
					if ok:
						await ctx.send("Noting spend for Fortitude")
	
		if setting_name != "":
			current = mydb.get_linear_setting(nameid, setting_name, 10, server)	
				
			# total = current - amount
			total = current - amount
			# - report error if < 0
			if total < 0:
				await ctx.send('Master {}, you cannot spend {} as it would take your {} to {}.'.format(author, amount, setting, total))
			else:
				# - otherwise
				#	- update database
				ok = mydb.save_linear_setting(nameid, setting_name, total, server)
				if ok:
					await ctx.send('Master {}, you have spent {} {} {}. Your {} is now {}.'.format(author, amount, setting, setting_detail, setting_name, total))
				else:
					await ctx.send("I'm sorry, Master {}, that change failed to save".format(author))	
		
			mydb.disconnect()

	# ST ONLY
	# .combat list
	# List initiative order
	#	- report in order, and list everyone in channel so can see who hasn't rolled
	# .combat clear
	# 	Clear initiative list
	# .combat start
	# Reset combat to the start, round count = 1
	# .combat
	#	This is round X, normal actions. Next to act is {} on initiative {}
	
	# TopInitiative
	# TopCelerity
	# Round
	
	@commands.command(name='combat', usage='[report | clear | start]', brief='Manage Initiative and combat rounds', help='''Run combat using these commands.
	
	Storytellers use this command to manage combat.
	
	report\t: List initiative of channel members
	clear\t: Clear initiative list
	start\t: Start the combat - set round to 1
	
	Use the .next command to progress to the next in the initiative order.''')
	@commands.has_role('storytellers')
	async def combat(self, ctx, cmd: str = ""):
		server = ctx.message.guild
		author = ctx.message.author.display_name
		nameid = ctx.message.author.id
		server = ctx.message.guild.name
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		botid = ctx.bot.user.id

		# is this user actually in a voice channel?
		if ctx.message.author.voice is not None:
			# which voice channel is this user in?
			channel = ctx.message.author.voice.channel
			
			# who else is in the channel?
			members = channel.members

			if cmd == "report":
				rows = []
				
				# list summary table of combat info
				for member in members:
					if member.nick is None:
						cname = member.name
					else:
						cname = member.nick
					result1 = mydb.get_linear_setting(member.id, "Initiative", "-", server)
					result2 = mydb.get_linear_setting(member.id, "CelerityActions", "-", server)
					result3 = mydb.get_linear_setting(member.id, "Bloodpool", "-", server)
					result4 = mydb.get_linear_setting(member.id, "Potence", 0, server)
					result5 = mydb.get_linear_setting(member.id, "Fortitude", 0, server)
					
					spends = ""
					if result4 > 0:
						spends = spends + "P"
					if result5 > 0:
						spends = spends + "F"
					
					rows.append([cname, result1, result2, result3, spends])

				headers = ['Character', 'Initiative', 'Celerity Actions', "Bloodpool","Spends"]
				table = tabulate(rows, headers)
				await ctx.send('```\n' + table + '```')
				
				# list summary of initiative order
				order = self.get_init_order(members, botid, server)
				rows=[]
				turn = 1
				curraction = mydb.get_linear_setting(botid, "CurrentAction", 1, server)
				round = mydb.get_linear_setting(botid, "Round", 1, server)
				for action in order:
					if curraction == turn:
						marker = "<-- Next"
					else:
						marker = ""
					rows.append([turn, action["name"],action["atype"], action["init"], action["caction"], marker])
					turn += 1
				#print(order)
				headers = ["","Name","Action Type","Initiative","Celerity Action",""]
				table2 = tabulate(rows, headers)
				await ctx.send('```\n' + table2 + '```')
				
				if curraction == 0:
					await ctx.send('```\nAction: Spend blood/Declare actions\nRound: {}```'.format(round))
				else:
					await ctx.send('```\nAction: {}\nRound: {}```'.format(curraction, round))
				
			elif cmd == "clear":
				#ok = 1
				for member in members:
					nameid = member.id
					mydb.clear_linear_setting(nameid, "Initiative", server)
					mydb.clear_linear_setting(nameid, "CelerityActions", server)
					mydb.clear_linear_setting(nameid, "Potence", server)
					mydb.clear_linear_setting(nameid, "Fortitude", server)
						
				await ctx.send("I have cleared the initiative settings for everyone in the channel.")
		
			elif cmd == "start":
				# do we have this setting saved?
				botid = ctx.bot.user.id
				#count = 0
				
				ok = mydb.save_linear_setting(botid, "Round", 1, server)
				
				order = self.get_init_order(members, botid, server)
				
				ok = mydb.save_linear_setting(botid, "CurrentAction", 1, server)

				await ctx.send("Ready to begin round 1. Please make your blood spends.")
				
				
			else:
				botid = ctx.bot.user.id
				round = mydb.get_linear_setting(botid, "Round", 1, server)
				action = mydb.get_linear_setting(botid, "CurrentAction", 0, server)
				order = self.get_init_order(members, botid, server)
				
				if action == 0:
					await ctx.send("This is round {}, Spend blood and prepare your actions.".format(round))
				else:
					thisround = order[action-1]
					
					if thisround["atype"] == "Normal":
						await ctx.send("This is round {}, normal actions on initiative {}. Next to act is {}.".format(round, thisround["init"], thisround["name"]))
					else:
						await ctx.send("This is round {}, celerity action {} on initiative {}. Next to act is {}.".format(round, thisround["caction"], thisround["init"], thisround["name"]))
				
		else:
			await ctx.send("Please accept my apologies. You must be in a voice channel to use this command.")
					

		mydb.disconnect()
	
	
	# set celerity actions for the round
	#	- via blood spend "spend 2 blood on celerity"
	#	- via 'set' command

    # ST ONLY
	# .next command - cycle through
	# normal action, then celerity actions
	# decrement #celerity actions every time you get your celerity action

	# "Master Jen, Angus acts next on normal action with initiative 30
	# "Round X begins with normal actions"
	#
	# "This is a new round. Please make your blood spends now."
	@commands.command(name='next', help='Progress through initiative rounds')
	@commands.has_role('storytellers')
	async def next(self, ctx):
		server = ctx.message.guild
		author = ctx.message.author.display_name
		nameid = ctx.message.author.id
		server = ctx.message.guild.name
		botid = ctx.bot.user.id
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		
		# is this user actually in a voice channel?
		if ctx.message.author.voice is not None:
			# which voice channel is this user in?
			channel = ctx.message.author.voice.channel
			
			# who else is in the channel?
			members = channel.members
			
			order = self.get_init_order(members, botid, server)
			#print(order)
			
			# Which combat round are we on?
			round = mydb.get_linear_setting(botid, "Round", 1, server)
						
			# Which initiative are we at?
			action = mydb.get_linear_setting(botid, "CurrentAction", 0, server)

			#await ctx.send("Action = {}, list = {}".format(action, len(order)))

			# whose action is it?
			if action == len(order):
				newround = 1
			else:
				newround = 0
			
			if action == 0:
				await ctx.send("This is the beginning of round {}. Please make your blood spends.".format(round))
			else:
				thisround = order[action-1]
			
				if thisround["atype"] == "Normal":
					await ctx.send("This is round {}, normal actions on initiative {}. It is the turn of {} to act.".format(round, thisround["init"], thisround["name"]))
				else:
					await ctx.send("This is round {}, Celerity action {} on initiative {}. Next to act is {}.".format(round, thisround["caction"], thisround["init"], thisround["name"]))
			
			
			# clear celerity on newround
			if newround:
				round += 1
				action = 0
				for member in members:
					mydb.clear_linear_setting(member.id, "CelerityActions", server)
					mydb.clear_linear_setting(member.id, "Potence", server)
					mydb.clear_linear_setting(member.id, "Fortitude", server)
					
				#await ctx.send("New round. Reset action to {}, increment  round to {}, clear celerity actions.".format(action, round))
			else:
				action += 1

			
			ok = mydb.save_linear_setting(botid, "CurrentAction", action, server)
			ok = mydb.save_linear_setting(botid, "Round", round, server)
			
		else:
			await ctx.send("Please accept my apologies. You must be in a voice channel to use this command.")
					

		mydb.disconnect()

		
	async def cog_command_error(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send("I'm sorry Master, I need more information. Can you tell me the {}?".format(error.param.name))
		else:
			print(error)

	def get_init_order(self, members, botid, server):
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()

		# what initiative does each member have?
		initdict = {}
		membernames = {}
		topinit = 0
		celerityinit = {}
		topcelerity = 0
		for member in members:
			if member.nick is None:
				cname = member.name
			else:
				cname = member.nick
			membernames[member.id] = cname
			
			init = mydb.get_linear_setting(member.id, "Initiative", 1, server)
			if init > topinit:
				topinit = init
			initdict[member.id] = init
			
			celerity = mydb.get_linear_setting(member.id, "CelerityActions", 0, server)
			if celerity > topcelerity:
				topcelerity = celerity
			celerityinit[member.id] = celerity
		
		#print("Top initiative = {}".format(topinit))
		#print("Top celerity = {}".format(topcelerity))
		mydb.save_linear_setting(botid, "TopInitiative", topinit, server)
		mydb.save_linear_setting(botid, "TopCelerity", topcelerity, server)
		
		result = []
		
		# Normal Actions
		if topinit > 0:
			for i in range(topinit, 0, -1):
				match = 0
				for nameid in initdict.keys():
					if initdict[nameid] == i:
						result.append({
							"nameid": nameid,
							"name": membernames[nameid],
							"atype": "Normal",
							"init": i,
							"caction": 0
						});
						#print("Normal Action: Initiative {}. Action for {}.".format(i, membernames[nameid]))

			# Celerity Actions
			if topcelerity > 0:
				for i in range(1, topcelerity+1, 1):
					for j in range(topinit, 0, -1):
						for nameid in initdict.keys():
							if initdict[nameid] == j and celerityinit[nameid] >= i:
								result.append({
									"nameid": nameid,
									"name": membernames[nameid],
									"atype": "Celerity",
									"init": j,
									"caction": i
								});
								#print("Celerity Action {}: Initiative {}. Action for {}.".format(i, j, membernames[nameid]))
		
		return result

def setup(bot):
	bot.add_cog(Linears(bot))
