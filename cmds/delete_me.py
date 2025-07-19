# import discord
import DatabaseManager
import constants

# Function to delete all of the user's saved data
def delete_me(db:DatabaseManager, user:str)->None:
	# db.pop(user, None)
	return constants.SUCCESSFUL if db.delete_user(user) else constants.EMPTY_LIST