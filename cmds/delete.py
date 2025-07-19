import constants
import Message
import DatabaseManager

def delete(message: 'Message', db:DatabaseManager) -> str:
	if len(message.args) != 2:
		return constants.WRONG_ARGS_DEL
	return constants.SUCCESSFUL if db.delete_key(message.author.id, message.args[1]) else constants.KEY_NOT_FOUND