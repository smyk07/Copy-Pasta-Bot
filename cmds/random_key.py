from sqlitedict import SqliteDict
import constants
import random

def random_key(db: SqliteDict, user: str, search_term:str=None) -> str:
	user_db = db.get(user, None)

	if user_db is None:
		return constants.EMPTY_LIST

	if search_term is not None:
		user_db = {key:user_db[key] for key in user_db.keys() if search_term in key}
	
	return user_db[random.choice(list(user_db.keys()))]