"""
后台工作线程
"""
import requests
from PySide6.QtCore import QThread, Signal


class StreamWorker(QThread):
    """流式 API 调用线程 — 支持实时推送数据块"""
    chunk = Signal(str)       # 流式数据块
    finished = Signal(object)  # 最终结果

    def __init__(self, url, json_data):
        super().__init__()
        self._url = url
        self._json = json_data

    def run(self):
        try:
            r = requests.post(self._url, json=self._json, stream=True, timeout=120)
            full_text = ''
            for line in r.iter_lines(decode_unicode=True):
                if line and line.startswith('data: '):
                    chunk_text = line[6:]
                    if chunk_text == '[DONE]':
                        break
                    if chunk_text.startswith('[ERROR]'):
                        err = chunk_text[8:] if len(chunk_text) > 8 else '未知错误'
                        self.finished.emit({'full_text': '', 'error': err})
                        return
                    full_text += chunk_text
                    self.chunk.emit(chunk_text)  # 实时推送
            self.finished.emit({'full_text': full_text, 'error': None})
        except Exception as e:
            self.finished.emit({'full_text': '', 'error': str(e)})


class ApiWorker(QThread):
    """后台 API 调用线程"""
    finished = Signal(object)

    def __init__(self, target, *args):
        super().__init__()
        self._target = target
        self._args = args

    def run(self):
        try:
            result = self._target(*self._args)
        except Exception as e:
            result = {'error': str(e), 'success': False}
        self.finished.emit(result)
