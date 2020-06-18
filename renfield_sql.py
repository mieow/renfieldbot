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