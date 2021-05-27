import mysql.connector
import os

from dotenv import load_dotenv

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
	