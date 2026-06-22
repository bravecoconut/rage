# app/stage_6/edit_image/edit.py

"""Compose the final post image by overlaying caption text on the background asset."""

from PIL import Image, ImageDraw, ImageFont
from textwrap import wrap

import os

def add_meme_text(image_id, text):
    """Add wrapped caption text below the image and save the composed post asset."""
    try:
        error = {'error': None}

        image_path = f"data/images/{image_id}.png"

        output_path = f"data/results_images/{image_id}.png"
        
        img = Image.open(image_path).convert("RGBA")
        width, height = img.size

        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=30
            )
        except Exception as e:
            font = ImageFont.load_default()
            error['error'] = e 
            return error

        padding = 20
        line_spacing = 10
        lines = wrap(text, width=55)

        # Measure line height to size the caption strip.
        sample_bbox = font.getbbox("A")
        line_height = sample_bbox[3] - sample_bbox[1]
        text_strip_height = (line_height + line_spacing) * len(lines) + padding * 3

        # Apply a bottom gradient fade so the caption area blends into the image.
        fade_height = 100
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        for i in range(fade_height):
            alpha = int(255 * (i / fade_height))
            y_line = height - fade_height + i
            draw_overlay.line([(0, y_line), (width, y_line)], fill=(0, 0, 0, alpha))
        img = Image.alpha_composite(img, overlay).convert("RGB")

        # Render caption lines on a dedicated black strip below the image.
        text_strip = Image.new("RGB", (width, text_strip_height), color=(0, 0, 0))
        draw = ImageDraw.Draw(text_strip)

        y = padding
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, y), line, font=font, fill=(255, 255, 255))
            y += line_height + line_spacing

        # Stack the image and caption strip into the final post asset.
        final = Image.new("RGB", (width, height + text_strip_height), color=(0, 0, 0))
        final.paste(img, (0, 0))
        final.paste(text_strip, (0, height))
        final.save(output_path)

        return image_id
    
    except Exception as e:
        error['error'] = e 
        return error

