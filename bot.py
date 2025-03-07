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

sys.path.append(os.path.basename(__file__))

def is_admin(user_id: int) -> bool:
	return user_id in do_not_push.ADMINS

def is_blacklisted(user_id: int) -> bool:
	return user_id in constants.BLACKLIST
class DatabaseManager:
	def __init__(self, db_name: str):
		self.db = SqliteDict(db_name, autocommit=True)

	def store_text(self, user: str, key: str, value: str, overwrite=False) -> str:
		user_db = self.db.get(user, {})
		if key in user_db and not overwrite:
			return constants.KEY_EXISTS_ADD
		user_db[key] = value
		self.db[user] = user_db
		return constants.SUCCESSFUL

	def retrieve_text(self, user: str, key: str) -> Optional[str]:
		return self.db.get(user, {}).get(key)

	def get_user_keys(self, user: str) -> list:
		return list(self.db.get(user, {}).keys())

	def close(self):
		self.db.close()

	def delete_key(self, user: str, key: str) -> bool:
		user_db = self.db.get(user, {})
		if key in user_db:
			del user_db[key]
			self.db[user] = user_db
			return True
		return False

	def copy_database(self, new_db:SqliteDict):
		for key in self.db.keys():
			new_db[key] = self.db[key]

		return new_db

class CommandHandler:
	def __init__(self, db_manager: DatabaseManager):
		self.db = db_manager
		self.commands = {
			'add': lambda u, a, r, m: self._handle_add(u, a, r),
			'add_o': lambda u, a, r, m: self._handle_add(u, a, r, True),
			'saved': lambda u, a, r, m: self._handle_saved(u, a, m),
			'delete': lambda u, a, r, m: self._handle_delete(u, a, r),
			'delete_me': lambda u, a, r, m: self._handle_delete_me(u, a, r),
			'rename': lambda u, a, r, m: self._handle_rename(u, a, False),
			'rename_o': lambda u, a, r, m: self._handle_rename(u, a, True),
			'mock': lambda u, a, r, m: self._handle_mock(u, a, r),
			'steal': lambda u, a, r, m: self._handle_steal(u, a, r),
			'help': lambda u, a, r, m: constants.HELP_TEXT,
			'blacklist_add': lambda u, a, r, m: self._handle_blacklist_add(u, a, r),
			'blacklist_remove': lambda u, a, r, m: self._handle_blacklist_remove(u, a, r),
			'clap': self._handle_text_transform('clap'),
			'zalgo': self._handle_text_transform('zalgo'),
			'forbesify': self._handle_text_transform('forbesify'),
			'copypasta': self._handle_text_transform('copypasta'),
			'owo': self._handle_text_transform('owo'),
			'stretch': self._handle_text_transform('stretch'),
			'random': lambda u, a, r, m: self._handle_random(u),
			'search': lambda u, a, r, m: self._handle_search(u, a),

			'deepfry': lambda u, a, r, m: self._handle_deepfry(u, a, r),
			'dream': lambda u, a, r, m: self._handle_dream(u, a, r)
		}

	def _handle_add(self, user: discord.User, args: list, reply, overwrite=False) -> str:
		if len(args) == 1 or (len(args) == 2 and reply is None):
			return constants.WRONG_ARGS_ADD

		if len(args) == 2:
			if reply is None:
				return constants.WRONG_ARGS_ADD

			original_message = reply.resolved.content.strip() or ''
			original_message += self._get_attachments_text(reply.resolved)

			if not original_message:
				return constants.EMPTY_MESSAGE

			return self.db.store_text(user.id, args[1], original_message, overwrite)

		return self.db.store_text(user.id, args[1], ' '.join(args[2:]), overwrite)

	def _get_attachments_text(self, message: discord.Message) -> str:
		text = ''
		for i, attachment in enumerate(message.attachments):
			text += f'[Attachment {i}]({attachment.url}) '
		for sticker in message.stickers:
			text += f'[{sticker.name}]({sticker.url}) '
		return text

	def _handle_saved(self, user: discord.User, args: list, message=None) -> str:
		if len(args) == 2 and args[1].startswith('<@') and args[1].endswith('>'):
			if not is_admin(user.id):
				return "You don't have permission to view another user's keys."
			find_keys_for = args[1][2:-1]
			# keys = sorted(self.db.get_user_keys(mentioned_user_id))
			# return f"Keys for <@{mentioned_user_id}>:\n- " + '\n- '.join(keys) if keys else constants.EMPTY_LIST
		else:
			find_keys_for = user.id

		keys = sorted(self.db.get_user_keys(find_keys_for))
		if len(keys) == 0:
			return constants.EMPTY_LIST
		
		return_text = f'{constants.SAVED_MSGS} <@{str(find_keys_for)}>\n' +\
							'- ' + '\n- '.join(keys) if keys else constants.EMPTY_LIST

		if isinstance(message.channel, discord.TextChannel) or isinstance(message.channel, discord.VoiceChannel):
			if message.channel.permissions_for(message.channel.guild.me).add_reactions and \
						message.channel.permissions_for(message.channel.guild.me).manage_messages:
				return_text = f'{constants.SAVED_MSGS} <@{str(find_keys_for)}>\n1/{str(len(keys)//10 + 1)}\n' +\
								'- ' + '\n- '.join(keys[:10]) if keys else constants.EMPTY_LIST

		return return_text

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
		status = rename_key.rename_key(self.db.db, user.id, args[1], args[2])
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

	async def _handle_deepfry(self, user: discord.User, args: list, reply) -> Union[str, discord.File]:
		if reply is None:
			return "You need to reply to a message with an image to use this command."
		return await deepfry.handle_deepfry_command(reply)

	async def _handle_dream(self, user: discord.User, args: list, reply) -> Union[str, discord.File, None]:
		return await dream.handle_dream_command(user, args, message=reply)

	def _handle_steal(self, user: discord.User, args: list, reply) -> str:
		if len(args) not in {3, 4}:
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

	def _handle_random(self, user: discord.User) -> str:
		return random_key.random_key(self.db.db, user.id)

	def _handle_search(self, user: discord.User, args: list) -> str:
		if len(args) != 2:
			return constants.WRONG_ARGS
		return search.search(self.db.db, user.id, args[1])

	async def handle_command(self, user: discord.User, cmd: str, reply=None, message=None) -> Optional[Union[str, discord.File]]:
		if cmd.startswith(';;'):
			cmd = cmd[2:]

		args = cmd.split()
		if not args:
			return None

		command = args[0]
		if command in self.commands:
			if command in ['dream', 'deepfry']:
				return await self.commands[command](user, args, reply, message)
			else:
				return self.commands[command](user, args, reply, message)
		return None

class DiscordBot:
	def __init__(self, token: str):
		self.token = token
		intents = discord.Intents.default()
		intents.message_content = True
		self.client = discord.Client(intents=intents)
		self.db_manager = DatabaseManager(constants.DB_NAME)
		self.command_handler = CommandHandler(self.db_manager)
		self.setup_events()

	def setup_events(self):
		@self.client.event
		async def on_ready():
			print(f'Logged in as {self.client.user}')

		@self.client.event
		async def on_message(message: discord.Message):
			if message.author == self.client.user or message.author.bot:
				return

			if is_blacklisted(message.author.id):
				if message.content.strip().startswith(';;'):
					await message.reply("You are blacklisted from using this bot.")
				return

			await self.process_message(message)
		
		@self.client.event
		async def on_reaction_add(reaction, user:discord.User):
			if user == self.client.user:
				return

			message = reaction.message

			if not message.channel.permissions_for(message.channel.guild.me).manage_messages or \
				not message.channel.permissions_for(message.channel.guild.me).add_reactions:
				return

			if message.author != self.client.user:
				await reaction.remove(user)
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



	async def process_message(self, message: discord.Message):
		content = message.content.strip()
		if re.match(constants.REPLACE, content):
			await self.handle_replacement(message)
		elif re.match(constants.COMMAND, content):
			await self.handle_bot_command(message)

	async def handle_replacement(self, message: discord.Message):
		parts = message.content.strip().split(';;')
		replaced_text = self.db_manager.retrieve_text(message.author.id, parts[1])
		if replaced_text:
			target = message.reference.resolved if message.reference else message
			await target.reply(replaced_text)

	async def handle_bot_command(self, message: discord.Message):
		response = await self.command_handler.handle_command(
			message.author, 
			message.content.strip(), 
			reply=message.reference,
			message=message
		)

		if response:
			await self.send_response(message, response)

	async def send_response(self, message: discord.Message, response):
		cmd = message.content.strip()[2:]
		reply_to = message.reference.resolved if message.reference and cmd.split()[0] in {
			'mock', 'deepfry', 'clap', 'zalgo', 'forbesify', 'copypasta', 'owo', 'stretch', 'random'
		} else message

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
					if isinstance(message.channel, discord.TextChannel) or isinstance(message.channel, discord.VoiceChannel):
						if message.channel.permissions_for(message.channel.guild.me).add_reactions and \
							message.channel.permissions_for(message.channel.guild.me).manage_messages:
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
				backup_db = self.db_manager.copy_database(SqliteDict(constants.DB_NAME + '.bkp', autocommit=True))
				backup_db.close()
			self.db_manager.close()

if __name__ == '__main__':
	bot = DiscordBot(do_not_push.API_TOKEN)
	bot.run()