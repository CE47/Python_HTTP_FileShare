# ⚡ Zero‑Config Multi‑Threaded HTTP File Server

**Single‑file Python HTTP file share** – the fastest way to share files over your local network.

> No dependencies. No config files. Just copy, paste, and share.

## Why this instead of `python3 -m http.server`?

The built‑in server is **single‑threaded** – one download blocks all others.  
This server is **multi‑threaded**, handles **concurrent downloads**, and automatically shows you the IP addresses to use.

Perfect for:
- **LAN file sharing** with multiple colleagues
- **Ad‑hoc file exchange** between devices
- **Quickly serving static assets** during development
- **Replacing the slow default server** without any extra setup

## Features

| Feature | Benefit |
|---------|---------|
| 🧵 **Thread pool** | Handles many simultaneous downloads (auto‑scaled to 4× CPU cores) |
| 🌐 **Auto‑IP display** | Shows all reachable IPv4 addresses on startup – no more `ifconfig` |
| ⏱️ **Timeouts** | 5s socket + 30s HTTP timeout – prevents hanging clients |
| 📦 **Cache headers** | Browsers cache files for 1 hour – reduces redundant requests |
| 🔁 **Port reuse** | No “address already in use” errors on restart |
| 🧹 **Clean shutdown** | `Ctrl+C` stops gracefully without orphan threads |
| 🔇 **No logging** | Maximises throughput by skipping per‑request I/O |
| 📁 **Serves current directory** | Just like `http.server`, but **way faster** |

## Quick Start

### One‑liner (copy & paste into any terminal)

```bash
python3 -c "
import http.server, socketserver, os, sys, socket
from concurrent.futures import ThreadPoolExecutor

PORT = 8001
MAX_WORKERS = max(10, (os.cpu_count() or 1) * 4)
REQUEST_TIMEOUT = 30
SOCKET_TIMEOUT = 5

def get_local_ips():
    ips = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM):
            ip = info[4][0]
            if not ip.startswith('127.'):
                ips.append(ip)
    except:
        pass
    if not ips:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ips.append(s.getsockname()[0])
            s.close()
        except:
            pass
    return ips

class PoolTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    def get_request(self):
        request, client_address = super().get_request()
        request.settimeout(SOCKET_TIMEOUT)
        return request, client_address
    def process_request(self, request, client_address):
        self.executor.submit(self.process_request_thread, request, client_address)
    def server_close(self):
        self.executor.shutdown(wait=True)
        super().server_close()

class FastHandler(http.server.SimpleHTTPRequestHandler):
    timeout = REQUEST_TIMEOUT
    def log_message(self, format, *args):
        pass
    def end_headers(self):
        self.send_header('Cache-Control', 'public, max-age=3600')
        super().end_headers()

with PoolTCPServer(('', PORT), FastHandler) as httpd:
    print(f'Serving at port {PORT}')
    ips = get_local_ips()
    if ips:
        print('Reachable at:')
        for ip in ips:
            print(f'  http://{ip}:{PORT}')
    else:
        print(f'  (could not determine IP – try http://localhost:{PORT})')
    print(f'Thread pool: max {MAX_WORKERS} workers')
    print(f'Socket timeout: {SOCKET_TIMEOUT}s, HTTP timeout: {REQUEST_TIMEOUT}s')
    sys.stdout.flush()
    httpd.serve_forever()
"
