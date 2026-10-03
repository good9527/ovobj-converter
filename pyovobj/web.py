# -*- coding: utf-8 -*-
"""
pyovobj.web
-----------
Lightweight, zero-dependency embedded Web UI for interactive .ovobj drag-and-drop
conversion, map preview, and reverse packing.
"""

import os
import sys
import io
import json
import zipfile
import tempfile
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import geopandas as gpd

from pyovobj import __version__, read_ovobj, write_ovobj
from pyovobj.exporters.manager import export_dataset, SUPPORTED_FORMATS

INDEX_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ovobj Converter Web Toolkit</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    :root {
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --bg: #0f172a;
      --card-bg: #1e293b;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --border: #334155;
      --success: #10b981;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); display: flex; height: 100vh; overflow: hidden; }
    #sidebar { width: 420px; background: var(--card-bg); border-right: 1px solid var(--border); padding: 24px; display: flex; flex-direction: column; gap: 20px; overflow-y: auto; }
    #map-container { flex: 1; height: 100%; position: relative; }
    #map { width: 100%; height: 100%; }
    .header { border-bottom: 1px solid var(--border); padding-bottom: 16px; }
    .header h1 { font-size: 20px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 8px; }
    .badge { background: #3b82f6; color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 9999px; }
    .header p { font-size: 13px; color: var(--text-muted); margin-top: 6px; }
    .drop-zone { border: 2px dashed var(--border); border-radius: 12px; padding: 28px 16px; text-align: center; cursor: pointer; transition: all 0.2s; background: rgba(15, 23, 42, 0.4); }
    .drop-zone:hover, .drop-zone.dragover { border-color: var(--primary); background: rgba(37, 99, 235, 0.08); }
    .drop-zone svg { width: 40px; height: 40px; fill: var(--primary); margin-bottom: 8px; }
    .drop-zone p { font-size: 14px; font-weight: 500; }
    .drop-zone span { font-size: 12px; color: var(--text-muted); display: block; margin-top: 4px; }
    .form-group { display: flex; flex-direction: column; gap: 8px; }
    .form-group label { font-size: 13px; font-weight: 600; color: var(--text); }
    select, input { background: #0f172a; border: 1px solid var(--border); color: #fff; padding: 10px 12px; border-radius: 8px; font-size: 13px; outline: none; }
    select:focus, input:focus { border-color: var(--primary); }
    .format-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
    .format-card { background: #0f172a; border: 1px solid var(--border); border-radius: 8px; padding: 8px; font-size: 12px; display: flex; align-items: center; gap: 6px; cursor: pointer; }
    .format-card input { margin: 0; }
    .btn { background: var(--primary); color: #fff; border: none; border-radius: 8px; padding: 12px; font-size: 14px; font-weight: 600; cursor: pointer; transition: background 0.2s; display: flex; justify-content: center; align-items: center; gap: 8px; }
    .btn:hover { background: var(--primary-hover); }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .stats { background: #0f172a; border-radius: 8px; padding: 12px; border: 1px solid var(--border); font-size: 12px; display: none; }
    .stats-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .stats-row:last-child { border: none; }
  </style>
</head>
<body>
  <div id="sidebar">
    <div class="header">
      <h1>🗺️ Ovobj Converter <span class="badge">v1.0</span></h1>
      <p>奥维专有矢量二进制解码与多格式互转工作台</p>
    </div>

    <div class="drop-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
      <svg viewBox="0 0 24 24"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/></svg>
      <p>拖拽 .ovobj 文件到此处</p>
      <span>或点击浏览本地文件</span>
      <input type="file" id="fileInput" accept=".ovobj,.json,.geojson" style="display: none;" onchange="handleFileSelect(event)">
    </div>

    <div class="stats" id="statsBox">
      <div class="stats-row"><span>文件名</span><strong id="statName">-</strong></div>
      <div class="stats-row"><span>要素总数</span><strong id="statCount">0</strong></div>
      <div class="stats-row"><span>几何类型</span><strong id="statTypes">-</strong></div>
    </div>

    <div class="form-group">
      <label>目标工程投影 (CRS)</label>
      <select id="crsSelect">
        <option value="EPSG:4535">CGCS2000 / 3度分带 75E (EPSG:4535)</option>
        <option value="EPSG:4536">CGCS2000 / 3度分带 78E (EPSG:4536)</option>
        <option value="EPSG:4547">CGCS2000 / 3度分带 114E (EPSG:4547)</option>
        <option value="EPSG:4549">CGCS2000 / 3度分带 120E (EPSG:4549)</option>
        <option value="EPSG:4326">WGS-84 经纬度 (EPSG:4326)</option>
        <option value="EPSG:3857">Web Mercator (EPSG:3857)</option>
      </select>
    </div>

    <div class="form-group">
      <label>选择导出格式</label>
      <div class="format-grid">
        <label class="format-card"><input type="checkbox" name="fmt" value="shp" checked> Shapefile</label>
        <label class="format-card"><input type="checkbox" name="fmt" value="gpkg" checked> GeoPackage</label>
        <label class="format-card"><input type="checkbox" name="fmt" value="dxf" checked> AutoCAD DXF</label>
        <label class="format-card"><input type="checkbox" name="fmt" value="kml" checked> KML</label>
        <label class="format-card"><input type="checkbox" name="fmt" value="geojson" checked> GeoJSON</label>
        <label class="format-card"><input type="checkbox" name="fmt" value="xlsx" checked> Excel</label>
        <label class="format-card"><input type="checkbox" name="fmt" value="csv"> CSV</label>
        <label class="format-card"><input type="checkbox" name="fmt" value="fgb"> FlatGeobuf</label>
        <label class="format-card"><input type="checkbox" name="fmt" value="tab"> MapInfo</label>
      </div>
    </div>

    <button class="btn" id="exportBtn" disabled onclick="executeExport()">
      🚀 开始转换并下载压缩包
    </button>
  </div>

  <div id="map-container">
    <div id="map"></div>
  </div>

  <script>
    const map = L.map('map').setView([39.0, 77.0], 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);

    let currentFile = null;
    let geojsonLayer = null;

    const dropZone = document.getElementById('dropZone');
    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
      if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
    });

    function handleFileSelect(e) {
      if (e.target.files.length) handleFile(e.target.files[0]);
    }

    async function handleFile(file) {
      currentFile = file;
      document.getElementById('dropZone').querySelector('p').innerText = file.name;
      const formData = new FormData();
      formData.append('file', file);

      try {
        const resp = await fetch('/api/preview', { method: 'POST', body: formData });
        const data = await resp.json();
        if (data.error) {
          alert('解析失败: ' + data.error);
          return;
        }

        // Update stats
        document.getElementById('statsBox').style.display = 'block';
        document.getElementById('statName').innerText = file.name;
        document.getElementById('statCount').innerText = data.count;
        document.getElementById('statTypes').innerText = Object.entries(data.types).map(([k,v]) => `${k}:${v}`).join(', ');
        document.getElementById('exportBtn').disabled = false;

        // Render GeoJSON
        if (geojsonLayer) map.removeLayer(geojsonLayer);
        geojsonLayer = L.geoJSON(data.geojson, {
          style: { color: '#3b82f6', weight: 2, fillOpacity: 0.35 }
        }).addTo(map);
        map.fitBounds(geojsonLayer.getBounds());
      } catch (err) {
        alert('请求失败: ' + err);
      }
    }

    async function executeExport() {
      if (!currentFile) return;
      const selected = Array.from(document.querySelectorAll('input[name="fmt"]:checked')).map(cb => cb.value);
      if (!selected.length) {
        alert('请至少勾选一种导出格式！');
        return;
      }
      const crs = document.getElementById('crsSelect').value;
      const formData = new FormData();
      formData.append('file', currentFile);
      formData.append('formats', selected.join(','));
      formData.append('crs', crs);

      const btn = document.getElementById('exportBtn');
      btn.disabled = true;
      btn.innerText = '⏳ 正在转换打包中...';

      try {
        const resp = await fetch('/api/export', { method: 'POST', body: formData });
        if (!resp.ok) throw new Error('导出失败');
        const blob = await resp.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = currentFile.name.replace(/\.[^/.]+$/, '') + '_exported.zip';
        document.body.appendChild(a);
        a.click();
        a.remove();
      } catch (err) {
        alert('导出异常: ' + err);
      } finally {
        btn.disabled = false;
        btn.innerText = '🚀 开始转换并下载压缩包';
      }
    }
  </script>
</body>
</html>
"""

class OvobjWebHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(INDEX_HTML.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        # Parse multipart form data
        content_type = self.headers.get('Content-Type', '')
        boundary = content_type.split('boundary=')[-1].encode('ascii')

        parts = post_data.split(b'--' + boundary)
        file_bytes = None
        file_name = "data.ovobj"
        formats = "shp,gpkg,dxf,kml,geojson,xlsx"
        crs = "EPSG:4535"

        for part in parts:
            if b'name="file"' in part:
                headers, _, body = part.partition(b'\r\n\r\n')
                file_bytes = body.rstrip(b'\r\n')
                # Extract filename
                for line in headers.decode('utf-8', errors='ignore').splitlines():
                    if 'filename=' in line:
                        file_name = line.split('filename=')[-1].strip('"')
            elif b'name="formats"' in part:
                _, _, body = part.partition(b'\r\n\r\n')
                formats = body.rstrip(b'\r\n').decode('utf-8', errors='ignore')
            elif b'name="crs"' in part:
                _, _, body = part.partition(b'\r\n\r\n')
                crs = body.rstrip(b'\r\n').decode('utf-8', errors='ignore')

        if parsed_path.path == '/api/preview':
            if not file_bytes:
                self.send_json({'error': 'No file uploaded'}, status=400)
                return

            with tempfile.NamedTemporaryFile(suffix='.ovobj', delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            try:
                gdf = read_ovobj(tmp_path)
                types = gdf.geometry.type.value_counts().to_dict()
                # Limit preview to 500 features for fast browser rendering
                preview_gdf = gdf.iloc[:500] if len(gdf) > 500 else gdf
                geojson_str = preview_gdf.to_json()
                self.send_json({
                    'count': len(gdf),
                    'types': types,
                    'geojson': json.loads(geojson_str)
                })
            except Exception as e:
                self.send_json({'error': str(e)}, status=500)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        elif parsed_path.path == '/api/export':
            if not file_bytes:
                self.send_error(400, "Missing file")
                return

            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_src = os.path.join(tmp_dir, file_name)
                with open(tmp_src, 'wb') as f:
                    f.write(file_bytes)

                export_out = os.path.join(tmp_dir, "exports")
                base_name = os.path.splitext(file_name)[0]
                gdf = read_ovobj(tmp_src)
                fmt_list = [f.strip() for f in formats.split(',') if f.strip()]
                export_dataset(gdf, export_out, base_name, formats=fmt_list, target_crs=crs)

                # Create zip archive in memory
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for root, _, files in os.walk(export_out):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, export_out)
                            zip_file.write(file_path, arcname)

                zip_data = zip_buffer.getvalue()
                self.send_response(200)
                self.send_header('Content-Type', 'application/zip')
                self.send_header('Content-Disposition', f'attachment; filename="{base_name}_exports.zip"')
                self.send_header('Content-Length', str(len(zip_data)))
                self.end_headers()
                self.wfile.write(zip_data)

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def start_web_server(port: int = 8080):
    server = HTTPServer(('127.0.0.1', port), OvobjWebHandler)
    print(f"\n========================================================")
    print(f"[*] Ovobj Converter Web GUI is running at: http://127.0.0.1:{port}")
    print(f"[*] Open your browser to drag & drop .ovobj files!")
    print(f"[*] Press Ctrl+C to terminate the web server.")
    print(f"========================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nWeb server stopped.")

if __name__ == '__main__':
    start_web_server()
