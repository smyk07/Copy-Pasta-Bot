import do_not_push
import constants
import re
import asyncio
from typing import Optional, Union, Callable
import discord
import os
from sqlitedict import SqliteDict
from cmds import *
import sys
from datetime import datetime, timedelta, timezone

import subprocess
from DatabaseManager import DatabaseManager
from Message import Message

sys.path.append(os.path.basename(__file__))

def is_admin(user_id:int):
	return user_id in do_not_push.ADMINS

class CommandHandler:
	def __init__(self, db_manager: DatabaseManager, get_bot: Callable):
		self.db = db_manager

		self.commands = {
			'help': lambda message: help.help(message.args),
			
			# Copypasta
			'add': lambda message: add.add(message, self.db, overwrite=False),
			'add_o': lambda message: add.add(message, self.db, overwrite=True),
			'saved': self._handle_saved,
			'delete': lambda message: delete.delete(message, self.db),
			'delete_me': lambda message: delete_me.delete_me(self.db, message.author.id),
			'rename': lambda message: rename_key.handle_rename(message, self.db, overwrite=False),
			'rename_o': lambda message: rename_key.handle_rename(message, self.db, overwrite=True),
			'steal': lambda message: steal.handle_steal(self.db, message.author, message.args),
			'random': lambda message: random_key.handle_random(message.author, message.args),
			'search': lambda message: search.handle_search(self.db, message.author, message.args),
			
			# Text transform
			'clap': lambda message: text_transform.handle_text_transform('clap', message),
			'zalgo': lambda message: text_transform.handle_text_transform('zalgo', message),
			'forbesify': lambda message: text_transform.handle_text_transform('forbesify', message),
			'copypasta': lambda message: text_transform.handle_text_transform('copypasta', message),
			'owo': lambda message: text_transform.handle_text_transform('owo', message),
			'uwu': lambda message: text_transform.handle_text_transform('owo', message), # Alias
			'stretch': lambda message: text_transform.handle_text_transform('stretch', message),
			
			# Fun
			'mock': mock.handle_mock,
			'roast': lambda message: roast.roast(message.message_obj, self.get_bot()),
			'roast_add': lambda message: roast.add_roast(message),

			# TODO
			'deepfry': lambda message: deepfry.handle_deepfry_command(message.reference),
			# 'dream': lambda message: self._handle_dream(message.author, message.args, message.reference),
			'dream': lambda message: dream.handle_dream_command(message.reference),

			# Admin
			'blacklist': lambda message: blacklist.handle_blacklist(message.author.id, message.args),
		}
		self.get_bot = get_bot

	def _handle_saved(self, message: 'Message') -> str:
		args = message.args
		if len(args) == 2 and args[1].startswith('<@') and args[1].endswith('>'):
			if not is_admin(message.author.id):
				return "You don't have permission to view another user's keys."
			find_keys_for = args[1][2:-1]
			# keys = sorted(self.db.get_user_keys(mentioned_user_id))
			# return f"Keys for <@{mentioned_user_id}>:\n- " + '\n- '.join(keys) if keys else constants.EMPTY_LIST
		else:
			find_keys_for = message.author.id

		keys = sorted(self.db.get_user_keys(find_keys_for))
		if len(keys) == 0:
			return constants.EMPTY_LIST
		
		return_text = f'{constants.SAVED_MSGS} <@{str(find_keys_for)}>\n' +\
							'- ' + '\n- '.join(keys) if keys else constants.EMPTY_LIST

		message_obj = message.message_obj
		if isinstance(message_obj.channel, discord.TextChannel) or isinstance(message_obj.channel, discord.VoiceChannel):
			if message_obj.channel.permissions_for(message_obj.channel.guild.me).add_reactions and \
						message_obj.channel.permissions_for(message_obj.channel.guild.me).manage_messages:
				return_text = f'{constants.SAVED_MSGS} <@{str(find_keys_for)}>\n1/{str(len(keys)//10 + 1)}\n' +\
								'- ' + '\n- '.join(keys[:10]) if keys else constants.EMPTY_LIST

		return return_text

	# async def _handle_deepfry(self, user: discord.User, args: list, reply) -> Union[str, discord.File]:
	# 	if reply is None:
	# 		return "You need to reply to a message with an image to use this command."
	# 	return await deepfry.handle_deepfry_command(reply)

	def _handle_text_transform(self, command_type: str) -> Callable:
		handlers = {
			'clap': clap.handle_clap_command,
			'zalgo': zalgo.handle_zalgo_command,
			'forbesify': forbesify.handle_forbesify_command,
			'copypasta': copypasta.handle_copypasta_command,
			'owo': owo.handle_owo_command,
			'stretch': stretch.handle_stretch_command
		}

		def handler(user: discord.User, args: list, reply, message=None) -> str:
			if reply is None:
				return "You need to reply to a message to use this command."
			return handlers[command_type](reply)

		return handler

	def _handle_delete(self, user: discord.User, args: list, reply) -> str:
		if len(args) == 1:
			return constants.WRONG_ARGS_DEL
		return constants.SUCCESSFUL if self.db.delete_key(user.id, args[1]) else constants.KEY_NOT_FOUND

	def _handle_delete_me(self, user: discord.User, args: list, reply) -> str:
		return constants.SUCCESSFUL if delete_me.delete_me(self.db.db, user.id) else constants.EMPTY_LIST

	def _handle_rename(self, user: discord.User, args: list, overwrite: bool) -> str:
		if len(args) != 3:
			return constants.WRONG_ARGS_DEL
		status = rename_key.rename_key(self.db.db, user.id, args[1], args[2], overwrite)
		match status:
			case 0: return constants.SUCCESSFUL
			case -1: return constants.EMPTY_LIST
			case -2: return constants.KEY_NOT_FOUND
			case -3: return constants.KEY_EXISTS_RENAME if not overwrite else constants.UNSUCCESSFUL
			case _: return constants.UNSUCCESSFUL

	def _handle_mock(self, user: discord.User, args: list, reply) -> Union[str, discord.File]:
		if reply is None:
			return "You need to reply to a message to use this command."
		return mock.handle_mock_command(reply)
	
	def _handle_flirt(self, user: discord.User, args: list, reply, message) -> str:
		from cmds import flirt
		if len(message.mentions) == 0:
			return "You need to mention someone to flirt with! Try ;;flirt @username"
		return flirt.handle_flirt_command(message)

	async def _handle_deepfry(self, user: discord.User, args: list, reply) -> Union[str, discord.File]:
		if reply is None:
			return "You need to reply to a message with an image to use this command."
		return await deepfry.handle_deepfry_command(reply)

	async def _handle_dream(self, user: discord.User, args: list, reply) -> Union[str, discord.File, None]:
		return await dream.handle_dream_command(user, args, message=reply)

	def _handle_steal(self, user: discord.User, args: list, reply) -> str:
		if len(args) == 2 and '<@' in args[1]:
			return constants.WRONG_ARGS_STEAL
		elif len(args) not in {3, 4}:
			return constants.WRONG_ARGS

		steal_from = args[1]
		if not steal_from.startswith('<@') or not steal_from.endswith('>'):
			return constants.WRONG_USER_ID

		steal_from = steal_from[2:-1]
		new_key = args[3] if len(args) == 4 else None
		return steal.steal(self.db.db, user.id, args[2], steal_from, new_key)

	def _handle_blacklist_add(self, user: discord.User, args: list, reply) -> str:
		if not is_admin(user.id):
			return "You don't have permission to use this command."
		if len(args) != 2 or not args[1].startswith('<@') or not args[1].endswith('>'):
			return "Invalid user mention"
		user_id_to_blacklist = int(args[1][2:-1])
		if user_id_to_blacklist in do_not_push.ADMINS:
			return "You cannot blacklist another admin."
		if user_id_to_blacklist in constants.BLACKLIST:
			return "User is already blacklisted."
		constants.BLACKLIST.append(user_id_to_blacklist)
		return f"User <@{user_id_to_blacklist}> has been blacklisted."

	def _handle_blacklist_remove(self, user: discord.User, args: list, reply) -> str:
		if not is_admin(user.id):
			return "You don't have permission to use this command."
		if len(args) != 2 or not args[1].startswith('<@') or not args[1].endswith('>'):
			return "Invalid user mention"
		user_id_to_remove = int(args[1][2:-1])
		if user_id_to_remove not in constants.BLACKLIST:
			return "User is not blacklisted."
		constants.BLACKLIST.remove(user_id_to_remove)
		return f"User <@{user_id_to_remove}> has been removed from the blacklist."

	def _handle_random(self, user: discord.User, args:list) -> str:
		if len(args) != 1 and len(args) != 2:
			return constants.WRONG_ARGS
		
		search_term = args[1] if len(args) == 2 else None
		return random_key.random_key(self.db.db, user.id, search_term)

	def _handle_search(self, user: discord.User, args: list) -> str:
		if len(args) != 2:
			return constants.WRONG_ARGS
		return search.search(self.db.db, user.id, args[1])

	# async def _handle_dream(self, user: discord.User, args: list, reply) -> Union[str, discord.File, None]:
	# 	return await dream.handle_dream_command(user, args, message=reply)

	async def handle_command(self, message: Message) -> Optional[Union[str, discord.File]]:
		args = message.args
		if not args:
			return None

		command = args[0]
		if command in self.commands:
			if command in constants.ADMIN_COMMANDS:
				if not is_admin(message.author.id):
					return constants.ADMIN_ONLY
				return self.commands[command](message)

			if command in ['dream', 'deepfry']:
				return await self.commands[command](message)
			else:
				return self.commands[command](message)
		return None


class DiscordBot:
	def __init__(self, token: str):
		self.token = token
		intents = discord.Intents.default()
		intents.message_content = True
		self.client = discord.Client(intents=intents)
		self.db_manager = DatabaseManager(constants.DB_NAME)
		self.command_handler = CommandHandler(self.db_manager, self._get_user)
		self.setup_events()

	def _get_user(self):
		return self.client.user
	
	async def update_status(self):
		while True:
			try:
				total_users = sum(guild.member_count for guild in self.client.guilds)
				total_servers = len(self.client.guilds)
				status = f'Serving {total_users}+ users in {total_servers} servers'
				await self.client.change_presence(activity=discord.Activity(
					type=discord.ActivityType.custom,
					name=status,
					state=status
				))
			except Exception as e:
				print(f"Error updating status: {e}", file=sys.stderr)
			await asyncio.sleep(86400)

	def setup_events(self):
		@self.client.event
		async def on_ready():
			print(f'Logged in as {self.client.user}')
			asyncio.create_task(self.update_status())

		@self.client.event
		async def on_message(message: discord.Message):
			if message.author == self.client.user or message.author.bot:
				return

			if not blacklist.is_blacklisted(message.author.id):
				return constants.BLACKLISTED
			
			mess = Message(message)
			await self.process_message(mess)
		
		@self.client.event
		async def on_reaction_add(reaction, user:discord.User):
			if user == self.client.user:
				return

			message = reaction.message

			if not message.channel.permissions_for(message.channel.guild.me).manage_messages or \
				not message.channel.permissions_for(message.channel.guild.me).add_reactions:
				return

			if message.author != self.client.user:
				return

			if message.created_at < datetime.now(timezone.utc) - timedelta(minutes=5):
				return

			if not message.content.strip().startswith(constants.SAVED_MSGS):
				return

			# Message format:
			# Saved messages for: <@userid>
			# Pageno/total
			# <content>

			message_lines = message.content.strip().split('\n')
			numbers = re.findall(r'\d+', message_lines[0]) # Should only contain 1 element
			if len(numbers) != 1:
				print('Error updating saved message: Can\'t find author id in: ', message_lines[0], file=sys.stderr)
				return

			author = numbers[0]
			if author != str(user.id):
				await reaction.remove(user)
				return
			try:
				page_no = int(message_lines[1].split('/')[0]) - 1
			except ValueError:
				print('Error updating saved message: Can\'t find page no in: ', message_lines[1], file=sys.stderr)
				return
			except Exception as e:
				print('Error updating saved message: Unknown error lmao ' + str(e) , file=sys.stderr)
				return

			user_saved = sorted(self.db_manager.get_user_keys(author))
			pages = [user_saved[i:i+10] for i in range(0, len(user_saved), 10)]

			match reaction.emoji:
				case '▶️':
					new_page = page_no + 1
					if len(pages) <= new_page:
						await reaction.remove(user)
						return
					else:
						new_content = f'{constants.SAVED_MSGS} <@{author}>\n' +\
										f'{str(new_page+1)}/{str(len(pages))}\n' +\
										'- ' + '\n- '.join(pages[new_page])
						await message.edit(content=new_content)

				case '⏭️':
					new_content = f'{constants.SAVED_MSGS} <@{author}>\n' +\
									f'{str(len(pages))}/{str(len(pages))}\n' +\
									'- ' + '\n- '.join(pages[-1])
					await message.edit(content=new_content)

				case '◀️':
					new_page = page_no - 1
					if 0 > new_page:
						await reaction.remove(user)
						return
					else:
						new_content = f'{constants.SAVED_MSGS} <@{author}>\n' +\
										f'{str(new_page+1)}/{str(len(pages))}\n' +\
										'- ' + '\n- '.join(pages[new_page])
						await message.edit(content=new_content)

				case '⏮️':
					new_content = f'{constants.SAVED_MSGS} <@{author}>\n' +\
									f'0/{str(len(pages))}\n' +\
									'- ' + '\n- '.join(pages[0])
					await message.edit(content=new_content)

				case _:
					await reaction.remove(user)
					return

			try:
				# await message.clear_reactions()
				# await message.add_reaction('⏮️')
				# await message.add_reaction('◀️')
				# await message.add_reaction('▶️')
				# await message.add_reaction('⏭️')
				await reaction.remove(user)
			except discord.HTTPException:
				print('Error removing reactions', file=sys.stderr)
			except discord.Forbidden:
				print('This shouldn\'t happen :)', file=sys.stderr)
			except Exception as e:
				print(e, file=sys.stderr)



	async def process_message(self, message: 'Message'):
		content = message.content
		if re.search(constants.REPLACE, content):
			await self.handle_replacement(message)
		elif re.match(constants.COMMAND, content):
			await self.handle_bot_command(message)

	async def handle_replacement(self, message: 'Message'):
		def get_text(match:re.Match)->str:
			key = match.string[match.start()+2:match.end()-2]
			replacement = self.db_manager.retrieve_text(message.author.id, key)
			if replacement:
				return replacement
			return f';;{key};;'

		replaced_text = re.sub(constants.REPLACE,
				get_text,
				message.content).strip()
		if replaced_text != message.content and replaced_text != '':
			target = message.reference.resolved if message.reference else message.message_obj
			await target.reply(replaced_text)

	async def handle_bot_command(self, message: 'Message'):
		response = await self.command_handler.handle_command(message)

		if response:
			await self.send_response(message, response)

	async def send_response(self, message: 'Message', response):
		message_obj = message.message_obj
		cmd = message_obj.content.strip()[2:]
		reply_to = message.reference.resolved if message.reference and cmd.split()[0] in {
			'mock', 'deepfry', 'clap', 'zalgo', 'forbesify', 'copypasta', 'owo', 'stretch', 'random'
		} else message.message_obj

		if isinstance(response, discord.File):
			await reply_to.reply(file=response)
			if hasattr(response.fp, 'name'):
				os.remove(response.fp.name)
		elif isinstance(response, str):
			if len(response) > 2000:
				# Always reply to the command message for error responses
				await message.reply("## Fuck me! Keep it under the 2k character limit of Discord.")
			else:
				resp = await reply_to.reply(response)
				if cmd == 'saved':
					if response.strip().startswith(constants.SAVED_MSGS):
						message_obj = message.message_obj
						if isinstance(message_obj.channel, discord.TextChannel) or isinstance(message_obj.channel, discord.VoiceChannel):
							if message_obj.channel.permissions_for(message_obj.channel.guild.me).add_reactions and \
								message_obj.channel.permissions_for(message_obj.channel.guild.me).manage_messages:
								await resp.add_reaction('⏮️')
								await resp.add_reaction('◀️')
								await resp.add_reaction('▶️')
								await resp.add_reaction('⏭️')
		else:
			print("Unhandled response type:", type(response))

	def run(self):
		try:
			self.client.run(self.token)
		except Exception as e:
			print(f"Error: {e}")
		finally:
			# To avoid another data loss due to DB file getting deleted while bot is running
			if not os.path.exists(constants.DB_NAME):
				os.makedirs(os.path.dirname(constants.DB_NAME))
				os.mknod(constants.DB_NAME)
				backup_db = self.db_manager.copy_database(SqliteDict(constants.DB_NAME + '.bkp', autocommit=True))
				backup_db.close()
			self.db_manager.close()

if __name__ == '__main__':
	bot = DiscordBot(do_not_push.API_TOKEN)
	bot.run()