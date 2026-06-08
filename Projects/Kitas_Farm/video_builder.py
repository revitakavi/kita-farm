# C:\KITA FARM\Projects\Kitas_Farm\video_builder.py
"""
KITA FARM Automated Video Builder
Loads the approved script/audio metadata and stitches images from KITA FARM's Raw media
using MoviePy with Ken Burns zooming effects, subtitle overlay, and output rendering.
"""

import os
import sys
import json
import glob
import re
from moviepy import ImageClip, ColorClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, TextClip, VideoFileClip, vfx



# Fix for MoviePy throwing AttributeError on newer Pillow versions
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

def get_sorted_images(media_dir):
    files = glob.glob(os.path.join(media_dir, "**", "*.jpg"), recursive=True)
    # Pick 5-8 random images if there are too many, to keep compilation fast
    if len(files) > 6:
        import random
        return random.sample(files, 6)
    return files

def apply_ken_burns(clip, target_duration):
    # Resize and crop to 9:16 (1080x1920) in MoviePy v2 style
    clip = clip.resized(height=1920)
    if clip.w > 1080:
        clip = clip.cropped(x_center=clip.w/2, width=1080)
    else:
        clip = clip.resized(width=1080)
        clip = clip.cropped(y_center=clip.h/2, height=1920)
        
    def zoom(t):
        # Scale up slightly over time (Ken Burns effect)
        return 1 + 0.08 * (t / target_duration)
        
    return clip.resized(zoom).cropped(x_center=540, y_center=960, width=1080, height=1920)

def build_reels_video():
    # Load today's approved script info if available
    today_content = {}
    meta_path = "Projects/Kitas_Farm/today_content.json"
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                today_content = json.load(f)
        except Exception as e:
            print(f"Error reading today_content.json: {e}")

    visual_mode = today_content.get("visual_mode", "ai_generated")
    topic = today_content.get("topic", "KITA FARM ผักสลัดพรีเมียม")
    category = today_content.get("category", "TOURING")
    script_text = today_content.get("script", "")

    # We will generate a 15-second preview (3 images, 5 seconds each) to match short vertical formats
    target_duration = 15.0
    img_duration = 5.0
    num_images_needed = 3
    
    # Locate photos based on visual style
    # If farm_footage, we look in uploads directory. If empty, fall back.
    ai_dir = "Raw/KitaFarm_Media/ai_generated"
    uploads_dir = "Raw/KitaFarm_Media/uploads"
    fallback_dir = "Raw/KitaFarm_Media/facebook"
    
    all_images = []
    if visual_mode == "ai_generated" and os.path.exists(ai_dir):
        # Load scene images in order
        all_images = [os.path.join(ai_dir, f"scene_{i}.jpg") for i in range(1, 4)]
        all_images = [p for p in all_images if os.path.exists(p)]
        print(f"Visual Mode: ai_generated. Found {len(all_images)} generated photos.")

    if not all_images and visual_mode == "farm_footage" and os.path.exists(uploads_dir):
        all_images = glob.glob(os.path.join(uploads_dir, "**", "*.jpg"), recursive=True)
        print(f"Visual Mode: farm_footage. Found {len(all_images)} employee-uploaded photos.")
        
    if not all_images:
        # Fall back to standard/facebook photo directory
        all_images = glob.glob(os.path.join(fallback_dir, "**", "*.jpg"), recursive=True)
        print(f"Visual Mode: {visual_mode} (using facebook/AI pool). Found {len(all_images)} photos.")

    if not all_images:
        # Absolute safety check: check any jpeg anywhere under Raw
        all_images = glob.glob(os.path.join("Raw", "**", "*.jpg"), recursive=True)

    if not all_images:
        print(f"Error: No images found at all.")
        return False
        
    # Pick 3 images (repeat if we have fewer)
    import random
    images = []
    if visual_mode == "ai_generated" and len(all_images) == num_images_needed:
        images = all_images
    elif len(all_images) >= num_images_needed:
        images = random.sample(all_images, num_images_needed)
    else:
        images = list(all_images)
        while len(images) < num_images_needed:
            images.append(random.choice(all_images))
            
    print(f"Using {len(images)} images for the {target_duration}s video (5s each)")
    
    clips = []
    for idx, img in enumerate(images):
        print(f"Processing image {idx+1}/{len(images)}: {os.path.basename(img)}")
        img_clip = ImageClip(img).with_duration(img_duration)
        img_clip = apply_ken_burns(img_clip, img_duration)
        clips.append(img_clip)
        
    print("Concatenating image clips...")
    video = concatenate_videoclips(clips, method="compose")
    
    # Overlay Script Text / Hook
    text_clips = []
    hook_text = f"[{category}] {topic}"
    
    # Render main title/hook overlay
    try:
        title_clip = TextClip(
            text=hook_text, 
            font_size=55, 
            color='white', 
            font='Arial-Bold',
            stroke_color='green', 
            stroke_width=3, 
            method='caption', 
            size=(950, None)
        )
        title_clip = title_clip.with_position(('center', 150)).with_duration(target_duration)
        text_clips.append(title_clip)
    except Exception as e:
        print(f"TextClip rendering skipped/failed: {e}.")
        
    # Load audio voice track if approved
    audio_path = "Raw/Voice/daily_voice.mp3"
    if os.path.exists(audio_path):
        try:
            print("Applying Thai voiceover audio track...")
            audio = AudioFileClip(audio_path)
            if audio.duration > target_duration:
                audio = audio.subclipped(0, target_duration)
            else:
                # Pad/trim
                pass
            video = video.with_audio(audio)
        except Exception as e:
            print(f"Failed to load/apply voiceover audio: {e}")
        
    if text_clips:
        video = CompositeVideoClip([video] + text_clips)
        
    output_dir = "Projects/Kitas_Farm"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "preview_reels.mp4")
    
    print(f"Rendering final output to {output_path}...")
    # Render with fast preset and low resolution option to generate preview very quickly
    video.write_videofile(
        output_path, 
        fps=15, 
        codec="libx264", 
        preset="ultrafast", 
        ffmpeg_params=["-vf", "scale=540:960"]
    )
    print("Preview video rendering completed successfully!")
    return True

if __name__ == "__main__":
    build_reels_video()
