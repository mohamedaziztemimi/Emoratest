#!/usr/bin/env python3
"""Extract text from image-based PDF using OCR."""

import sys

try:
    from pdf2image import convert_from_path
    import pytesseract
    from PIL import Image

    PDF_PATH = 'Emoratest refactroing playbook.md'
    OUTPUT_PATH = 'playbook_text.txt'

    print("Starting PDF OCR extraction...")
    print("Converting PDF to images (this may take a while)...")

    # Convert first 10 pages to images
    try:
        images = convert_from_path(
            PDF_PATH,
            dpi=300,
            first_page=1,
            last_page=10
        )
    except Exception as e:
        print(f"Error with pdf2image: {e}")
        print("\nNote: pdf2image requires poppler to be installed.")
        print("You can install it from: https://poppler.freedesktop.org/")
        sys.exit(1)

    print(f"Converted {len(images)} pages")

    full_text = ''

    for i, image in enumerate(images, 1):
        print(f"OCR on page {i}...", end=' ')
        try:
            text = pytesseract.image_to_string(image)
            full_text += f"\n{'='*60}\n"
            full_text += f"PAGE {i}\n"
            full_text += f"{'='*60}\n"
            full_text += text + '\n\n'
            print(f"Done ({len(text)} chars)")
        except Exception as e:
            print(f"Error: {e}")

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(full_text)

    print(f"\n=== TEXT WRITTEN TO {OUTPUT_PATH} ===")
    print(f"Total characters: {len(full_text)}")

except ImportError as e:
    print(f"Missing dependency: {e}")
    print("\nInstall required packages:")
    print("  pip install pdf2image pytesseract pillow")
    print("\nAnd install tesseract OCR:")
    print("  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
    print("  Or use: choco install tesseract")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
