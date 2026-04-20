#!/usr/bin/env python3
"""Simple HTTP server for the Demo Store.

Run this script to serve the demo store locally:
    python serve.py

Then visit: http://localhost:5500
"""

import http.server
import socketserver
import os

PORT = 5500
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Enable CORS for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"╔════════════════════════════════════════════╗")
        print(f"║       Demo Store is now running!          ║")
        print(f"╠════════════════════════════════════════════╣")
        print(f"║  URL:  http://localhost:{PORT}               ║")
        print(f"║                                            ║")
        print(f"║  Make sure the EmoraTest backend is       ║")
        print(f"║  running at http://localhost:8000         ║")
        print(f"║                                            ║")
        print(f"║  Press Ctrl+C to stop the server          ║")
        print(f"╚════════════════════════════════════════════╝")
        print()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Demo Store stopped.")
