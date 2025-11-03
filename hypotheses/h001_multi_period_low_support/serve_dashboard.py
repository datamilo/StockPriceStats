"""
Simple HTTP server to serve the lightweight dashboard with parquet data loading.
This solves the CORS issue when opening HTML files locally.

Usage:
    python serve_dashboard.py
    Then open browser to: http://localhost:8000/consecutive_breaks_dashboard_lite.html
"""

import http.server
import socketserver
import webbrowser
from pathlib import Path
import time

# Configuration
PORT = 8000
SCRIPT_DIR = Path(__file__).parent
HTML_FILE = SCRIPT_DIR / 'consecutive_breaks_dashboard_lite.html'
DATA_FILE = SCRIPT_DIR / '../../price_data_filtered.parquet'

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow loading parquet file
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Suppress verbose logging
        if 'GET' in format:
            print(f"[{self.address_string()}] {format % args}")

def main():
    # Check if files exist
    if not HTML_FILE.exists():
        print(f"❌ Error: HTML file not found at {HTML_FILE}")
        return

    if not DATA_FILE.exists():
        print(f"⚠️  Warning: Data file not found at {DATA_FILE}")
        print(f"   Make sure price_data_filtered.parquet is in the parent directory")
        return

    # Change to script directory so server can serve files
    import os
    os.chdir(SCRIPT_DIR)

    # Create server
    handler = MyHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), handler)

    print("=" * 60)
    print("📊 Consecutive Breaks Dashboard Server")
    print("=" * 60)
    print(f"✅ Server started on http://localhost:{PORT}")
    print(f"📄 HTML file: {HTML_FILE.name}")
    print(f"📊 Data file: {DATA_FILE.name}")
    print()
    print("🌐 Opening dashboard in your browser...")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)

    # Open browser automatically after a short delay
    def open_browser():
        time.sleep(1)  # Give server time to start
        webbrowser.open(f'http://localhost:{PORT}/consecutive_breaks_dashboard_lite.html')

    import threading
    thread = threading.Thread(target=open_browser, daemon=True)
    thread.start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped")
        httpd.server_close()

if __name__ == '__main__':
    main()
