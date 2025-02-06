# gui_module.py:
import tkinter as tk
from tkinter import messagebox
import logging
from stock_ai_analysis.data_collector import get_stock_data
from stock_ai_analysis.report_generator import generate_report
from stock_ai_analysis.ai_model import train_model_for_stock, predict_next_price, adjust_prediction_with_memory
import pandas as pd
import os
import threading

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
STOCK_LIST_FILE = "stocks.csv"
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

class StockAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("股票分析 AI 系統")
        self.create_widgets()

    def create_widgets(self):
        self.title_label = tk.Label(self.root, text="股票分析 AI 系統", font=("Helvetica", 16))
        self.title_label.grid(row=0, column=0, columnspan=2, pady=10)
        self.stock_list_label = tk.Label(self.root, text="股票列表：")
        self.stock_list_label.grid(row=1, column=0, sticky="e")
        self.stock_listbox = tk.Listbox(self.root, height=10, width=40)
        self.stock_listbox.grid(row=1, column=1, padx=10)
        self.load_stock_list()
        self.add_stock_label = tk.Label(self.root, text="新增股票 (代碼)：")
        self.add_stock_label.grid(row=2, column=0, sticky="e")
        self.add_stock_entry = tk.Entry(self.root)
        self.add_stock_entry.grid(row=2, column=1, sticky="w", padx=10)
        self.add_stock_button = tk.Button(self.root, text="新增", command=self.add_stock)
        self.add_stock_button.grid(row=2, column=2, padx=10)
        self.delete_stock_button = tk.Button(self.root, text="刪除選中股票", command=self.delete_stock)
        self.delete_stock_button.grid(row=3, column=1, pady=10)
        self.analyze_button = tk.Button(self.root, text="開始分析選中股票", command=self.analyze_selected_stock)
        self.analyze_button.grid(row=4, column=1, pady=10)
        self.batch_analyze_button = tk.Button(self.root, text="批量分析所有股票", command=self.batch_analyze)
        self.batch_analyze_button.grid(row=5, column=1, pady=10)
        self.backtest_button = tk.Button(self.root, text="回測分析", command=self.backtest_analysis)
        self.backtest_button.grid(row=6, column=1, pady=10)

    def load_stock_list(self):
        self.stock_listbox.delete(0, tk.END)
        if os.path.exists(STOCK_LIST_FILE):
            df = pd.read_csv(STOCK_LIST_FILE)
            for _, row in df.iterrows():
                self.stock_listbox.insert(tk.END, f"{row['symbol']} ({row['category']})")

    def add_stock(self):
        symbol = self.add_stock_entry.get().strip().upper()
        if not symbol:
            messagebox.showwarning("輸入錯誤", "請輸入股票代碼！")
            return
        if self.is_stock_in_list(symbol):
            messagebox.showwarning("重複項目", f"股票 {symbol} 已存在於清單中！")
            return
        try:
            if os.path.exists(STOCK_LIST_FILE):
                df = pd.read_csv(STOCK_LIST_FILE)
            else:
                df = pd.DataFrame(columns=["symbol", "category"])
            df = df.append({"symbol": symbol, "category": "未分類"}, ignore_index=True)
            df.to_csv(STOCK_LIST_FILE, index=False)
            self.load_stock_list()
            self.add_stock_entry.delete(0, tk.END)
            logging.info(f"新增股票 {symbol} 成功！")
        except Exception as e:
            logging.error(f"新增股票失敗: {str(e)}")
            messagebox.showerror("錯誤", "新增股票失敗！")

    def is_stock_in_list(self, symbol):
        if os.path.exists(STOCK_LIST_FILE):
            df = pd.read_csv(STOCK_LIST_FILE)
            return symbol in df["symbol"].values
        return False

    def delete_stock(self):
        selected = self.stock_listbox.curselection()
        if not selected:
            messagebox.showwarning("操作錯誤", "請選擇要刪除的股票！")
            return
        try:
            selected_stock = self.stock_listbox.get(selected[0]).split(" (")[0]
            df = pd.read_csv(STOCK_LIST_FILE)
            df = df[df["symbol"] != selected_stock]
            df.to_csv(STOCK_LIST_FILE, index=False)
            self.load_stock_list()
            logging.info(f"刪除股票 {selected_stock} 成功！")
        except Exception as e:
            logging.error(f"刪除股票失敗: {str(e)}")
            messagebox.showerror("錯誤", "刪除股票失敗！")

    def analyze_selected_stock(self):
        selected = self.stock_listbox.curselection()
        if not selected:
            messagebox.showwarning("操作錯誤", "請選擇要分析的股票！")
            return
        symbol = self.stock_listbox.get(selected[0]).split(" (")[0]
        threading.Thread(target=self.perform_analysis, args=(symbol,), daemon=True).start()

    def batch_analyze(self):
        threading.Thread(target=self.perform_batch_analysis, daemon=True).start()

    def backtest_analysis(self):
        threading.Thread(target=self.perform_backtest_analysis, daemon=True).start()

    def perform_analysis(self, symbol):
        try:
            logging.info(f"開始分析股票 {symbol}...")
            from stock_ai_analysis.data_collector import get_stock_data
            data = get_stock_data(symbol, period="1y", interval="1d")
            if data is None or data.empty:
                messagebox.showerror("錯誤", f"股票 {symbol} 數據無效！")
                return
            from stock_ai_analysis.ai_model import train_model_for_stock, predict_next_price, adjust_prediction_with_memory
            model_short = train_model_for_stock(symbol, data, window=10)
            short_prediction = predict_next_price(model_short, data, window=10)
            short_prediction = adjust_prediction_with_memory(symbol, short_prediction)
            model_long = train_model_for_stock(symbol, data, window=50)
            long_prediction = predict_next_price(model_long, data, window=50)
            long_prediction = adjust_prediction_with_memory(symbol, long_prediction)
            from stock_ai_analysis.report_generator import generate_report
            report_path = generate_report([{
                "symbol": symbol,
                "short_prediction": short_prediction,
                "long_prediction": long_prediction
            }])
            messagebox.showinfo("完成", f"分析完成，報告已保存至 {report_path}")
            logging.info(f"股票 {symbol} 分析完成")
        except Exception as e:
            logging.error(f"分析股票 {symbol} 失敗: {str(e)}")
            messagebox.showerror("錯誤", "分析失敗！")

    def perform_batch_analysis(self):
        try:
            df = pd.read_csv(STOCK_LIST_FILE)
            for _, row in df.iterrows():
                symbol = row["symbol"]
                self.perform_analysis(symbol)
        except Exception as e:
            logging.error(f"批量分析失敗: {str(e)}")
            messagebox.showerror("錯誤", "批量分析失敗！")

    def perform_backtest_analysis(self):
        try:
            logging.info("開始回測分析...")
            selected_stocks = self.select_random_stocks(10)
            backtest_results = []
            for symbol in selected_stocks:
                logging.info(f"回測股票 {symbol}...")
                from stock_ai_analysis.data_collector import get_stock_data
                data = get_stock_data(symbol, period="150d", interval="1d")
                if data is None or data.empty:
                    logging.warning(f"{symbol} 數據無效，跳過...")
                    continue
                train_data = data.iloc[:-50]
                validate_data = data.iloc[-50:]
                from stock_ai_analysis.ai_model import train_model_for_stock, predict_next_price, adjust_prediction_with_memory
                short_model = train_model_for_stock(symbol, train_data, window=10)
                short_predictions = self.predict_future_prices(short_model, train_data, len(validate_data), window=10)
                long_model = train_model_for_stock(symbol, train_data, window=50)
                long_predictions = self.predict_future_prices(long_model, train_data, len(validate_data), window=50)
                validate_prices = validate_data["Close"].values
                short_error = sum(abs(validate_prices - short_predictions)) / len(validate_prices)
                long_error = sum(abs(validate_prices - long_predictions)) / len(validate_prices)
                backtest_results.append({
                    "symbol": symbol,
                    "short_error": short_error,
                    "long_error": long_error,
                })
                if short_error > 5 or long_error > 5:
                    self.trigger_ai_learning(symbol, short_error, long_error)
            report_path = self.save_backtest_results(backtest_results)
            messagebox.showinfo("完成", f"回測分析完成，結果已保存至 {report_path}")
        except Exception as e:
            logging.error(f"回測分析失敗: {str(e)}")
            messagebox.showerror("錯誤", "回測分析失敗！")

    def select_random_stocks(self, num):
        try:
            df = pd.read_csv(STOCK_LIST_FILE)
            return df["symbol"].sample(n=num).tolist()
        except Exception as e:
            logging.error(f"隨機選擇股票失敗: {str(e)}")
            return []

    def predict_future_prices(self, model, data, steps, window):
        predictions = []
        current_window = data["Close"].values[-window:]
        for _ in range(steps):
            predicted = model.predict(current_window.reshape(1, -1, 1))
            predictions.append(predicted[0, 0])
            current_window = current_window[1:]
            current_window = list(current_window) + [predicted[0, 0]]
        return predictions

    def trigger_ai_learning(self, symbol, short_error, long_error):
        logging.info(f"觸發 AI 學習，股票: {symbol}, 短期誤差: {short_error}, 長期誤差: {long_error}")
        # 擴充學習機制，例如定期再訓練、調整權重或引入增強學習
        pass

    def save_backtest_results(self, results):
        try:
            df = pd.DataFrame(results)
            report_path = os.path.join(CACHE_DIR, "backtest_results.csv")
            df.to_csv(report_path, index=False)
            logging.info(f"回測結果保存至 {report_path}")
            return report_path
        except Exception as e:
            logging.error(f"保存回測結果失敗: {str(e)}")
            return None

if __name__ == "__main__":
    root = tk.Tk()
    app = StockAnalyzerGUI(root)
    root.mainloop()
