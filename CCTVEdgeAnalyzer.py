from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import json
import time

class CCTVEdgeAnalyzer:
    def __init__(self):
        # 設置 Edge 選項
        self.edge_options = Options()
        self.edge_options.add_argument('--headless')  # 如果需要無頭模式則取消註釋
        self.edge_options.add_argument('--disable-gpu')
        self.edge_options.add_argument('--no-sandbox')
        self.edge_options.add_argument('--disable-dev-shm-usage')
        
        # 添加必要的 Edge 參數來捕獲網路請求
        self.edge_options.set_capability('ms:loggingPrefs', {'performance': 'ALL'})
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('CNTV-Edge')

    def _init_driver(self):
        """初始化 Edge WebDriver"""
        # 如果你的 Edge Driver 在特定位置，可以在這裡指定
        # service = Service(r"path_to_your_msedgedriver.exe")
        # return webdriver.Edge(service=service, options=self.edge_options)
        return webdriver.Edge(options=self.edge_options)

    def _wait_for_network_idle(self, driver, timeout=20):
        """等待網路請求完成"""
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            time.sleep(3)  # 額外等待一些時間確保所有請求完成
        except Exception as e:
            self.logger.warning(f"等待頁面加載時出錯: {str(e)}")

    def get_prefix_hls_url(self, hls_url: str) -> str:
        try:
            # 檢查輸入
            if not isinstance(hls_url, str):
                print("hls_url 必須是字符串類型")
                return ""
                
            if not hls_url:
                print("hls_url 不能為空")
                return ""
                
            # 分割並檢查結果
            if "default/" in hls_url and "/main":
                prefix_of_hls_url = hls_url.split("default/")[1]
                prefix_of_hls_url = prefix_of_hls_url.split("/main")[0]
                return prefix_of_hls_url
            else:
                print("URL 中沒有找到 'main' 關鍵字")
                return hls_url  # 或者返回原始URL
                
        except Exception as e:
            print(f"處理 hls_url 時出錯: {str(e)}")
            return ""

    def get_api_response_about_hls_url(self, url):
        """獲取 API 請求的回應內容"""

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
            'Accept': '*/*',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Origin': 'https://tv.cctv.com',
            'Referer': 'https://tv.cctv.com/',
            'sec-ch-ua': '"Chromium";v="122", "Edge";v="122", "Not(A:Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
        }
        
        try:
            from urllib.request import Request, urlopen
            from urllib.error import URLError
            
            # 創建請求
            req = Request(
                url,
                headers=self.headers,
            )
            
            # 發送請求並讀取回應
            with urlopen(req) as response:
                data = response.read()
                json_data = json.loads(data.decode('utf-8'))
                res = {
                    'hls_url': json_data['hls_url'],
                    'video_length': json_data['video']['totalLength']
                }
                return res
                
        except URLError as e:
            self.logger.warning(f"URL 錯誤：{e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON 解析錯誤：{e}")
            return None
        except Exception as e:
            self.logger.warning(f"其他錯誤：{e}")
            return None
        



    def find_api_requests(self, video_page_url):
        """查找所有 API 請求"""
        driver = None
        try:
            self.logger.info("啟動 Edge 瀏覽器...")
            driver = self._init_driver()
            
            self.logger.info(f"訪問頁面: {video_page_url}")
            driver.get(video_page_url)
            
            # 等待頁面加載
            self.logger.info("等待頁面加載...")
            self._wait_for_network_idle(driver)
            
            # 獲取所有網路請求
            logs = driver.get_log('performance')
            
            # 提取相關請求
            api_request = None
            ts_request = None
            
            for entry in logs:
                try:
                    if api_request != None and ts_request != None:
                        break

                    message = json.loads(entry['message'])['message']                                    
                    if ('params' in message and 
                        'request' in message['params'] and 
                        'url' in message['params']['request']):
                        url = message['params']['request']['url']
                        # 分類不同的請求
                        if 'getHttpVideoInfo.do' in url:
                            api_request = url
                        elif '.ts' in url:
                            ts_request= url
                            
                except Exception as e:
                    continue
            
            return {
                'api_request': api_request,
                'ts_request': ts_request  # 只返回前5個 ts 請求作為示例
            }
                
        except Exception as e:
            self.logger.error(f"查找 API 請求時出錯: find_api_requests {str(e)}")
            return None
        finally:
            if driver:
                driver.quit()
    