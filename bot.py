import do_not_push
import constants
import re
import discord
import os
from sqlitedict import SqliteDict
from cmds import *
import sys

# Jugaad to import constants in cmds
sys.path.append(os.path.basename(__file__))

RE_CMD = re.compile(constants.COMMAND)
RE_REPLACE = re.compile(constants.REPLACE)

def initialize_db():
	return SqliteDict(constants.DB_NAME, autocommit=True)

def store_text(db: SqliteDict, user: str, key: str, value: str, overwrite=False) -> str:
	user_db = db.get(user, None) or {}

	val = user_db.get(key, None)  # Apparently faster than `in` or `try...except`?
	if val is not None:
		if not overwrite:
			return constants.KEY_EXISTS_ADD

	user_db[key] = value
	db[user] = user_db

def retrieve_text(db: SqliteDict, user: str, key: str) -> str:
	user_db = db.get(user, None)
	if user_db is not None:
		return user_db.get(key, None)
	return None

def add(db: SqliteDict, user: str, args: list, reply, overwrite: bool) -> str:
	if len(args) == 1:
		return_text = constants.WRONG_ARGS_ADD
	
	elif len(args) == 2:
		if reply is None:
			return_text = constants.WRONG_ARGS_ADD
		else:
			original_message = reply.resolved.content.strip() or ''

			# Multiple attachments
			for i in range(len(reply.resolved.attachments)):
				original_message += f'[Attachment {i}]({reply.resolved.attachments[i].url}) '

			for i in reply.resolved.stickers:
				original_message += f'[{i.name}]({i.url}) '

			if original_message != '':
				return_text = store_text(db, user.id, args[1], original_message, overwrite=overwrite)
			else:
				return_text = constants.EMPTY_MESSAGE
	
	else:
		return_text = store_text(db, user.id, args[1], ' '.join(args[2:]), overwrite=overwrite)
	
	return return_text

def replace_text(db: SqliteDict, user: str, message: str) -> str:
	parts = message.split(';;')
	
	parts[1] = retrieve_text(db, user.id, parts[1])

	if parts[1] is None:
		return
	
	return ' '.join(parts)

def is_admin(user_id: int) -> bool:
	"""Check if the user is an admin."""
	return user_id in do_not_push.ADMINS

def is_blacklisted(user_id: int) -> bool:
	"""Check if the user is blacklisted."""
	return user_id in constants.BLACKLIST

def handle_command(db: SqliteDict, user: discord.User, cmd: str, reply=None) -> str:
	if cmd[0] == ';':
		cmd = cmd[2:]
	
	args = cmd.split(' ')

	return_text = None
	match args[0]:
		case 'add':
			return_text = add(db, user, args, reply, overwrite=False) or constants.SUCCESSFUL

		case 'add_o':
			return_text = add(db, user, args, reply, overwrite=True) or constants.SUCCESSFUL

		case 'saved':
			if len(args) == 2 and args[1].startswith('<@') and args[1].endswith('>'):
				mentioned_user_id = int(args[1][2:-1])
				if not is_admin(user.id):
					return_text = "You don't have permission to view another user's keys."
				else:
					mentioned_user_db = db.get(mentioned_user_id, None)
					if mentioned_user_db is None:
						return_text = constants.EMPTY_LIST
					else:
						return_text = f"Keys for <@{mentioned_user_id}>:\n- " + '\n- '.join(
							list(mentioned_user_db.keys())
						)
			else:
				user_db = db.get(user.id, None)
				if user_db is None:
					return_text = constants.EMPTY_LIST
				else:
					return_text = '- ' + '\n- '.join(list(user_db.keys()))

		case 'delete':
			if len(args) == 1:
				return_text = constants.WRONG_ARGS_DEL
			else:
				# Maybe allow deleting multiple keys at a time?
				user_db = db.get(user.id, None)
				if user_db is None:
					return_text = constants.EMPTY_LIST
				else:
					deleted = user_db.pop(args[1], None)
					db[user.id] = user_db
					return_text = constants.SUCCESSFUL if deleted else constants.KEY_NOT_FOUND

		case 'delete_me':
			return_text = constants.SUCCESSFUL if delete_me.delete_me(db, user.id) else constants.EMPTY_LIST

		case 'rename':
			match rename_key.rename_key(db, user.id, args[1], args[2]):
				case 0:
					return_text = constants.SUCCESSFUL
				case -1:
					return_text = constants.EMPTY_LIST
				case -2:
					return_text = constants.KEY_NOT_FOUND
				case -3:
					return_text = constants.KEY_EXISTS_RENAME
				case _:
					return_text = constants.UNSUCCESSFUL
		
		case 'rename_o':
			match rename_key.rename_key(db, user.id, args[1], args[2]):
				case 0:
					return_text = constants.SUCCESSFUL
				case -1:
					return_text = constants.EMPTY_LIST
				case -2:
					return_text = constants.KEY_NOT_FOUND
				case -3:
					# Shouldn't occur
					return_text = constants.KEY_EXISTS_RENAME
				case _:
					return_text = constants.UNSUCCESSFUL

		case 'mock':
			if reply is None:
				return_text = "You need to reply to a message to use this command."
			else:
				return mock.handle_mock_command(reply)
		
		case 'steal':
			if len(args) not in {3, 4}:
				return constants.WRONG_ARGS

			new_key = args[3] if len(args) == 4 else None

			steal_from = args[1]
			if not steal_from.startswith('<@') or not steal_from.endswith('>'):
				return constants.WRONG_USER_ID

			steal_from = steal_from[2:-1]

			return steal.steal(db, user.id, args[2], steal_from, new_key)

		case 'help':
			return_text = constants.HELP_TEXT

		case 'blacklist_add':
			if not is_admin(user.id):
				return_text = "You don't have permission to use this command."
			elif len(args) == 2 and args[1].startswith('<@') and args[1].endswith('>'):
				user_id_to_blacklist = int(args[1][2:-1])
				if user_id_to_blacklist in do_not_push.ADMINS:
					return_text = "You cannot blacklist another admin."
				elif user_id_to_blacklist in constants.BLACKLIST:
					return_text = "User is already blacklisted."
				else:
					constants.BLACKLIST.append(user_id_to_blacklist)
					return_text = f"User <@{user_id_to_blacklist}> has been blacklisted."

		case 'blacklist_remove':
			if not is_admin(user.id):
				return_text = "You don't have permission to use this command."
			elif len(args) == 2 and args[1].startswith('<@') and args[1].endswith('>'):
				user_id_to_remove = int(args[1][2:-1])
				if user_id_to_remove not in constants.BLACKLIST:
					return_text = "User is not blacklisted."
				else:
					constants.BLACKLIST.remove(user_id_to_remove)
					return_text = f"User <@{user_id_to_remove}> has been removed from the blacklist."
		case 'clap':
			if reply is None:
				return_text = "You need to reply to a message to use this command."
			else:
				return_text = clap.handle_clap_command(reply)

	return return_text

if __name__ == '__main__':
	intents = discord.Intents.default()
	intents.message_content = True

	client = discord.Client(intents=intents)

	db = initialize_db()

	@client.event
	async def on_ready():
		print(f'Logged in as {client.user}')

	@client.event
	async def on_message(message: discord.Message):
		# Ignore messages from the bot itself
		if message.author == client.user:
			return

		# Ignore non-command messages from blacklisted users
		if is_blacklisted(message.author.id):
			if not message.content.strip().startswith(';;'):
				return
			else:
				await message.reply("You are blacklisted from using this bot.")
				return

		# Process command replacements
		message_text = message.content.strip()
		if RE_REPLACE.match(message_text):
			replaced_text = replace_text(db, message.author, message_text)
			if replaced_text is not None:
				if message.reference is not None:
					await message.reference.resolved.reply(replaced_text)
				else:
					await message.reply(replaced_text)

		# Process bot commands
		elif RE_CMD.match(message_text):
			response = handle_command(db, message.author, message_text, reply=message.reference)
			if response is not None:
				if isinstance(response, discord.File):
					# For mock command, reply to the original message instead of the command
					if message.content.strip()[2:].startswith('mock'):
						await message.reference.resolved.reply(file=response)
					else:
						await message.reply(file=response)
					# Clean up the temporary file
					os.remove(response.fp.name)
				else:
					if message.content.strip()[2:].startswith('clap'):
						await message.reference.resolved.reply(response)
					else:
						await message.reply(response)

	try:
		client.run(do_not_push.API_TOKEN)
	except Exception as e:
		print(f"Error: {e}")
	finally:
		db.close()