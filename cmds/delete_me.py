import discord
from sqlitedict import SqliteDict

# Function to delete all of the user's saved data
def delete_me(db:SqliteDict, user:str)->None:
	db.pop(user, None)