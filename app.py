import http.server
import socketserver
import json
import os
import sys
import re
import hashlib
import traceback
import time
import requests
from PIL import Image, ImageFile
from io import BytesIO
from urllib.parse import unquote, urlparse, parse_qs

PORT = 8000
DB_FILE = "db.json"
CONFIG_FILE = "config.json"
THUMB_DIR = "thumbnails"

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None 
sys.stdout.reconfigure(encoding='utf-8')
requests.packages.urllib3.disable_warnings()

if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump({"proxy": ""}, f)
if not os.path.exists(THUMB_DIR):
    os.makedirs(THUMB_DIR)

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/links':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.wfile.write((content if content else "[]").encode('utf-8'))
            except:
                self.wfile.write(b"[]")
            return
        
        if self.path == '/api/config':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.wfile.write(f.read().encode('utf-8'))
            return

        if self.path.startswith('/api/process?url='):
            try:
                url_part = self.path.split('url=')[1]
                url = unquote(url_part)
                result = self.process_image(url)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            except Exception:
                error_msg = traceback.format_exc()
                print(f"❌ 后台报错: {sys.exc_info()[1]}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(sys.exc_info()[1])}).encode('utf-8'))
            return
        return super().do_GET()

    def do_POST(self):
        try:
            length = int(self.headers['Content-Length'])
            post_body = self.rfile.read(length).decode('utf-8')
        except: return

        if self.path == '/api/links':
            try:
                new_data = json.loads(post_body)
                with open(DB_FILE, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, ensure_ascii=False, indent=2)
                self.send_response(200)
                self.wfile.write(b"OK")
            except: self.send_response(500)
            return
        
        if self.path == '/api/config':
            try:
                new_conf = json.loads(post_body)
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(new_conf, f, ensure_ascii=False, indent=2)
                self.send_response(200)
                self.wfile.write(b"OK")
            except: self.send_response(500)
            return

        if self.path == '/api/test_proxy':
            try:
                payload = json.loads(post_body)
                proxy = payload.get('proxy', '').strip()
                result = self.test_proxy_connection(proxy)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            except: self.send_response(500)
            return

        if self.path == '/api/delete':
            try:
                payload = json.loads(post_body)
                self.delete_item(payload.get('url'))
                self.send_response(200)
                self.wfile.write(b"Deleted")
            except: self.send_response(500)
            return

    def delete_item(self, target_url):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            item = next((i for i in data if i['url'] == target_url), None)
            if item:
                if item.get('thumb'):
                    path = item['thumb'].replace('/', os.sep)
                    if os.path.exists(path):
                        try: os.remove(path)
                        except: pass
                data.remove(item)
                with open(DB_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except: pass

    def get_proxies(self, custom_proxy=None):
        proxy = custom_proxy
        if proxy is None:
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    proxy = json.load(f).get('proxy', '').strip()
            except: pass
        if proxy:
            return {"http": proxy, "https": proxy}
        return {}

    def test_proxy_connection(self, proxy):
        proxies = {"http": proxy, "https": proxy} if proxy else {}
        print(f"⚡ 测试代理: {proxy}")
        try:
            requests.get("https://www.google.com", proxies=proxies, timeout=5, verify=False)
            return {"status": "success", "msg": "连接 Google 成功"}
        except Exception as e:
            return {"status": "fail", "msg": f"失败: {str(e)}"}

    def resolve_download_link(self, url, session, proxies):
        """ 智能解析下载链 (核心逻辑) """
        
        # 1. SharePoint: 强制转换 (不走网络，纯正则)
        if 'sharepoint.com' in url:
            print("🚀 SharePoint 模式")
            try:
                match_base = re.search(r'(https://[^/]+\.sharepoint\.com)', url)
                match_user = re.search(r'/(personal/[^/]+)/', url)
                if match_base and match_user:
                    base = match_base.group(1)
                    user = match_user.group(1)
                    # 提取 token
                    token = url.split('?')[0].split('/')[-1]
                    final_url = f"{base}/{user}/_layouts/52/download.aspx?share={token}"
                    return final_url, False # False = 不走代理
            except: pass
            return url, False # 默认不走代理

        # 2. 个人版: 跟踪跳转
        print("✈️ 个人版模式 (代理)")
        
        # 如果本身就是 1drv.ms，先跳一跳
        current_url = url
        if '1drv.ms' in url or 'onedrive.live.com' in url:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                }
                # 跟踪跳转，获取最终的 redir 链接
                r = session.get(url, headers=headers, proxies=proxies, stream=True, timeout=15, verify=False)
                current_url = r.url
                print(f"   ↳ 跳转至: {current_url[:50]}...")
            except Exception as e:
                print(f"   ⚠️ 跳转跟踪失败: {e}")

        # 3. 【关键修复】把 /redir 替换为 /download
        if '/redir' in current_url:
            print("   ✨ 触发 403 修复: 替换 redir -> download")
            current_url = current_url.replace('/redir', '/download')
        
        # 4. 替换 embed
        if 'embed' in current_url:
            current_url = current_url.replace('embed', 'download')

        return current_url, True # True = 走代理

    def extract_filename(self, response, original_url):
        """ 不依赖 cgi 的文件名提取 """
        filename = None
        try:
            cd = response.headers.get("Content-Disposition", "")
            if cd:
                # filename*=utf-8''xxx
                match_star = re.search(r'filename\*=([^;]+)', cd, re.IGNORECASE)
                if match_star:
                    raw = match_star.group(1).strip().strip('"').strip("'")
                    if "''" in raw: raw = raw.split("''")[-1]
                    filename = unquote(raw)
                
                if not filename:
                    match_norm = re.search(r'filename="?([^";]+)"?', cd, re.IGNORECASE)
                    if match_norm:
                        filename = unquote(match_norm.group(1))
        except: pass

        if filename: return filename

        try:
            path = urlparse(response.url).path
            name = os.path.basename(path)
            if '.' in name and len(name) < 100: return unquote(name)
        except: pass

        return f"OneDrive_{int(time.time())}.jpg"

    def process_image(self, url):
        # 创建 Session 保持 Cookie
        session = requests.Session()
        
        # 1. 获取代理配置
        proxies_conf = self.get_proxies()
        
        # 2. 解析链接 (决定是否走代理)
        download_url, use_proxy = self.resolve_download_link(url, session, proxies_conf)
        
        # 3. 配置请求环境
        request_proxies = proxies_conf if use_proxy else {}
        if not use_proxy:
            session.trust_env = False # SharePoint 强制直连
            request_proxies = {}

        print(f"⬇️ 最终下载: {download_url[:50]}... (代理: {use_proxy})")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        }

        try:
            r = session.get(download_url, headers=headers, proxies=request_proxies, stream=True, timeout=60, verify=False)
            r.raise_for_status()
        except Exception as e:
            ptype = "代理" if use_proxy else "直连"
            raise Exception(f"[{ptype}] 下载失败: {e} (请检查网络或代理)")

        if 'text/html' in r.headers.get('Content-Type', '').lower():
            raise Exception("下载失败：返回的是网页。")

        filename = self.extract_filename(r, download_url)
        filename = re.sub(r'[\\/*?:"<>|]', "", filename)

        try:
            image_data = BytesIO(r.content)
            img = Image.open(image_data)
            if img.mode != "RGB": img = img.convert("RGB")
            img.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
            thumb_filename = hashlib.md5(url.encode('utf-8')).hexdigest() + ".jpg"
            thumb_path = os.path.join(THUMB_DIR, thumb_filename)
            img.save(thumb_path, "JPEG", quality=90)
        except Exception as e:
            raise Exception(f"图片损坏: {e}")

        return {
            "real_name": filename,
            "thumb_path": f"{THUMB_DIR}/{thumb_filename}"
        }

print(f"✅ 服务已启动: http://localhost:{PORT}")
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    try: httpd.serve_forever()
    except KeyboardInterrupt: pass
