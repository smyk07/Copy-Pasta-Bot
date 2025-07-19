# cmds/forbesify.py
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger_eng')

def handle_forbesify_command(reply):
	if reply is None:
		return "You need to reply to a message to use this command."
	
	text = reply.resolved.content
	if not text:
		return "Message has no text content to forbesify."

	words = text.split()
	tagged = nltk.pos_tag(words)
	result_words = []
	
	for word, tag in tagged:
		if tag in ['VB', 'VBD', 'VBG', 'VBN']:
			result_words.extend(['accidentally', word])
		else:
			result_words.append(word)
	
	return ' '.join(result_words)