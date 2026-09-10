#!/usr/bin/env python3
"""Export cv/print/index.html to partials/Janaka_Premathilaka_CV_2026.pdf with headless Chrome.
Fails if the result is not exactly two pages."""
import os, subprocess, sys, http.server, threading, socketserver, functools
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = os.path.join(ROOT, "partials", "Janaka_Premathilaka_CV_2026.pdf")

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=ROOT))
PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
try:
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--no-pdf-header-footer",
                    "--virtual-time-budget=8000", f"--print-to-pdf={OUT}",
                    f"http://127.0.0.1:{PORT}/cv/print/index.html"], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
finally:
    srv.shutdown()
from pypdf import PdfReader
n = len(PdfReader(OUT).pages)
print(f"wrote {OUT}: {n} pages, {os.path.getsize(OUT)//1024} KB")
sys.exit(0 if n == 2 else 1)
