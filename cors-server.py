#!/usr/bin/env python3
"""
CORS-enabled proxy server for LocalStack dashboard
Handles CORS issues by proxying requests to LocalStack
"""

import http.server
import socketserver
import json
import urllib.request
import urllib.parse
from urllib.error import URLError, HTTPError
import os

PORT = 8080
LOCALSTACK_URL = 'http://localhost:4566'

class CORSProxyHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        if self.path.startswith('/api/'):
            # Proxy request to LocalStack
            self.proxy_to_localstack()
        elif self.path == '/' or self.path == '/dashboard':
            # Serve dashboard
            self.serve_dashboard()
        else:
            # Serve static files
            super().do_GET()

    def proxy_to_localstack(self):
        """Proxy requests to LocalStack with CORS headers"""
        try:
            # Remove /api prefix and forward to LocalStack
            localstack_path = self.path[4:]  # Remove '/api'
            url = f"{LOCALSTACK_URL}{localstack_path}"
            
            print(f"🔄 Proxying: {self.path} -> {url}")
            
            # Make request to LocalStack
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read()
                
                # Send successful response with CORS headers
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(data)
                
        except HTTPError as e:
            print(f"❌ HTTP Error {e.code}: {e.reason}")
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({'error': f'HTTP {e.code}: {e.reason}'})
            self.wfile.write(error_response.encode())
            
        except URLError as e:
            print(f"❌ Connection Error: {e.reason}")
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({'error': f'LocalStack connection failed: {e.reason}'})
            self.wfile.write(error_response.encode())
            
        except Exception as e:
            print(f"❌ Proxy Error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({'error': f'Proxy error: {str(e)}'})
            self.wfile.write(error_response.encode())

    def serve_dashboard(self):
        """Serve the dashboard HTML"""
        try:
            with open('dashboard.html', 'r') as f:
                content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(content.encode())
        except FileNotFoundError:
            self.send_response(404)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>Dashboard not found</h1>')

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), CORSProxyHandler) as httpd:
        print(f"🚀 LocalStack CORS Proxy Server starting at http://localhost:{PORT}")
        print(f"📊 Dashboard: http://localhost:{PORT}/")
        print(f"🔄 Proxy: http://localhost:{PORT}/api/* -> http://localhost:4566/*")
        print(f"⚡ LocalStack: http://localhost:4566")
        print("Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")

if __name__ == "__main__":
    main()
