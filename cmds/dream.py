from lumaai import LumaAI
import requests
import asyncio
import discord
import do_not_push
import time
import argparse
import shlex
from io import BytesIO
import math

# Dictionary to track user cooldowns
user_cooldowns = {}

async def handle_dream_command(user, args, message=None):
	try:
		# Parse the command arguments
		parser = argparse.ArgumentParser(add_help=False)
		parser.add_argument('-v', '--video', action='store_true', help='Generate a video instead of an image')
		parser.add_argument('-i2v', '--image-to-video', action='store_true', help='Transform an image into a video')
		parser.add_argument('prompt', nargs='*', help='The prompt for generation')
		
		# Convert args to a string and use shlex to handle quoting
		args_string = " ".join(args[1:]) if args and args[0].lower() == "dream" else " ".join(args)
		try:
			parsed_args = parser.parse_args(shlex.split(args_string))
			is_video = parsed_args.video
			is_image_to_video = parsed_args.image_to_video
			prompt = " ".join(parsed_args.prompt)
		except Exception:
			# Fallback for simpler parsing if argparse fails
			is_video = "-v" in args_string or "--video" in args_string
			is_image_to_video = "-i2v" in args_string or "--image-to-video" in args_string
			
			# Remove the flags from the prompt
			prompt = args_string
			if is_video:
				prompt = prompt.replace("-v", "").replace("--video", "")
			if is_image_to_video:
				prompt = prompt.replace("-i2v", "").replace("--image-to-video", "")
			prompt = prompt.strip()
		
		# Check user permissions
		user_id = user.id
		current_time = time.time()

		# Check if user has permission to use the command at all
		if user_id not in do_not_push.ADMINS:
			# Check for cooldowns
			if user_id in user_cooldowns:
				cooldown_info = user_cooldowns[user_id]
				generation_type = cooldown_info["type"]
				last_used = cooldown_info["timestamp"]
				
				# Different cooldown periods based on generation type
				if generation_type in ["video", "image-to-video"]:
					cooldown_period = 3600  # 1 hour in seconds
				else:
					cooldown_period = 300   # 5 minutes in seconds
					
				time_elapsed = current_time - last_used
				time_remaining = cooldown_period - time_elapsed
				
				if time_remaining > 0:
					minutes_remaining = math.ceil(time_remaining / 60)
					return f"You're on cooldown for {minutes_remaining} more minute{'s' if minutes_remaining > 1 else ''}. Please try again later."
			
			# If we reach here, set the current cooldown type
			generation_type = "image-to-video" if is_image_to_video else ("video" if is_video else "image")
			user_cooldowns[user_id] = {
				"timestamp": current_time,
				"type": generation_type
			}
		
		def upload_image_to_0x0(image_bytes):
			try:
				files = {'file': ('image.jpg', image_bytes, 'image/jpeg')}
				response = requests.post("https://0x0.st", files=files)

				if response.status_code == 200:
					return response.text.strip()  # The URL of the uploaded image
				else:
					return None
			except Exception as e:
				return None
		
		# Image to video requires a reply to a message with an image
		if is_image_to_video:
			if not message:
				return "For image-to-video generation, you must reply to a message containing an image."
				
			# In your implementation, 'message' is already the MessageReference object
			# Get the resolved message directly
			replied_to = message.resolved
			if not replied_to:
				return "Could not find the message you're replying to."
			
			# Check if the message has attachments and at least one is an image
			image_url = None
			if replied_to.attachments:
				for attachment in replied_to.attachments:
					if hasattr(attachment, "content_type") and attachment.content_type and attachment.content_type.startswith('image/'):
						image_url = attachment.url
						break
			
			# Check for embeds with images if no attachments found
			if not image_url and replied_to.embeds:
				for embed in replied_to.embeds:
					if embed.image:
						image_url = embed.image.url
						break
			
			if not image_url:
				return "The message you replied to doesn't contain any images."
			
			image_response = requests.get(image_url)
			if image_response.status_code != 200:
				return f"Failed to download the image from Discord CDN: HTTP {image_response.status_code}"
			
			# Upload the image to 0x0.st
			uploaded_image_url = upload_image_to_0x0(image_response.content)
			if not uploaded_image_url:
				return "Failed to upload image to 0x0.st. Please try again later."
		
		if not prompt and not is_image_to_video:
			return "Please provide a prompt for generation. Usage: ;;dream <prompt>, ;;dream -v <prompt> for video, or ;;dream -i2v <prompt> to transform an image to video (must reply to a message with an image)"
		
		# Initialize Luma AI client with auth_token
		client = LumaAI(auth_token=do_not_push.LUMA_API_KEY)
		
		# Initial response to indicate we're working on it
		generation_type = "image-to-video" if is_image_to_video else ("video" if is_video else "image")
		initial_response = f"Creating {generation_type} for prompt: '{prompt}'... This might take a few minutes."
		
		# Create the generation request based on type
		if is_image_to_video:
			# Create image-to-video generation
			generation = client.generations.create(
				prompt=prompt if prompt else "Transform this image into a cinematic video",
				model="ray-2",
				keyframes={
					"frame0": {
						"type": "image",
						"url": uploaded_image_url
					}
				},
				resolution="540p",
				duration="5s"
			)

		elif is_video:
			# Use specific parameters for video generation
			generation = client.generations.video.create(
				prompt=prompt,
				model="ray-2",
				resolution="540p",
				duration="5s"
			)
		else:
			generation = client.generations.image.create(prompt=prompt)
		
		# Poll until completion
		completed = False
		polling_count = 0
		max_polling = 120  # Maximum poll attempts (10 minutes with 5 second intervals)
		
		while not completed and polling_count < max_polling:
			generation = client.generations.get(id=generation.id)
			
			if generation.state == "completed":
				completed = True
			elif generation.state == "failed":
				return f"{generation_type.capitalize()} generation failed: {generation.failure_reason}"
			
			# Wait before checking again (longer interval for videos)
			polling_interval = 5 if (is_video or is_image_to_video) else 3
			await asyncio.sleep(polling_interval)
			polling_count += 1
			
		if not completed:
			return f"{generation_type.capitalize()} generation timed out. Please try again later."
		
		# Get the media URL and appropriate file extension
		if is_video or is_image_to_video:
			media_url = generation.assets.video
			file_extension = "mp4"
			discord_filename = "dream_video_result.mp4"
		else:
			media_url = generation.assets.image
			file_extension = "jpg"
			discord_filename = "dream_result.jpg"
		
		# Download the generated content
		response = requests.get(media_url, stream=True)
		file_path = f'{generation.id}.{file_extension}'
		
		with open(file_path, 'wb') as file:
			file.write(response.content)
		
		# Create a Discord file object
		discord_file = discord.File(
			file_path,
			filename=discord_filename,
			description=f"Dream {generation_type} completed for '{prompt}'"
		)
		
		return discord_file
		
	except Exception as e:
		return f"Error generating content: {str(e)}"