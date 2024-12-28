def handle_clap_command(reply):
    """
    Insert clapping emoji between words in the message.
    
    Args:
        reply: The message reference containing the original message
    
    Returns:
        str: The modified message with clapping emojis
    """
    if not reply.resolved.content:
        return "Cannot clap an empty message or a message with only attachments."
    
    # Split the message into words and join with clap emoji
    words = reply.resolved.content.strip().split()
    clapped_message = " 👏 ".join(words)
    
    return clapped_message