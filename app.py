import http.server, socketserver, os, sys, socket
from concurrent.futures import ThreadPoolExecutor

PORT = 8001
MAX_WORKERS = max(10, (os.cpu_count() or 1) * 4)
REQUEST_TIMEOUT = 30
SOCKET_TIMEOUT = 5

# ---- Helper to get all reachable IPs (excludes 127.0.0.1) ----
def get_local_ips():
    ips = []
    try:
        # Get all IPs associated with the hostname
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM):
            ip = info[4][0]
            if not ip.startswith('127.'):   # skip loopback
                ips.append(ip)
    except:
        pass
    # Fallback: try to find default route IP
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
        print('  (could not determine IP – try http://localhost:{PORT})')
    print(f'Thread pool: max {MAX_WORKERS} workers')
    print(f'Socket timeout: {SOCKET_TIMEOUT}s, HTTP timeout: {REQUEST_TIMEOUT}s')
    sys.stdout.flush()
    httpd.serve_forever()
