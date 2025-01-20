import os
import traceback
from cryptography.fernet import Fernet
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv


load_dotenv()
key_loc = os.getenv("KEY_FILE_LOCATION") + "/.wp_key"

# function to create & write encryption key
def write_key():
    try:
        if os.path.isfile(key_loc):
            print("Existing Key")
            return "using existing key"
        else:
            print("New Key")
            key = Fernet.generate_key()
            with open(key_loc, "wb") as key_file:
                key_file.write(key)
                return "new key generated"
    except Exception as e:
        print(e)
 
# function to read encryption key
def load_key():
	"""
	Loads the key named `secret.key` from the current directory.
	"""
	write_key()
	return open(key_loc, "rb").read()
	
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




