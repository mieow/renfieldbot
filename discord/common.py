import os
import traceback
from cryptography.fernet import Fernet
from discord.ext import commands
from discord import app_commands


# function to create & write encryption key
def write_key():
	if os.path.isfile("/home/renfield/.wp_key"):
		return "using existing key"
	else:
		key = Fernet.generate_key()
		with open("/home/renfield/.wp_key", "wb") as key_file:
			key_file.write(key)
		return "new key generated"
 
# function to read encryption key
def load_key():
	"""
	Loads the key named `secret.key` from the current directory.
	"""
	return open("/home/renfield/.wp_key", "rb").read()
	
# function to encode string
def str_encode(message):
	key = load_key()
	fernet = Fernet(key)
	return fernet.encrypt(message.encode())

# function to decode string
def str_decode(encMessage):
	key = load_key()
	fernet = Fernet(key)
	return fernet.decrypt(encMessage).decode()




