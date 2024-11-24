DB_NAME 		= './db/mysqlite.db'
KEY_EXISTS 		= 'Could not add because this key already exists. Use `add_o` to overwrite.'
KEY_NOT_FOUND	= 'Key you specified does not exist.'
SUCCESSFUL 		= 'Success!'
UNSUCCESSFUL 	= 'Something went wrong :/'
WRONG_ARGS_ADD	= '`add <key> <value>` or `add <key>` and reply to a message'
WRONG_ARGS_DEL	= '`delete <key>`'
EMPTY_LIST		= 'You have not saved any text yet.'
EMPTY_MESSAGE	= 'The message you replied to seems to be empty.'
HELP_TEXT		= '''
Start command with `;;`
- **add <key> <message>** : Add text to db
- **add_o <key> <message>** : Add text but overwrite if exists
- **help** : This message
- **saved** : See all saved texts
- **delete <key>** : Delete text associated with this key
- **delete_me** : Delete all your keys (can't be undone)

Usage ;;key;;
'''


# REGEX
COMMAND 		= r'^;;.' # commands preceded by ;;
REPLACE 		= r'(^|\S+\s+);;\S+;;(\s+\S+|$)' # ;;word;;