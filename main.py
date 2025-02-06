# main.py:
import pandas as pd
import logging
import json
import datetime
from stock_ai_analysis.config import EMAIL_SETTINGS
from stock_ai_analysis.data_collector import get_stock_data
from stock_ai_analysis.technical_analysis import add_technical_indicators
from stock_ai_analysis.ai_model import (
    train_model_for_stock,
    predict_next_price,
    predict_future_price,  # 新增多步預測函數
    adjust_prediction_with_memory,
    analyze_prediction_error,
    ensemble_prediction,
    time_series_cross_validation
)
from stock_ai_analysis.news_analysis import get_stock_news, analyze_news_sentiment, detect_fake_news
from stock_ai_analysis.report_generator import generate_report, email_report
from stock_ai_analysis.email_sender import send_email
from stock_ai_analysis.error_analysis import record_error
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

def load_stock_list(file_path="stocks.csv"):
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        logging.error(f"讀取股票清單失敗: {e}")
        return pd.DataFrame(columns=["symbol", "category"])

def run_report_main():
    logging.info("開始產生報告")
    stock_list = load_stock_list()
    report_data = []

    try:
        with open("ai_brain.json", "r", encoding="utf-8") as f:
            ai_memory = json.load(f)
    except Exception as e:
        logging.warning("AI 記憶庫不存在或讀取失敗，將以空資料處理")
        ai_memory = {}

    today = pd.Timestamp.today().normalize()

    for idx, row in stock_list.iterrows():
        symbol = row["symbol"]
        category = row["category"]
        try:
            data = get_stock_data(symbol)
            if data is None or data.empty:
                raise ValueError(f"{symbol} 沒有數據")
            if "Close" not in data.columns:
                raise ValueError(f"{symbol} 缺少 'Close' 欄位")
            logging.info(f"開始處理 {symbol} ...")
            data = add_technical_indicators(data)

            # 使用全部數據訓練模型
            model_short = train_model_for_stock(symbol, data, window=10)
            model_long = train_model_for_stock(symbol, data, window=50)

            # 利用新函數預測未來第 10 天和第 50 天股價
            predicted_price_day10 = predict_future_price(model_short, data, horizon=10, window=10)
            predicted_price_day50 = predict_future_price(model_long, data, horizon=50, window=50)

            # 從最近 100 天中取後 50 天作為驗證數據，並獲取第 10 天（索引9）與最後一天（第50天）的實際股價
            if len(data) >= 100:
                validate_data = data.iloc[-50:]
                actual_price_day10 = validate_data["Close"].iloc[9]   # 第10天
                actual_price_day50 = validate_data["Close"].iloc[-1]    # 第50天
            else:
                actual_price_day10 = None
                actual_price_day50 = None

            if actual_price_day10 is not None and actual_price_day50 is not None:
                error_day10 = abs(actual_price_day10 - predicted_price_day10)
                error_day50 = abs(actual_price_day50 - predicted_price_day50)
            else:
                error_day10 = None
                error_day50 = None

            # 給出原因說明
            if error_day10 is not None and error_day10 > 5:
                reason_day10 = f"第10天預測誤差過大（誤差={error_day10:.2f}），可能受短期市場波動影響。"
            else:
                reason_day10 = "第10天預測準確。"

            if error_day50 is not None and error_day50 > 5:
                reason_day50 = f"第50天預測誤差過大（誤差={error_day50:.2f}），可能因長期趨勢變化及資料延遲導致。"
            else:
                reason_day50 = "第50天預測準確。"

            # 其餘原有預測（短期預測、新聞情緒、集成預測等）
            headlines = get_stock_news(symbol)
            news_sentiment = analyze_news_sentiment(headlines)
            news_headlines = "; ".join(headlines)
            latest_close = data["Close"].iloc[-1]
            current_error = abs(latest_close - predict_next_price(model_short, data, window=10))
            error_analysis = "無重大誤差" if current_error <= 5 else f"短期預測誤差: {current_error:.2f}"
            from textblob import TextBlob
            news_validity = not (len(headlines) > 0 and max([abs(TextBlob(h).sentiment.polarity) for h in headlines]) > 0.9) if headlines else True
            market_volatility = 1.0
            if current_error > 5:
                reason = f"短期預測誤差過大，誤差={current_error:.2f}。"
                analyze_prediction_error(symbol, latest_close, predict_next_price(model_short, data, window=10),
                                         error_threshold=5, market_volatility=market_volatility,
                                         news_factor=(1.0 if news_validity else 2.0))
                record_error(category, symbol, "10天", latest_close, predict_next_price(model_short, data, window=10), reason)
                error_analysis = reason

            losses, avg_cv_loss = time_series_cross_validation(symbol, data, window=10, n_splits=3)

            report_data.append({
                "symbol": symbol,
                "category": category,
                "latest_close": latest_close,
                "predicted_price_day10": predicted_price_day10,
                "actual_price_day10": actual_price_day10,
                "error_day10": error_day10,
                "reason_day10": reason_day10,
                "predicted_price_day50": predicted_price_day50,
                "actual_price_day50": actual_price_day50,
                "error_day50": error_day50,
                "reason_day50": reason_day50,
                "ensemble_prediction": ensemble_prediction(symbol, data, window=10, n_models=3),
                "error_current": current_error,
                "news_sentiment": news_sentiment,
                "news_headlines": news_headlines,
                "error_analysis": error_analysis,
                "training_count": len(ai_memory.get(symbol, [])),
                "avg_cv_loss": avg_cv_loss,
                "Report_Time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            logging.info(f"{symbol} 分析完成")
        except Exception as inner_e:
            logging.error(f"Error processing {symbol}: {str(inner_e)}")
            continue

    report_path = generate_report(report_data)
    logging.info("報告生成完成")
    email_report(report_path)

if __name__ == "__main__":
    run_report_main()
