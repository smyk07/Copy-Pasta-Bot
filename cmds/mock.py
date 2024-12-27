import os
from PIL import Image, ImageDraw, ImageFont
import discord

def get_asset_path(filename: str) -> str:
    # Get the path to the root directory (one level up from cmds folder)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root_dir, 'assets', filename)

def fit_text_to_width(draw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
    """
    Returns the longest substring of text that fits within max_width,
    adding ellipsis if text is truncated.
    """
    if draw.textlength(text, font=font) <= max_width:
        return text
        
    # Binary search for the maximum fitting length
    left, right = 0, len(text)
    while left < right:
        mid = (left + right + 1) // 2
        test_text = text[:mid] + "..."
        if draw.textlength(test_text, font=font) <= max_width:
            left = mid
        else:
            right = mid - 1
            
    return text[:left] + "..."

def create_mock_image(text: str) -> str:
    """
    Creates a SpongeBob mocking meme with the given text.
    Returns the path to the saved image.
    """
    # Convert text to mocking format (alternating case)
    mocked_text = ''.join(c.upper() if i % 2 else c.lower() for i, c in enumerate(text))
    
    # Open the base image
    base_image = Image.open(get_asset_path('mock.jpg'))
    
    # Create a drawing object
    draw = ImageDraw.Draw(base_image)
    
    # Load the font
    font = ImageFont.truetype(get_asset_path('Impacted.ttf'), 36)  # Adjust size as needed
    
    # Get image dimensions
    img_w, img_h = base_image.size
    
    # Calculate maximum width for text (80% of image width)
    max_text_width = int(img_w * 0.9)
    
    # Fit text to width
    fitted_text = fit_text_to_width(draw, mocked_text, font, max_text_width)
    
    # Get text dimensions
    text_bbox = draw.textbbox((0, 0), fitted_text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    
    # Calculate text position (centered)
    x = (img_w - text_w) // 2
    y = img_h - text_h - 20  # 20 pixels from bottom
    
    # Add text to image
    draw.text((x, y), fitted_text, font=font, fill='white')
    
    # Save the image
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp_mock.jpg')
    base_image.save(output_path)
    
    return output_path

def handle_mock_command(reply: discord.MessageReference) -> discord.File:
    """
    Handles the mock command by creating and returning a meme image.
    """
    if reply is None or reply.resolved is None:
        return None
        
    target_message = reply.resolved.content
    if not target_message:
        return None
        
    image_path = create_mock_image(target_message)
    return discord.File(image_path)
