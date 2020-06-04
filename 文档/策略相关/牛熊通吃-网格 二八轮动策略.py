# 克隆自聚宽文章：https://www.joinquant.com/post/27558
# 标题：牛熊通吃，网格+二八轮动策略
# 作者：Jq564264056

from jqdata import *

def initialize(context):
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG') 
    run_daily(market_open, time='every_bar', reference_security='000300.XSHG')
    g.grid=0.03
    g.pestatus = 0
    g.security = '510630.XSHG'
    
    # 二八轮动参数
    g.lag = 20
    g.hour = 14
    g.minute = 53
    g.hs =  '000300.XSHG' #300指数
    g.zz =  '000905.XSHG'#500指数
        
    g.ETF300 = '510300.XSHG'#'510300.XSHG'
    g.ETF500 = '510500.XSHG'#'510500.XSHG'
def before_market_open(context):
    pe,peupper,pelower = pequery(context)
    if pe > peupper:
        g.pestatus = 1
    elif pe < pelower:
        g.pestatus = -1
    else:
        g.pestatus = 0
    
## 开盘时运行函数
def market_open(context):
    if g.pestatus == 1:
        roll28(context)
    else:
        grid_trade(context)

def grid_trade(context):
    security = g.security
    current_data = get_current_data()
    current_price=current_data[security].last_price
    cash = context.portfolio.available_cash
    if len(context.portfolio.positions) == 0:
        g.grid_cash = cash/10  # 可用资金分成10份
        orders=order_value(security, cash*0.5)
        if orders is None:
            print("创建订单失败...")
        else:
            log.info("空仓, 建立底仓，买入{}".format(security))
            g.last_order_price=orders.price
            g.grid_pos=round(orders.amount/5/100)*100  # 将全仓位分成10份
    elif (current_price/g.last_order_price-1 < -g.grid) and (cash > 0):
        orders=order_value(security, g.grid_cash)
        if orders is None:
            print("创建订单失败...")
        else:
            log.info("价格下跌1个网格，买入1份资金：{}".format(security))
            g.last_order_price=orders.price
    elif (current_price/g.last_order_price-1 > g.grid) and context.portfolio.positions[security].closeable_amount >= g.grid_pos:
        orders=order(security, -g.grid_pos)
        if orders is None:
            print("创建订单失败...")
        else:
            log.info("价格上涨1个网格, 卖出1份仓位：{}".format(security))
            g.last_order_price=orders.price
            
'''
----------------------------------------------------------------------------二八轮动代码开始----------------------------------------------------------------------------
'''
def roll28(context):
    signal = get_signal(context)
    if signal == 'sell_the_stocks':
        sell_the_stocks(context)
    elif signal == 'ETF300' or signal == 'ETF500':
        buy_the_stocks(context,signal)

def get_signal(context):
    hs300,cp300 = getStockPrice(g.hs, g.lag)
    zz500,cp500  = getStockPrice(g.zz, g.lag)
    hs300increase = (cp300 - hs300) / hs300
    zz500increase = (cp500 - zz500) / zz500
    hold300 = context.portfolio.positions[g.ETF300].total_amount
    hold500 = context.portfolio.positions[g.ETF500].total_amount
    if (hs300increase<=0 and hold300>0) or (zz500increase<=0 and hold500>0):
        return 'sell_the_stocks'
    elif hs300increase>zz500increase and hs300increase>0 and (hold300==0 and hold500==0):
        return 'ETF300'
    elif zz500increase>hs300increase and zz500increase>0 and (hold300==0 and hold500==0):
        return 'ETF500'

def getStockPrice(stock, interval):
    h = attribute_history(stock, interval, unit='1d', fields=('close'), skip_paused=True)
    return (h['close'].values[0],h['close'].values[-1])

def sell_the_stocks(context):
    for stock in context.portfolio.positions.keys():
        return (log.info("Selling %s" % stock), order_target_value(stock, 0))

def buy_the_stocks(context,signal):
    return (log.info("Buying %s"% signal ),order_value(eval('g.%s'% signal), context.portfolio.cash))
    
    
'''
----------------------------------------------------------------------------二八轮动代码结束----------------------------------------------------------------------------
'''


def selectstock(context,count):
    security_list = get_index_stocks('000300.XSHG')
    security_list = paused_filter(security_list)
    security_list = get_PEG(security_list)
    security_list = list(security_list[security_list['pe']<0.5]['code'].values)
    security_list = get_std(context,security_list,count)
    log.info(security_list)
    g.security_list = security_list
    
    
def pequery(context):
    q=query(finance.STK_EXCHANGE_TRADE_INFO).filter(
            finance.STK_EXCHANGE_TRADE_INFO.date <= context.previous_date,
            finance.STK_EXCHANGE_TRADE_INFO.exchange_code == '322002',
        ).order_by(finance.STK_EXCHANGE_TRADE_INFO.date.desc()).limit(3000)
    df=finance.run_query(q)
    DF = df[['pe_average']]
    DF = DF.copy()
    DF['V'] = DF.apply(lambda x: np.log10(x.pe_average),axis=1)
    pe = DF['V'].values[0]
    peupper = DF['V'].median() + DF['V'].std() * 0.05
    pelower = DF['V'].median() - DF['V'].std() * 0.25
    return pe,peupper,pelower
    
def paused_filter(security_list):
    current_data = get_current_data()
    security_list = [stock for stock in security_list if not current_data[stock].paused]
    security_list = [x for x in security_list if x[0:3] != '688']
    security_list = [x for x in security_list if x[0:3] != '300']
    return security_list
    
def get_std(context,stocks,count):
    dic = {'code':[],'stds':[]}
    dataprices = get_bars(stocks, end_dt=context.previous_date,fields=['close','low'], count=10)
    for s in stocks:
        if dataprices[s]['close'][-1] < dataprices[s]['low'].mean():
            dic['code'].append(s)
            dic['stds'].append(dataprices[s]['close'].std())
    stocklist = pd.DataFrame(dic).sort_values(by="stds" , ascending=False)[0:count]
    return list(stocklist['code'].values)
    
def get_PEG(stock_list): 
    q_PE_G = query(valuation.code, valuation.pe_ratio, indicator.inc_net_profit_year_on_year
                 ).filter(valuation.code.in_(stock_list)) 
    df_PE_G = get_fundamentals(q_PE_G)
    df_Growth_PE_G = df_PE_G[(df_PE_G.pe_ratio >0)&(df_PE_G.inc_net_profit_year_on_year >0)]
    df_Growth_PE_G.dropna()
    Series_PE = df_Growth_PE_G.ix[:,'pe_ratio']
    Series_G = df_Growth_PE_G.ix[:,'inc_net_profit_year_on_year']
    Series_PEG = Series_PE/Series_G
    Series_PEG.index = df_Growth_PE_G.ix[:,0]
    df_PEG = pd.DataFrame(Series_PEG)
    code = df_PEG.index.values
    pe = df_PEG.values 
    dic = {'code':code,'pe':pe.reshape(pe.shape[0])}
    stocks = pd.DataFrame(dic).sort_values(by="pe", ascending=True)
    return stocks