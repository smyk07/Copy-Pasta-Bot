import random

def get_zalgo_chars():
    """Returns lists of combining characters for above, middle, and below effects."""
    # Above combining characters (0x300-0x36F)
    above = [chr(x) for x in range(0x300, 0x36F)]
    # Middle combining characters (0x483-0x487)
    middle = [chr(x) for x in range(0x483, 0x487)]
    # Below combining characters (0x488-0x489)
    below = [chr(x) for x in range(0x488, 0x489)]
    
    return above, middle, below

def add_zalgo_to_char(char, intensity=1):
    """Add zalgo effects to a single character."""
    if char.strip() == '':
        return char
    
    above, middle, below = get_zalgo_chars()
    zalgo_chars = []
    max_chars = max(1, intensity)  # Ensure at least 1 combining character if intensity > 0

    # Add above characters
    for _ in range(random.randint(0, max_chars - 1)):
        if len(zalgo_chars) < max_chars:
            zalgo_chars.append(random.choice(above))
    
    # Add middle characters occasionally
    if len(zalgo_chars) < max_chars and random.random() < 0.5:
        zalgo_chars.append(random.choice(middle))
    
    # Add below characters even less frequently
    if len(zalgo_chars) < max_chars and random.random() < 0.3:
        zalgo_chars.append(random.choice(below))
    
    return char + ''.join(zalgo_chars)

def handle_zalgo_command(reply, intensity=2):
    """
    Add zalgo text effects to the message.
    
    Args:
        reply: The message reference containing the original message
        intensity: How many combining characters to add (default: 1)
    
    Returns:
        str: The modified message with zalgo effects
    """
    if not reply.resolved.content:
        return "Cannot apply zalgo to an empty message or a message with only attachments."
    
    text = reply.resolved.content.strip()
    
    # Dynamically adjust intensity based on input length
    adjusted_intensity = max(1, intensity - len(text) // 50)
    
    # Apply Zalgo effect to each character selectively
    zalgo_text = ''.join(
        add_zalgo_to_char(c, adjusted_intensity) if random.random() < 0.7 else c
        for c in text
    )
    
    return zalgo_text