from typing import Optional
from sqlitedict import SqliteDict
import constants
import traceback

class DatabaseManager:
	def __init__(self, db_name: str):
		self.db = SqliteDict(db_name, autocommit=True)

	def store_text(self, user_id: str, key: str, value: str, overwrite=False) -> str:
		user_db = self.db.get(user_id, {})
		if key in user_db and not overwrite:
			match traceback.extract_stack()[1].name: # function which called this
				case 'add':
					return constants.KEY_EXISTS_ADD

				case '_rename_key':
					return constants.KEY_EXISTS_RENAME

				case '_steal':
					return constants.KEY_EXISTS_STEAL

				case _:
					# unreachable?
					return constants.KEY_EXISTS

		user_db[key] = value
		self.db[user_id] = user_db
		return constants.SUCCESSFUL

	def retrieve_text(self, user_id: str, key: str) -> Optional[str]:
		return self.db.get(user_id, {}).get(key)

	def get_user_keys(self, user_id: str) -> list:
		return list(self.db.get(user_id, {}).keys())

	def close(self):
		self.db.close()

	def delete_key(self, user_id: str, key: str) -> bool:
		user_db = self.db.get(user_id, {})
		if key in user_db:
			del user_db[key]
			self.db[user_id] = user_db
			return True
		return False

	def copy_database(self, new_db:SqliteDict):
		'''
		Create a copy of the database
		'''
		for key in self.db.keys():
			new_db[key] = self.db[key]

		return new_db

	def delete_user(self, user_id:str) -> bool:
		try:
			self.db.pop(user_id)
			return True
		except Error as e:
			print(e)
			return False

	def get_users(self) -> list:
		return self.db.keys()
