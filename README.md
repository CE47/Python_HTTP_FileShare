# Fast Multi‑Threaded HTTP File Server

A drop‑in replacement for `python3 -m http.server` that handles **multiple concurrent downloads** with a thread pool, socket timeouts, cache headers, and automatic IP detection.

Perfect for quickly sharing files from your laptop or server with several users – without any extra dependencies.

## Features

- 🚀 **Concurrent downloads** – fixed thread pool (auto‑scaled to 4× CPU cores, min 10)
- 🌐 **Auto‑IP detection** – shows all non‑loopback IPv4 addresses on startup
- ⏱️ **Timeouts** – socket timeout (5s) and HTTP request timeout (30s) prevent hanging clients
- 📦 **Cache headers** – `Cache-Control: public, max‑age=3600` reduces repeated downloads
- 🔁 **Port reuse** – `allow_reuse_address = True` avoids “address already in use” errors
- 🧹 **Clean shutdown** – `daemon_threads = True` + executor shutdown on `Ctrl+C`
- 📁 **Serves current directory** – just like the standard `http.server`
- 🔇 **No logging** – suppresses per‑request output for maximum performance

## Requirements

- **Python 3.6+** (uses `f‑strings` and `concurrent.futures`)
- No third‑party packages – only the standard library.

## Usage

### One‑liner (copy & paste into terminal)

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
