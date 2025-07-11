from flask import Flask, request, jsonify, render_template_string
import sqlite3
import cv2
import numpy as np
from PIL import Image
import io
import datetime
import os

app = Flask(__name__)
DB_PATH = 'assets.db'

GRID_BOXES = [
    (20, 150, 120, 190),  # Calibration_Status
    (120, 150, 220, 190), # Is_In_Use
    (20, 190, 120, 230),  # Maintenance_Required
    (120, 190, 220, 230), # Functional
]

@app.route('/')
def index():
    with open("index.html", "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()
    html += '<br><a href="/dashboard"><button style="padding:10px 20px;font-size:16px;">📊 View Dashboard</button></a>'
    return html

@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get column names from the table
    cursor.execute("PRAGMA table_info(assets)")
    columns = [col[1] for col in cursor.fetchall()]

    # Get all rows
    cursor.execute("SELECT * FROM assets")
    rows = cursor.fetchall()
    conn.close()

    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Asset Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #f1f1f1; }
            table { border-collapse: collapse; width: 100%; background: white; font-size: 14px; }
            th, td { border: 1px solid #ccc; padding: 6px; text-align: center; }
            th { background: #333; color: white; position: sticky; top: 0; z-index: 10; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            #searchBar { width: 100%; padding: 8px; margin-bottom: 12px; font-size: 16px; }
        </style>
    </head>
    <body>
        <h1>📊 Asset Dashboard</h1>
        <input type="text" id="searchBar" onkeyup="searchTable()" placeholder="Search assets...">
        <div style="overflow-x:auto;">
        <table id="assetTable">
            <tr>
                {% for col in columns %}
                <th>{{ col }}</th>
                {% endfor %}
            </tr>
            {% for row in rows %}
            <tr>
                {% for cell in row %}
                <td>{{ cell }}</td>
                {% endfor %}
            </tr>
            {% endfor %}
        </table>
        </div>
        <script>
        function searchTable() {
            const input = document.getElementById("searchBar").value.toLowerCase();
            const rows = document.querySelectorAll("#assetTable tr:not(:first-child)");
            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(input) ? "" : "none";
            });
        }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html, rows=rows, columns=columns)


@app.route('/scan', methods=['POST'])
def scan_label():
    file = request.files.get('image')
    if not file:
        return jsonify({'error': 'No image provided'}), 400

    image_bytes = np.array(Image.open(io.BytesIO(file.read())).convert('RGB'))
    gray = cv2.cvtColor(image_bytes, cv2.COLOR_RGB2GRAY)

    qr_decoder = cv2.QRCodeDetector()
    asset_id, _, _ = qr_decoder.detectAndDecode(gray)
    if not asset_id:
        return jsonify({'error': 'QR Code not found'}), 400

    marks = []
    for (x0, y0, x1, y1) in GRID_BOXES:
        roi = gray[y0:y1, x0:x1]
        _, thresh = cv2.threshold(roi, 180, 255, cv2.THRESH_BINARY_INV)
        black_pixels = cv2.countNonZero(thresh)
        marks.append(1 if black_pixels > 200 else 0)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM assets WHERE Asset_ID = ?", (asset_id,))
    if cursor.fetchone()[0] == 0:
        return jsonify({'error': f'Asset_ID \"{asset_id}\" not found in DB'}), 404

    cursor.execute("""
        UPDATE assets SET 
            Calibration_Status = ?,
            Is_In_Use = ?,
            Maintenance_Required = ?,
            Functional = ?,
            last_updated = ?
        WHERE Asset_ID = ?
    """, (*marks, datetime.datetime.now().isoformat(), asset_id))
    conn.commit()
    conn.close()

    return jsonify({'Asset_ID': asset_id, 'updated': marks})

if __name__ == '__main__':
    app.run(debug=True)
