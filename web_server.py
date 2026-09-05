"""
web_server.py
Lightweight HTTP server to run and preview the 'The Community 2' interactive web dashboard.
Usage:
    python web_server.py [--port 8000]
"""

import os
import sys
import webbrowser
import http.server
import socketserver
import argparse

DEFAULT_PORT = 8000


def run_server(port: int = DEFAULT_PORT, auto_open: bool = True):
    web_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(web_dir)

    handler = http.server.SimpleHTTPRequestHandler

    # Allow port reuse
    socketserver.TCPServer.allow_reuse_address = True

    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            url = f"http://localhost:{port}/index.html"
            print("=" * 70)
            print("  🌐 '더 커뮤니티 2: 보이지 않는 손' 웹 대시보드 서버 가동")
            print("=" * 70)
            print(f"  • 서버 URL: {url}")
            print(f"  • 호스팅 디렉토리: {web_dir}")
            print("  • 종료하려면 Ctrl+C를 누르세요.")
            print("=" * 70)

            if auto_open:
                webbrowser.open(url)

            httpd.serve_forever()
    except OSError as e:
        if e.errno == 98 or e.errno == 10048:
            print(f"⚠️ 포트 {port}가 이미 사용 중입니다. 포트 {port+1}로 재시도합니다...")
            run_server(port + 1, auto_open)
        else:
            raise e
    except KeyboardInterrupt:
        print("\n🛑 웹 서버가 종료되었습니다.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="웹 대시보드 로컬 서버 실행기")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="포트 번호 (기본값: 8000)")
    parser.add_argument("--no-open", action="store_true", help="브라우저 자동 열기 비활성화")
    args = parser.parse_args()

    run_server(port=args.port, auto_open=not args.no_open)
