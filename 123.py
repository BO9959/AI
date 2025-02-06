from stock_ai_analysis.data_collector import get_stock_data



# 下載 AAPL 股票數據，時間範圍 10 年，每日資料
df = get_stock_data("AAPL", period="10y", interval="1d")

# 檢查是否成功下載
if df is not None:
    print(df.head())
else:
    print("❌ AAPL 數據下載失敗！")
