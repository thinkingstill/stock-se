import akshare as ak
import pandas as pd
import plotly.express as px
import json
import sys
import os
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

def min_max_normalize(column):
    '''
        最大最小归一化函数
    '''
    return round(((column - column.min()) / (column.max() - column.min()))*100, 1)

if __name__ == "__main__":
    
    # 执行命令
    opt = sys.argv[1]

    # 判断当前日是否是交易日
    LATEST_EXCHAGE_DATE = get_exchange_date()
    if TODAY_STR != LATEST_EXCHAGE_DATE:
        print(f'今天({TODAY_STR})非交易日!')
        sys.exit()
    if opt == "daily":
        # 获取今日行情数据
        stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
        stock_zh_a_spot_em_df['date'] = LATEST_EXCHAGE_DATE
        with open(f'stock_daily_{LATEST_EXCHAGE_DATE}.json', 'w', encoding='utf-8') as f:
            f.write(stock_zh_a_spot_em_df.to_json(orient='records', force_ascii=False))
        
        # 获取雪球每日热度数据
        stock_hot_xueqiu_df = get_xueqiu_hot()
        stock_hot_xueqiu_df['date'] = LATEST_EXCHAGE_DATE
        stock_hot_xueqiu_df_valid = stock_hot_xueqiu_df.query('关注.notna() and 讨论.notna() and 交易.notna()')
        ## 匹配行业信息
        industry_mapping = json.load(open('disk/industry_mapping.json'))
        stock_hot_xueqiu_df_valid['行业'] = stock_hot_xueqiu_df_valid['股票代码'].apply(lambda x : industry_mapping.get(x[-6:], '缺失'))
        stock_hot_xueqiu_df_valid['涨跌幅'] = stock_hot_xueqiu_df_valid['股票简称'].apply(lambda x : stock_zh_a_spot_em_df.query(f'名称 == "{x}"')['涨跌幅'].values[0] if len(stock_zh_a_spot_em_df.query(f'名称 == "{x}"')['涨跌幅'].values) > 0 else stock_zh_a_spot_em_df['涨跌幅'].min() - 0.1)
        stock_hot_xueqiu_df_valid.rename(columns={
            '关注' : '关注_r',
            '讨论' : '讨论_r',
            '交易' : '交易_r',
            '涨跌幅' : '涨跌幅_r'
        }, inplace = True)
        stock_hot_xueqiu_df_valid['关注'] = min_max_normalize(stock_hot_xueqiu_df_valid['关注_r'])
        stock_hot_xueqiu_df_valid['讨论'] = min_max_normalize(stock_hot_xueqiu_df_valid['讨论_r'])
        stock_hot_xueqiu_df_valid['交易'] = min_max_normalize(stock_hot_xueqiu_df_valid['交易_r'])
        stock_hot_xueqiu_df_valid['涨跌幅'] = min_max_normalize(stock_hot_xueqiu_df_valid['涨跌幅_r'])
        ## 保存json数据
        with open(f'hot_daily_{LATEST_EXCHAGE_DATE}.json', 'w', encoding='utf-8') as f:
            f.write(stock_hot_xueqiu_df_valid.to_json(orient='records', force_ascii=False))
        
        # 生成3D可视化图片
        ## 添加散点图轨迹
        print('开始执行可视化')
        fig = px.scatter_3d(
            stock_hot_xueqiu_df_valid,
            x='关注',
            y='讨论',
            z='涨跌幅',
            color = '行业',
            hover_name = '股票简称',
            title='A股每日热度')
        # 自定义 scene 和布局
        fig.update_layout(
            scene=dict(
                xaxis_title='关注',
                yaxis_title='讨论',
                zaxis_title='涨跌幅'
            )
        )
        fig.update_traces(
            marker=dict(opacity=0.7),
            customdata=stock_hot_xueqiu_df_valid[['关注_r', '讨论_r', '涨跌幅_r', '行业']],
            hovertemplate=(
                "名称: %{hovertext}<br>"
                "关注: %{customdata[0]}<br>"
                "讨论: %{customdata[1]}<br>"
                "涨跌幅: %{customdata[2]}<br>"
                "行业: %{customdata[3]}<extra></extra>" 
            )
            )

        print('可视化完成')
        today_viz_file = f'stock_hot_vis_{LATEST_EXCHAGE_DATE}.html'
        fig.write_html(today_viz_file)
        print(f'是否存在html文件{os.path.exists(today_viz_file)}')
