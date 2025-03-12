import os
import random
import discord

def get_asset_path(filename: str) -> str:
	root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	return os.path.join(root_dir, 'assets', filename)

def load_roasts() -> list:
	"""Load roasts from the roasts.txt file"""
	try:
		with open(get_asset_path('roasts.txt'), 'r', encoding='utf-8') as file:
			# Filter out empty lines
			roasts = [line.strip() for line in file if line.strip()]
		return roasts
	except FileNotFoundError:
		print("Error: roasts.txt file not found in assets directory")
		return ["Error: Couldn't find roasts file. Contact the bot owner."]
	except Exception as e:
		print(f"Error loading roasts: {e}")
		return ["Error: Couldn't load roasts. Contact the bot owner."]

def get_random_roast() -> str:
	"""Get a random roast from the roasts file"""
	roasts = load_roasts()
	return random.choice(roasts)

def handle_roast_command(message: discord.Message) -> str:
	"""Handle the ;;roast command and return the response message"""
	
	# Check if there's a user mention in the message
	if not message.mentions:
		return "You need to mention someone to roast! Try ;;roast @username"
	
	# Get the first mentioned user
	target_user = message.mentions[0]
	
	# Get a random roast
	roast = get_random_roast()
	
	# Format the response with the target user mention and the roast
	# Using discord.utils.escape_markdown to preserve '*' for censoring 
	response = f"{target_user.mention} {discord.utils.escape_markdown(roast)}"
	
	return response