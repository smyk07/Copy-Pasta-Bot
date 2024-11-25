from sqlitedict import SqliteDict

def rename_key(db:SqliteDict, user:str, key:str, new_key:str, overwrite:bool)->int:
	user_db = db.get(user, None)
	if not user_db:
		return -1
	
	value = user_db.get(key, None)
	if not value:
		return -2
	
	if user_db.get(new_key, None) and not overwrite:
		return -3

	user_db[new_key] = value
	del user_db[key]

	db[user] = user_db

	return 0
	