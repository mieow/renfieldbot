import mysql.connector
import os

from dotenv import load_dotenv
from common import str_encode, str_decode

load_dotenv()
DATABASE_USERNAME = os.getenv('DATABASE_USERNAME')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')

config = {
  'host' : "localhost",
  'user' : DATABASE_USERNAME,
  'passwd' : DATABASE_PASSWORD,
  'database' : "discordbot"
}
	
class renfield_sql():

	def connect(self):
		try:
			self.connection = mysql.connector.connect(**config)
			self.cursor = self.connection.cursor(buffered=True)
		except mysql.connector.Error as err:
			print("Something went wrong: {}".format(err))
		return self.cursor

	def disconnect(self):
		self.cursor.close()
		self.connection.close()

	def commit(self):
		self.connection.commit()

	def test(self):
		print(self.connection)
		return "This is a test"
		
	def save_linear_setting(self, nameid, setting_name, setting_level, server):
		mycursor = self.connect()
		ok = 1
		
		if setting_name == "":
			return 0
		
		count = 0
		try:
			sql = "select count(name) from linearsettings where name = %s and setting_name = %s and server = %s"
			val = ("{}".format(nameid), "{}".format(setting_name), server)
			mycursor.execute(sql, val)
			countall = mycursor.fetchall()
			count = countall[0][0]
		except Exception as e:
			ok = 0
			print('Count setting')
			print(e)
		
		if not ok:
			return 0
			
		if count == 0:
			# insert
			try:
				sql = "INSERT INTO linearsettings (name, setting_name, setting_level, server) VALUES (%s, %s, %s, %s)"
				val = (nameid, setting_name, setting_level, server)
				mycursor.execute(sql, val)
				self.commit()
			except Exception as e:
				ok = 0
				print('insert failed')
				print(e)
		
		else:
			# update
			try:
				sql = "UPDATE linearsettings SET setting_level = %s WHERE name = %s and setting_name = %s and server = %s"				
				val = (setting_level, nameid, setting_name, server)
				mycursor.execute(sql, val)
				self.commit()
			except Exception as e:
				ok = 0
				print('update failed')
				print(e)
	
		return ok

	def get_linear_setting(self, nameid, setting_name, default_level, server):
		mycursor = self.connect()
		ok = 1
		# get the current level of the setting
		try:
			sql = "select setting_level from linearsettings where name = %s and setting_name = %s and server = %s"
			val = ("{}".format(nameid), "{}".format(setting_name), server)
			mycursor.execute(sql, val)
			settings = mycursor.fetchall()
			if not settings:
				current = default_level
			else:
				current = settings[0][0]
		except Exception as e:
			ok = 0
			print(e)

		if ok:
			return current
		else:
			return default_level
	
	def clear_linear_setting(self, nameid, setting_name, server):
		mycursor = self.connect()
		ok = 1
		try:
			sql = "DELETE FROM `linearsettings` where setting_name = %s and name = %s and server = %s"
			val = ("{}".format(setting_name), "{}".format(nameid), server)
			mycursor.execute(sql, val)
			self.commit()
		except Exception as e:
			print(e)
			ok = 0
		return ok
		
	def save_bot_setting(self, setting_name, setting_value, server):
		mycursor = self.connect()
		ok = 1
		
		if setting_name == "":
			return 0
		
		count = 0
		try:
			sql = "select count(id) from serversettings where setting_name = %s and server = %s"
			val = ("{}".format(setting_name), server)
			mycursor.execute(sql, val)
			countall = mycursor.fetchall()
			count = countall[0][0]
		except Exception as e:
			ok = 0
			print('Count setting')
			print(e)
		
		if not ok:
			return 0
			
		if count == 0:
			# insert
			try:
				sql = "INSERT INTO serversettings (setting_name, setting_value, server) VALUES (%s, %s, %s)"
				val = (setting_name, setting_value, server)
				mycursor.execute(sql, val)
				self.commit()
			except Exception as e:
				ok = 0
				print('insert failed')
				print(e)
		
		else:
			# update
			try:
				sql = "UPDATE serversettings SET setting_value = %s WHERE setting_name = %s and server = %s"				
				val = (setting_value, setting_name, server)
				mycursor.execute(sql, val)
				self.commit()
			except Exception as e:
				ok = 0
				print('update failed')
				print(e)
	
		return ok

	def get_bot_setting(self, setting_name, default_value, server):
		mycursor = self.connect()
		ok = 1
		# get the current level of the setting
		try:
			sql = "select setting_value from serversettings where setting_name = %s and server = %s"
			val = ("{}".format(setting_name), server)
			mycursor.execute(sql, val)
			settings = mycursor.fetchall()
			if not settings:
				current = default_value
			else:
				current = settings[0][0]
		except Exception as e:
			ok = 0
			print(e)

		if ok:
			return current
		else:
			return default_value

	def get_nice(self, server):
		mycursor = self.connect()
		count = 0
		compliment = ""
		
		try:
			sql = "select count(id) from niceness where server = %s"
			val = (server,)
			mycursor.execute(sql, val)
			countall = mycursor.fetchall()
			count = countall[0][0]
			#await ctx.send('I have {} good ones for you, Master.'.format(count))
		except Exception as e:
			print(e)
			print(server)
			print (mycursor.statement)
			compliment = 'I\'m sorry, if I can\'t say anything nice then I won\'t say anything at all.'

		if count > 0:
			# or get their member_id from the the table
			try:
				sql = "select compliment from niceness where server = %s order by rand() limit 1"
				val = (server,)
				mycursor.execute(sql,val)
				results = mycursor.fetchall()
				compliment = results[0][0]
				compliment = '{}'.format(compliment)
			except Exception as e:
				print(e)
				compliment = 'I\'m sorry, Master, my mind has gone blank in your presence.'
		else:
			compliment = 'I\'m sorry, Master, I don\'t know what to say.'
		self.disconnect()
		
		return compliment

	# Add member
	def add_member(self, nameid, playername, server):
		result = {
			"status": 1,
			"member_id" : 0,
			"message" : ""
		}
		mycursor = self.connect()
				
		count = 0
		try:
			sql = "select count(member_id) from members where name = %s"
			val = ("{}".format(nameid), )
			mycursor.execute(sql, val)
			countall = mycursor.fetchall()
			count = countall[0][0]
			#result["message"] = 'Master, I have the members list.'
		except Exception as e:
			print(e)
			result["message"] = 'I\'m sorry, Master {}, I was unable to read the member list.'.format(nameid)
			result["status"] = 0
			return result
		
		member_id = 0
		if count == 0 and playername == "":
			result["message"] = 'I\'m sorry, Master, please let me know your Player name for the membership records'
			result["status"] = 0
		elif count == 0:
			#Add to member table
			try:
				sql = "INSERT INTO members (name, playername, wordpress_id) VALUES (%s, %s, %s)"
				val = (nameid, playername, "")
				mycursor.execute(sql, val)
				mydb.commit()
				member_id = mycursor.lastrowid
				result["member_id"] = member_id
				#result["message"] = 'Thank you, Master. I have added your name to the members list.'
			except Exception as e:
				print(e)
				result["message"] = 'I\'m sorry, Master, I was unable to add your name to the member list.'
				result["status"] = 0

		else:
			# or get their member_id from the the table
			try:
				sql = "select member_id from members where name = %s"
				val = ("{}".format(nameid), )
				mycursor.execute(sql, val)
				member_ids = mycursor.fetchall()
				member_id = member_ids[0][0]
				result["member_id"] = member_id
				#result["message"] = 'Thank you, Master. I have confirmed that you are a member with membership number {}.'.format(member_id)
			except Exception as e:
				print(e)
				result["message"] = 'I\'m sorry, Master, I was unable to find your membership number.'
				result["status"] = 0
		
			old_player = self.get_player_name(member_id, nameid)
		
			if playername != old_player and playername != "":
				try:
					mycursor = self.connect()
					sql = "UPDATE members SET playername = %s WHERE member_id = %s"				
					val = (playername, member_id)
					mycursor.execute(sql, val)
					self.commit()
					result["message"] = 'I had you listed here as {} but I suppose you can call yourself {} if you want, instead.'.format(old_player, playername)
				except Exception as e:
					print(e)
					result["message"] = 'I\'m sorry, Master, I was unable to update your membership with your player name.'
					result["status"] = 0
		
		return result

	def get_player_name(self, member_id, nameid):
		mycursor = self.connect()
		playername = ""
		# get the current level of the setting
		try:
			sql = "select playername from members where name = %s and member_id = %s"
			val = ("{}".format(nameid), "{}".format(member_id))
			mycursor.execute(sql, val)
			players = mycursor.fetchall()
			playername = players[0][0]
		except Exception as e:
			print(e)

		return playername

	def get_wordpress_id(self, nameid, server):
		mycursor = self.connect()
		wordpress_id = ""
		# get the current level of the setting
		try:
			sql = "select wordpress_id from wp_link where name = %s and server = %s"
			val = ("{}".format(nameid), "{}".format(server))
			mycursor.execute(sql, val)
			#print(mycursor.statement)
			ids = mycursor.fetchall()
			wordpress_id = ids[0][0]
		except Exception as e:
			print(e)

		return wordpress_id


	def save_link(self, nameid, wordpress_id, secret, server):
		mycursor = self.connect()
		ok = 1
		
		count = 0
		try:
			sql = "select count(name) from wp_link where name = %s and server = %s"
			val = ("{}".format(nameid), server)
			mycursor.execute(sql, (nameid, server))
			countall = mycursor.fetchall()
			count = countall[0][0]
		except Exception as e:
			ok = 0
			print('check existing wp_link failed')
			print(e)
		
		if not ok:
			return 0
		
		encSecret = str_encode(secret)
			
		if count == 0:
			# insert
			try:
				sql = "INSERT INTO wp_link (server, name, wordpress_id, secret) VALUES (%s, %s, %s, %s)"
				val = (server, nameid, wordpress_id, encSecret)
				mycursor.execute(sql, val)
				self.commit()
			except Exception as e:
				ok = 0
				print('insert to wp_link failed')
				print(e)
		
		else:
			# update
			try:
				sql = "UPDATE wp_link SET wordpress_id = %s, secret = %s WHERE name = %s and server = %s"				
				val = (wordpress_id, encSecret, nameid, server)
				mycursor.execute(sql, val)
				self.commit()
			except Exception as e:
				ok = 0
				print('update to wp_link failed')
				print(e)
	
		return ok

	def get_link(self, nameid, server):
		mycursor = self.connect()
		ok = 1
		info = {
			"wordpress_id" : "",
			"secret" : ""
		}
		# get the current level of the setting
		try:
			sql = "select wordpress_id, secret from wp_link where name = %s and server = %s"
			val = ("{}".format(nameid), server)
			mycursor.execute(sql, val)
			result = mycursor.fetchall()
			info["wordpress_id"] = result[0][0]
			info["secret"] =  str_decode(result[0][1])
			
		except Exception as e:
			ok = 0
			print(e)

		return info

	def update_event(self, beforename, aftername, starttime, server):
		mycursor = self.connect()

		ok = 0
		# update
		try:
			sql = "UPDATE events SET name = %s, eventdate = %s WHERE name = %s and server = %s"				
			val = (aftername, starttime, beforename, server)
			mycursor.execute(sql, val)
			self.commit()
			ok = 1
		except Exception as e:
			print('update to events failed')
			print(mycursor.statement)
			print(e)
	
		return ok	