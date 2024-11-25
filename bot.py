import api_token
import constants
import re
import discord
from sqlitedict import SqliteDict
from cmds import *

RE_CMD = re.compile(constants.COMMAND)
RE_REPLACE = re.compile(constants.REPLACE)

def initialize_db():
	return SqliteDict(constants.DB_NAME, autocommit=True)

def store_text(db:SqliteDict, user:str, key:str, value:str, overwrite=False)->str:
	user_db = db.get(user, None) or {}

	val = user_db.get(key, None) # Apparently faster than `in` or `try...except`?
	if val is not None:
		if not overwrite:
			return constants.KEY_EXISTS_ADD
	
	user_db[key] = value
	db[user] = user_db

def retrieve_text(db:SqliteDict, user:str, key:str)->str:
	user_db = db.get(user, None)
	if user_db is not None:
		return user_db.get(key, None)
	return None

def add(db:SqliteDict, user:str, args:list, reply, overwrite:bool)->str:
	if len(args) == 1:
		return_text = constants.WRONG_ARGS_ADD
	
	elif len(args) == 2:
		if reply is None:
			return_text = constants.WRONG_ARGS_ADD
		else:
			original_message = reply.resolved.content.strip() or ''

			# Multiple attachments ???
			# if len(reply.resolved.attachments) > 0:
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

def replace_text(db:SqliteDict, user:str, message:str)->str:
	parts = message.split(';;')
	
	parts[1] = retrieve_text(db, user.id, parts[1])

	if parts[1] is None:
		return
	
	return ' '.join(parts)

def handle_command(db:SqliteDict, user:str, cmd:str, reply=None)->str:
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
			user_db = db.get(user.id, None)
			if user_db is None:
				return_text = constants.EMPTY_LIST
			else:
				#TODO: Figure out pagination
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

		
		case 'help':
			return_text = constants.HELP_TEXT

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
	async def on_message(message:discord.Message):
		if message.author == client.user:
			return

		message_text = message.content.strip()
		if RE_REPLACE.match(message_text):
			replaced_text = replace_text(db, message.author, message_text)
			if replaced_text is not None:
				if message.reference is not None:
					await message.reference.resolved.reply(replaced_text)
				else:
					await message.reply(replaced_text)

		elif RE_CMD.match(message_text):
			reply_text = handle_command(db, message.author, message_text, reply=message.reference)
			if reply_text is not None:
				await message.reply(reply_text)

	try:
		client.run(api_token.API_TOKEN)
	except:
		pass
		#TODO add logging
	finally:
		db.close()