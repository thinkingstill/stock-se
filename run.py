import akshare as ak
import pandas as pd
import sys
import time

TODAY_STR = time.strftime("%Y%m%d", time.localtime())

def get_exchange_date():
    '''
        获取数据最新的交易时间
    '''
    sse_info = ak.stock_sse_summary()
    return sse_info.loc[ sse_info['项目'] == '报告时间', '股票'].values[0]

def get_exchange(code):
    '''
        处理交易所
    '''
    if code.startswith('688'):
        return '上海证券交易所科创板'
    elif code.startswith('920'):
        return '北京证券交易所'
    elif code.startswith('689'):
        return '上海证券交易所科创板（CDR公司）'
    elif code.startswith('600') or code.startswith('601') or code.startswith('603') or code.startswith('605'):
        return '上海证券交易所主板'
    elif code.startswith('000'):
        return '深圳证券交易所主板'
    elif code.startswith('001') or code.startswith('002'):
        return '深圳证券交易所中小板'
    elif code.startswith('003'):
        return '深圳证券交易所创业板'
    elif code.startswith('300') or code.startswith('301'):
        return '深圳证券交易所创业板'
    elif code.startswith('8'):
        return '北京证券交易所'
    elif code.startswith('430'):
        return '新三板'
    else:
        return '无法识别的股票代码'

def get_total_industry_stock():
    '''
        获取行业明细
    '''
    stock_board_industry_name_em_df = ak.stock_board_industry_name_em()
    total_df = []
    for row in stock_board_industry_name_em_df.itertuples():
        print(f'当前开始处理板块{row.板块名称}')
        try:
            tmp_df = ak.stock_board_industry_cons_em(symbol=f"{row.板块名称}")
            tmp_df['产业板块'] = row.板块名称
        except Exception as e:
            print(f'当前处理板块{row.板块名称}失败')
            continue
        total_df.append(tmp_df)
        print(f'当前处理板块{row.板块名称}成功')
    return pd.concat(total_df)

def get_total_stock_info(total_industry_df):
    '''
        获取股票基础静态信息
    '''
    stock_info = []
    for row in total_industry_df.itertuples():
        print(f'当前开始处理股票{row.代码}')
        try:
            tmp_df = ak.stock_individual_info_em(symbol=f"{row.代码}")
        except Exception as e:
            print(f'当前处理股票{row.代码}失败')
            continue
        stock_info.append(tmp_df)
        print(f'当前处理股票{row.代码}成功')
    stock_detail_df = pd.concat([ df.set_index('item').T for df in stock_info])
    stock_detail_df.reset_index(drop=True,inplace=True)
    stock_detail_df['交易所'] = stock_detail_df['股票代码'].apply(lambda x : get_exchange(x))
    return stock_detail_df[['股票代码', '股票简称', '上市时间', '总股本', '流通股', '行业', '交易所']]

def get_xueqiu_hot():
    '''
        获取雪球每天关注、评论、交易热度数据
    '''
    follow_df = ak.stock_hot_follow_xq(symbol="最热门")
    tweet_df = ak.stock_hot_tweet_xq(symbol="最热门")
    tweet_df.rename(columns={'关注':'讨论'}, inplace=True)
    deal_df = ak.stock_hot_deal_xq(symbol="最热门")
    deal_df.rename(columns={'关注':'交易'}, inplace=True)
    merge_df = pd.merge(follow_df, tweet_df, on=['股票代码', '股票简称', '最新价'])
    final_df = pd.merge(merge_df, deal_df, on=['股票代码', '股票简称', '最新价'])
    return final_df

if __name__ == "__main__":
    
    # 执行命令
    opt = sys.argv[1]

    # 判断当前日是否是交易日
    LATEST_EXCHAGE_DATE = get_exchange_date()
    if TODAY_STR != LATEST_EXCHAGE_DATE:
        print('今天非交易日!')
    if opt == "daily":
        # 获取今日行情数据
        stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
        stock_zh_a_spot_em_df['date'] = LATEST_EXCHAGE_DATE
        with open(f'stock_daily_{LATEST_EXCHAGE_DATE}.json', 'w', encoding='utf-8') as f:
            f.write(stock_zh_a_spot_em_df.to_json(orient='records', force_ascii=False))
        
        # 获取雪球每日热度数据
        stock_hot_xueqiu_df = get_xueqiu_hot()
        stock_hot_xueqiu_df['date'] = LATEST_EXCHAGE_DATE
        with open(f'hot_daily_{LATEST_EXCHAGE_DATE}.json', 'w', encoding='utf-8') as f:
            f.write(stock_hot_xueqiu_df.to_json(orient='records', force_ascii=False))
