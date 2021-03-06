# 克隆自聚宽文章：https://www.joinquant.com/post/16351
# 标题：指数择时与仓位管理策略初探
# 作者：跟随哔哔做量化

# 导入函数库
from jqdata import *
import talib as tb
import statsmodels.api as sm

# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('002065.XSHE')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    # 过滤掉order系列API产生的比error级别低的log
    log.set_level('order', 'error')
    
    set_params(context)
    log.info('aaaaaaaaaaa')
    set_tutle_params(context)
    log.info('bbbbbbbbbbb')
    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')

    ## 运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'000300.XSHG'或'510300.XSHG'是一样的）
    # # 开盘前运行
    # run_daily(before_trading_start, time='', reference_security='000300.XSHG')
    # 开盘时运行
    run_daily(market_open, time='open', reference_security='000300.XSHG')

#每天开盘前要做的事情
def before_trading_start(context):
    set_slip_fee(context) 
    


#4 根据不同的时间段设置滑点与手续费
def set_slip_fee(context):
    # 将滑点设置为0
    set_slippage(FixedSlippage(0)) 
    # 根据不同的时间段设置手续费
    dt=context.current_dt
    
    if dt>datetime.datetime(2013,1, 1):
        set_commission(PerTrade(buy_cost=0.0003, sell_cost=0.0013, min_cost=5)) 
        
    elif dt>datetime.datetime(2011,1, 1):
        set_commission(PerTrade(buy_cost=0.001, sell_cost=0.002, min_cost=5))
            
    elif dt>datetime.datetime(2009,1, 1):
        set_commission(PerTrade(buy_cost=0.002, sell_cost=0.003, min_cost=5))
                
    else:
        set_commission(PerTrade(buy_cost=0.003, sell_cost=0.004, min_cost=5))

def set_params(context):
    g.security = '002065.XSHE'
    # 设置RSRS指标中N, M的值
    #统计周期
    g.N = 18
    #统计样本长度
    g.M = 1100
    #首次运行判断
    g.init = False
    # 买入阈值
    g.buy = 0.7
    g.sell = -0.7
    #用于记录回归后的beta值，即斜率
    g.ans = []
    #用于计算被决定系数加权修正后的贝塔值
    g.ans_rightdev= []
    # 计算2005年1月5日至回测开始日期的RSRS斜率指标
    # 获得回测前一天日期，千万避免未来数据
    log.info('aaaaaaaaaaa1')
    previous_date = context.current_dt - datetime.timedelta(days=2)
    log.info('aaaaaaaaaaa2')
    prices = get_price(g.security, '2020-01-05', previous_date, '1d', ['high', 'low'])
    highs = prices.high
    lows = prices.low
    g.ans = []
    log.info('aaaaaaaaaaa3')
    for i in range(len(highs))[g.N:]:
        data_high = highs.iloc[i-g.N+1:i+1]
        data_low = lows.iloc[i-g.N+1:i+1]
        X = sm.add_constant(data_low)
        log.info(i)
        model = sm.OLS(data_high,X)
        results = model.fit()
        g.ans.append(results.params[1])
        #计算r2
        g.ans_rightdev.append(results.rsquared)
    log.info('aaaaaaaaaaa-finish')

def set_tutle_params(context):
    # 系统的突破价格
    g.break_price = 0
    # 系统建的仓数
    g.sys = 0
    # 最大允许单元
    g.unit_limit = 4
    # 定义当前的仓位水平
    g.position_level = 0
    # ATR倍数
    g.ceof = 0.5

def ATR(high, low, close, pos):
    atrValue = tb.ATR(high, low, close, timeperiod=14)[-1]
    # 绝对波动幅度=N*合约每一点所代表的价值
    # 由于是现货，合约每一点所代表的价值就是指数代表的价值
    absAtr =  atrValue * 1
    unit = 0.01*pos/absAtr
    amount = unit * close[-1]   # 取目标价值就不需要之前乘以指数价值
    return atrValue, unit, amount

## 开盘时运行函数
def market_open(context):
    security = g.security
    # 获取股票的收盘价
    price_data = get_bars(security, count=20, unit='1d', fields=['close','high','low'])
    total_value = context.portfolio.total_value
    atr,vol, amount= ATR(price_data['high'],price_data['low'],price_data['close'],total_value)
    # vol, amount = total_value/(4*price_data['close'][-1]), int(total_value/4)  # 固定比例
    log.info('总价值',total_value)
    log.info('ATR控制的仓位值',amount)
    # 填入各个日期的RSRS斜率值
    beta=0
    r2=0
    if g.init:
        g.init = False
    else:
        #RSRS斜率指标定义
        prices = attribute_history(security, g.N, '1d', ['high', 'low'])
        highs = prices.high
        lows = prices.low
        X = sm.add_constant(lows)
        model = sm.OLS(highs, X)
        beta = model.fit().params[1]
        g.ans.append(beta)
        #计算r2
        r2=model.fit().rsquared
        g.ans_rightdev.append(r2)
    # 计算标准化的RSRS指标
    section = g.ans[-g.M:]
    # 计算均值序列
    mu = np.mean(section)
    # 计算标准化RSRS指标序列
    sigma = np.std(section)
    zscore = (section[-1]-mu)/sigma  
    #计算右偏RSRS标准分
    zscore_rightdev= zscore*beta*r2
    
    # 当前的价格
    current_price = get_current_data()[g.security].last_price  # 当前价格N
    price_base = max(attribute_history(g.security, 20, '1d', ('close'))['close'])

    # 如果上一时间点的RSRS斜率大于买入阈值, 则开仓买入
    if (zscore_rightdev > g.buy ) and g.sys == 0:  #or current_price > price_base
        
        # 记录这次买入
        log.info("市场风险在合理范围，买入")
        #满足条件运行交易
        order_value(security,amount)
        # order_target_value(security,total_value)
        g.sys += int(vol)   
        g.break_price = current_price
        g.top_price = current_price
        g.position_level += 1
        
    elif zscore_rightdev > g.buy and g.sys != 0:

        if current_price >= g.break_price + 0.1*g.ceof*(atr) and g.position_level <= g.unit_limit-1:
            
            # 记录这次买入
            log.info("市场风险在合理范围，加仓")
            #满足条件运行交易
            order_value(security, int(vol*current_price))
            g.sys += int(vol)
            g.position_level += 1
            g.break_price = g.break_price + 0.1*g.ceof*(atr)
        elif current_price <= g.break_price - g.ceof*(atr) and g.position_level >= 1:
            
            # 记录这次买入
            log.info("市场风险在合理范围，减仓")
            #满足条件运行交易
            order_value(security, -int(vol*current_price))
            g.sys -= int(vol)
            g.position_level -= 1
            g.break_price = g.break_price - g.ceof*(atr)
    # 如果上一时间点的RSRS斜率小于卖出阈值, 则平仓卖出
    elif (zscore_rightdev < g.sell) and (len(context.portfolio.positions.keys()) > 0):
        # 记录这次卖出
        log.info("市场风险过大，平仓卖出")
        # 卖出所有股票,使这只股票的最终持有量为0
        for s in context.portfolio.positions.keys():
            order_target(security, 0)
            # 清仓后，计数器和突破的价格归零
            g.break_price = 0
            g.sys = 0
            g.position_level = 0
    # 仓位画图展示
    position_last = context.portfolio.available_cash
    position_last_pct = 1-position_last/context.portfolio.total_value
    record(name=position_last_pct)

