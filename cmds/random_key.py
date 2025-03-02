from sqlitedict import SqliteDict
import constants
import random

def random_key(db: SqliteDict, user: str) -> str:
	user_db = db.get(user, None)

	if user_db is None:
		return constants.EMPTY_LIST
	
	return user_db[random.choice(list(user_db.keys()))]