import sys
import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# Fix Python path
nav_dir = os.path.dirname(os.path.abspath(__file__))
if nav_dir not in sys.path:
    sys.path.insert(0, nav_dir)

from core.decision_engine import DecisionEngine

# Initialize DecisionEngine
engine = DecisionEngine()

class APIHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/api/announcements':
            # Load mock messages from data/mock_messages.json
            mock_path = os.path.join(nav_dir, 'data', 'mock_messages.json')
            if os.path.exists(mock_path):
                with open(mock_path, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
                # Filter official announcements (msg_001 to msg_004 or channel_name contains thong-bao)
                official = [m for m in messages if m.get('channel_name') in ['#Thông báo Khóa học', '#venture-arena', '#thong-bao'] or m.get('id', '').startswith('msg_')]
                self._send_json({"status": "success", "count": len(official), "announcements": official})
            else:
                self._send_json({"status": "error", "message": "mock_messages.json not found"}, status=404)

        elif path == '/api/benchmark':
            # Return precomputed 34 benchmark results
            eval_path = os.path.join(nav_dir, 'data', 'eval_results_34.json')
            if os.path.exists(eval_path):
                with open(eval_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                self._send_json({"status": "success", "total": len(results), "passed": sum(1 for r in results if r.get('is_passed')), "results": results})
            else:
                self._send_json({"status": "error", "message": "Benchmark JSON not found"}, status=404)

        elif path == '/' or path == '/index.html':
            index_file = os.path.join(nav_dir, 'web_static', 'index.html')
            if os.path.exists(index_file):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                with open(index_file, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Frontend file not found")
        else:
            # Serve static files from web_static
            file_path = os.path.join(nav_dir, 'web_static', path.lstrip('/'))
            if os.path.exists(file_path) and os.path.isfile(file_path):
                content_type = 'text/plain'
                if file_path.endswith('.css'): content_type = 'text/css'
                elif file_path.endswith('.js'): content_type = 'application/javascript'
                elif file_path.endswith('.png'): content_type = 'image/png'
                elif file_path.endswith('.svg'): content_type = 'image/svg+xml'
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "File not found")

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        try:
            req_data = json.loads(body) if body else {}
        except Exception:
            req_data = {}

        if path == '/api/query':
            question = req_data.get('question', '').strip()
            if not question:
                self._send_json({"status": "error", "message": "Question is empty"}, status=400)
                return

            res = engine.process_query(question=question)
            
            # Format output for web
            selected = None
            if res.selected_source:
                selected = {
                    "id": res.selected_source.id,
                    "channel_name": res.selected_source.channel_name,
                    "author_name": res.selected_source.author_name,
                    "posted_at": res.selected_source.posted_at,
                    "content": res.selected_source.content,
                    "status": res.selected_source.status
                }

            rejected = []
            for r in res.rejected_sources:
                rejected.append({
                    "id": r.source.id,
                    "posted_at": r.source.posted_at,
                    "channel_name": r.source.channel_name,
                    "reason": r.reason
                })

            response_payload = {
                "question": question,
                "status": res.status.value,
                "confidence": res.confidence,
                "confidence_level": res.confidence_level,
                "needs_mod": res.needs_mod,
                "answer": res.answer,
                "selected_source": selected,
                "rejected_sources": rejected,
                "verification_details": res.verification_details
            }
            self._send_json(response_payload)

        elif path == '/api/announcements/add':
            # Add a new announcement dynamically
            title = req_data.get('title', '')
            content = req_data.get('content', '')
            cohort = req_data.get('cohort', 'K4')
            msg_id = f"custom_msg_{int(os.path.getmtime(__file__))}"
            
            # In-memory add
            from models.message import SourceMessage
            new_msg = SourceMessage(
                id=msg_id,
                channel_name="#Thông báo Khóa học",
                author_name="Ban Tổ Chức (BTC)",
                author_role="official",
                posted_at="2026-07-31T10:00:00",
                content=content,
                cohort=cohort,
                topic="Announce",
                status="active"
            )
            engine.retriever.live_messages_cache.append(new_msg)
            self._send_json({"status": "success", "message": "Added announcement dynamically", "announcement": req_data})
        else:
            self._send_json({"status": "error", "message": "Unknown endpoint"}, status=404)

def run_server(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, APIHandler)
    print(f"Verified Discord Navigator Web Server running on http://localhost:{port}")
    httpd.serve_forever()

if __name__ == '__main__':
    port = 8080
    if len(sys.argv) > 1:
        try: port = int(sys.argv[1])
        except ValueError: pass
    run_server(port)
