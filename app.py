from CCTVEdgeAnalyzer import CCTVEdgeAnalyzer
from tsDownloader import Downloader
from urllib.request import Request, urlopen
from urllib.error import URLError
import logging
import json
from targetPages import video_page_list

API_PREFIX = "https://hls.cntv.cdn20.com/asp/hls/1200/0303000a/3/default/"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

HEADER = {
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

videoMap = []

class App:
    def __init__(self):       
        self.logger = logging.getLogger('App')
        self.video_page_list = video_page_list
        self.hls_code_list = []

    def __get_length_of_video(self, length) -> int:
        videoLength = length.split(':')
        totalLength = int(videoLength[0]) * 60 * 60 + int(videoLength[1]) * 60 + int(videoLength[2])
        return totalLength
    
    def __get_api_response(self, api_url):
        try:
            # 創建請求
            req = Request(
                api_url,
                headers=HEADER,
            )
            
            # 發送請求並讀取回應
            with urlopen(req) as response:
                data = response.read()
                content = data.decode('utf-8')
                # 處理 JSONP
                # 移除 "lanmu_2(" 和最後的 ");"
                json_str = content.strip()
                json_str = json_str.removeprefix('lanmu_2(')
                json_str = json_str.removesuffix(');')
                json_str = json_str.removesuffix(')')  # 有時候可能沒有分號
                json_res = json.loads(json_str)
                hls_list = json_res["data"]["list"]

                for hls in hls_list:
                    if not (hls in self.hls_code_list):
                        self.hls_code_list.append({"guid": hls["guid"], "length": self.__get_length_of_video(hls["length"])})
                return
                
        except URLError as e:
            self.logger.warning(f"URL 錯誤：{e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON 解析錯誤：{e}")
            return None
        except Exception as e:
            self.logger.warning(f"其他錯誤：{e}")
            return None
    
    def main(self):
        if len(self.video_page_list) > 0:
            print("start looping")
            for video_page_url in self.video_page_list:
                self.__get_api_response(video_page_url)


if __name__ == "__main__":
    app = App()
    app.main()
    download = Downloader()
    video = app.hls_code_list[0]
    download.start_download(API_PREFIX + video["guid"], video["length"], video["guid"])




# def main():
#     analyzer   = CCTVEdgeAnalyzer()
#     downloader = Downloader()

#     # 視頻頁面 URL
#     video_url = "https://tv.cctv.com/2024/11/18/VIDErt2ZtnrN5L6iOrkM64lW241118.shtml?spm=C52346.PAqPdYX587cN.EdNN02ac93CE.265"

#     # 查找所有相關請求
#     print("正在查找相關請求...")
#     result_data = analyzer.find_api_requests(video_url)
#     api_request, ts_request = result_data['api_request'], result_data['ts_request']

#     # 印出 API 請求
#     if api_request:
#         res_of_hls_url = analyzer.get_api_response_about_hls_url(api_request)
#         hls_url, video_length = res_of_hls_url['hls_url'], res_of_hls_url['video_length']
#         video_length = int(float(video_length)) // 10
        
#         prefix_of_hls_url = analyzer.get_prefix_hls_url(hls_url)
#         downloader.start_download(API_PREFIX + prefix_of_hls_url, video_length, prefix_of_hls_url)
        



# if __name__ == "__main__":
#     downloader = Downloader()
#     downloader.start_download(API_PREFIX + "26a1c4341b284580ac49e9965573e492", 10, "test")
#     # main()