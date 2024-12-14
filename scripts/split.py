from PIL import Image
import os

# Load the animated GIF
gif_path = "./themes/touhou_boss.gif"
output_dir = "./themes/"
gif = Image.open(gif_path)

# Extract and save frames
frame_count = 0
while True:
    frame_path = os.path.join(output_dir, f"touhou_boss_frame_{frame_count}.png")
    gif.save(frame_path)
    frame_count += 1
    try:
        gif.seek(frame_count)  # Move to the next frame
    except EOFError:
        break  # No more frames
