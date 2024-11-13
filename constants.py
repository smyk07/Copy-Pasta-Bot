DB_NAME 		= 'mysqlite.db'
KEY_EXISTS 		= 'Could not add because this key already exists. Use `add_o` to overwrite.'
SUCCESSFUL 		= 'Success!'
UNSUCCESSFUL 	= 'Something went wrong :/'
WRONG_ARGS		= '`add <key> <value>` or `add <key>` and reply to a message'
EMPTY_LIST		= 'You have not saved any text yet.'
EMPTY_MESSAGE	= 'The message you replied to seems to be empty.'
HELP_TEXT		= '''
Start command with `;;`
- **add <key> <message>** : Add text to db
- **add_o <key> <message>** : Add text but overwrite if exists
- **help** : This message
- **saved** : See all saved texts
- **delete <key>** : Delete text associated with this key

Usage ;;key;;
'''


# REGEX
COMMAND 		= r'^;;([a-zA-Z0-9_\-]|\ )+$' # commands preceded by ;
REPLACE 		= r'(^|\S+\s+);;[a-zA-Z0-9_\-]+;;(\s+\S+|$)' # ;;word;;