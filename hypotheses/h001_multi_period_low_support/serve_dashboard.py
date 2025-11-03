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
SCRIPT_DIR = Path(__file__).parent
HTML_FILE = SCRIPT_DIR / 'consecutive_breaks_dashboard_lite.html'
DATA_FILE = SCRIPT_DIR / '../../price_data_filtered.parquet'

# Find an available port (start at 8000)
def find_available_port(start_port=8000, max_attempts=10):
    """Find an available port, trying ports in sequence"""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', port))
            sock.close()
            return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find available port between {start_port} and {start_port + max_attempts}")

PORT = find_available_port()

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
    import shutil

    # Check if files exist
    if not HTML_FILE.exists():
        print(f"❌ Error: HTML file not found at {HTML_FILE}")
        return

    if not DATA_FILE.exists():
        print(f"❌ Error: Data file not found at {DATA_FILE}")
        print(f"   Expected location: {DATA_FILE}")
        return

    # Copy parquet file to h001 directory if not already there
    LOCAL_DATA_FILE = SCRIPT_DIR / 'price_data_filtered.parquet'
    if not LOCAL_DATA_FILE.exists():
        print(f"📋 Copying data file to {SCRIPT_DIR}...")
        try:
            shutil.copy(DATA_FILE, LOCAL_DATA_FILE)
            print(f"✅ Data file copied successfully")
        except Exception as e:
            print(f"❌ Error copying data file: {e}")
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

    # Open browser automatically after a short delay (if available)
    def open_browser():
        time.sleep(1)  # Give server time to start
        try:
            webbrowser.open(f'http://localhost:{PORT}/consecutive_breaks_dashboard_lite.html')
        except Exception as e:
            # Browser not available (headless environment), just print URL
            print(f"\n🌐 Browser not available - open manually:")
            print(f"   http://localhost:{PORT}/consecutive_breaks_dashboard_lite.html\n")

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
