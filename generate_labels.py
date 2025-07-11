import pandas as pd
import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
from math import ceil

# Load data
df = pd.read_excel("technical_asset_inventory.xlsx")
if "Functional" not in df.columns:
    df["Functional"] = 0

# Label settings
label_width = 300
label_height = 220
grid_labels = ["Calibrated", "In Use", "Maintenance", "Functional"]
font_path = "arial.ttf"  # Change if needed

# Create output dir
os.makedirs("labels", exist_ok=True)

def draw_label(asset_id):
    img = Image.new("RGB", (label_width, label_height), "white")
    draw = ImageDraw.Draw(img)

    # QR Code
    qr = qrcode.make(str(asset_id))
    qr = qr.resize((100, 100))
    img.paste(qr, (10, 10))

    # Grid
    grid_x, grid_y = 120, 10
    box_w, box_h = 80, 40
    for i in range(2):
        for j in range(2):
            x0 = grid_x + j * box_w
            y0 = grid_y + i * box_h
            x1 = x0 + box_w
            y1 = y0 + box_h
            draw.rectangle([x0, y0, x1, y1], outline="black", width=2)
            label_index = i * 2 + j
            draw.text((x0 + 5, y0 + 12), grid_labels[label_index], fill="black")

    # ID below
    draw.text((10, 120), f"Asset ID: {asset_id}", fill="black")

    return img

# Create one image per label
label_imgs = []
for asset_id in df["Asset_ID"]:
    label_img = draw_label(asset_id)
    label_imgs.append(label_img)

# Combine into A4 pages (3 columns x 4 rows per page)
cols, rows = 3, 4
labels_per_page = cols * rows
pages = ceil(len(label_imgs) / labels_per_page)

a4_width = cols * label_width
a4_height = rows * label_height

for p in range(pages):
    page = Image.new("RGB", (a4_width, a4_height), "white")
    for i in range(labels_per_page):
        idx = p * labels_per_page + i
        if idx >= len(label_imgs): break
        label = label_imgs[idx]
        x = (i % cols) * label_width
        y = (i // cols) * label_height
        page.paste(label, (x, y))
    page.save(f"labels/page_{p+1}.png")

print("✅ Labels generated in 'labels/' folder.")
