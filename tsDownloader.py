"""
異步下载ts资源文件
"""
import asyncio
import aiohttp
import aiofiles
import logging
import os

HEADERS = {"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
           "referer":"https://tv.cctv.com/"}

class Downloader:
    def __init__(self):
        self.headers = HEADERS
        self.logger = logging.getLogger(__name__)
        self.timeout = aiohttp.ClientTimeout(total=30)  # 設置超時
        self.max_retries = 3  # 最大重試次數

    def __merge(self, amount, video_name):
        # 生成文件列表
        movie_list = [f"{i}.ts" for i in range(amount)]
        
        try:
            # 檢查並創建輸出目錄
            os.makedirs("ts_temp", exist_ok=True)
            
            # 進入 video1 目錄
            os.chdir("./ts_temp")
            
            # 檢查所有文件是否存在
            for file in movie_list:
                if not os.path.exists(file):
                    print(f"文件不存在: {file}")
                    return
            
            # 使用 ffmpeg 合併
            input_files = '|'.join(movie_list)
            cmd = f'ffmpeg -i "concat:{input_files}" -c copy -bsf:a aac_adtstoasc ../videos/{video_name}.mp4'
            
            print("開始合併...")
            result = os.popen(cmd)
            output = result.read()
            print(output)
            
            # 檢查輸出文件
            if os.path.exists(f"{video_name}.mp4"):
                print(f"合併完成: {video_name}.mp4")
            else:
                print("合併失敗")
                
        except Exception as e:
            print(f"發生錯誤: {str(e)}")
    
        finally:
            # 返回上一層目錄
            os.chdir("../")

    async def __download_one(self, url, sem):
        retries = 0
        while retries < self.max_retries:
            try:
                async with sem:
                    file_name = url.split("/")[-1]
                    self.logger.info(f"開始下載: {file_name} (嘗試 {retries + 1})")
                    
                    async with aiohttp.ClientSession(timeout=self.timeout) as session:
                        async with session.get(url, headers=self.headers) as res:
                            if res.status != 200:
                                self.logger.error(f"下載失敗 {file_name}: HTTP {res.status}")
                                retries += 1
                                await asyncio.sleep(1)  # 等待一秒後重試
                                continue
                            content = await res.content.read()
                            
                        async with aiofiles.open(f"ts_temp/{file_name}", mode="wb") as f:
                            await f.write(content)
                            
                        self.logger.info(f"{file_name} 下載成功")
                        return  # 成功後退出重試循環
                        
            except asyncio.TimeoutError:
                self.logger.warning(f"{file_name} 超時，重試第 {retries + 1} 次")
                retries += 1
                await asyncio.sleep(2)  # 超時後等待更久
            except Exception as e:
                self.logger.error(f"下載出錯 {file_name}: {str(e)}")
                retries += 1
                await asyncio.sleep(1)
                
        self.logger.error(f"{file_name} 達到最大重試次數，下載失敗")

    async def __download_all(self, url, amount):
        try:
            sem = asyncio.Semaphore(1000)
            tasks = []
            for i in range(amount):
                task = asyncio.create_task(self.__download_one(url + f"/{i}.ts", sem))
                tasks.append(task)
            await asyncio.wait(tasks)
            
        except Exception as e:
            self.logger.error(f"批次下載出錯: {str(e)}")

    def start_download(self, url, amount, video_name):
        try:
            self.logger.info(f"開始下載 {amount} 個檔案")
            asyncio.run(self.__download_all(url, amount))
            self.logger.info("下載完成")
            self.logger.info(f"開始合併 {amount} 個檔案")
            self.__merge(amount, video_name)

            
        except Exception as e:
            self.logger.error(f"下載程序出錯: {str(e)}")
