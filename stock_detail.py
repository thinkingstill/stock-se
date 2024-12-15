import tqdm
import pandas as pd
import akshare as ak
stock_basic_info = pd.read_pickle('./disk/stock_basic_info.pkl')

totla_stock_range = []
for idx in tqdm.tqdm(range(stock_basic_info.shape[0])):
    code = stock_basic_info.loc[idx, '股票代码']
    try:
        tmp_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20240923", end_date='20241215', adjust="")
    except Exception as e:
        continue
    totla_stock_range.append(tmp_df)
totla_stock__df = pd.concat(totla_stock_range)
merged_df = pd.merge(totla_stock__df, stock_basic_info, on='股票代码', how='left')
merged_df.to_pickle('./disk/stock_deital_09231215.pkl')
