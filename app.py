# app.py
import threading
import tkinter as tk
from stock_ai_analysis.scheduler import start_scheduler
from gui_module import StockAnalyzerGUI
import logging

# 設置日誌：清除現有處理器後添加文件和控制台處理器
logger = logging.getLogger()
logger.setLevel(logging.INFO)
if logger.hasHandlers():
    logger.handlers.clear()

file_handler = logging.FileHandler("app.log", mode="a", encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

logger.info("日誌已設定，app.log 將自動生成。")

def run_scheduler():
    """
    在背景線程中啟動 APScheduler，定時（每小時）生成報表並發送 Gmail。
    """
    try:
        start_scheduler()  # 注意：start_scheduler() 使用 BackgroundScheduler
    except Exception as e:
        logger.error(f"排程運行失敗: {e}")

def run_gui():
    """
    啟動桌面 GUI 介面。
    """
    root = tk.Tk()
    app = StockAnalyzerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    # 啟動排程線程（守護線程）
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("背景排程已啟動，每小時自動發送報表。")

    # 啟動 GUI 主介面
    run_gui()
