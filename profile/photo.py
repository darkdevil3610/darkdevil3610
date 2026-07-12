"""
Prepare a portrait photo for clean ASCII conversion:
  1. remove the background (rembg) so the subject is isolated
  2. boost LOCAL contrast so a flatly-lit face gains highlights and shadows
     -- this is what turns a dark blob into a recognizable face
  3. composite the subject onto pure white so the background reads as blank
     (white -> spaces in the ascii ramp)

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.
Run once whenever the source photo changes; the ascii SVG itself is static.

    python scripts/prep_photo.py <input.jpg> [output.png]
"""
import os
import sys

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from rembg import remove

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, ".."))


def resolve_input_path(path):
   if os.path.isabs(path):
      return path

   candidates = [
      path,
      os.path.join(HERE, path),
      os.path.join(REPO_ROOT, path),
      os.path.join(HERE, os.path.basename(path)),
      os.path.join(REPO_ROOT, os.path.basename(path)),
   ]
   for candidate in candidates:
      if os.path.exists(candidate):
         return candidate
   return path


INP = resolve_input_path(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.jpg")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

# 1. cut out the subject
cut = remove(Image.open(INP).convert("RGBA"))
gray = ImageOps.grayscale(cut)
alpha = cut.getchannel("A")                      # 0 = background

# 2. local-contrast the luminance without requiring OpenCV or numpy
gray = ImageOps.autocontrast(gray, cutoff=1)
gray = ImageEnhance.Contrast(gray).enhance(1.25)
gray = ImageEnhance.Brightness(gray).enhance(1.05)
gray = gray.filter(ImageFilter.UnsharpMask(radius=1, percent=140, threshold=3))

# 3. paste onto white using the alpha mask (feathered a hair to avoid a halo)
mask = alpha.filter(ImageFilter.GaussianBlur(radius=1.0))

white = Image.new("L", gray.size, 255)
out = Image.composite(gray, white, mask)

out.save(OUT)
print("wrote", OUT, out.size)