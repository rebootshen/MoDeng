# 克隆自聚宽文章：https://www.joinquant.com/post/27235
# 标题：基于机器学习优化的时间网格交易模型
# 作者：啊卫

# 克隆自聚宽文章：https://www.joinquant.com/post/539
# 标题：【网格交易策略-年化30%+】-网格大法好，熊市不用跑~
# 作者：陈小米。
import numpy as np
import numpy
import pandas as pd
from pandas import Series
def initialize(context):
    #运行天数
    g.day=0
    #股票个数
    g.count = 30
    #资本总额
    g.cash = 1000000
    #时间间隔
    g.interval=4
    #购买的股票池
    g.buy_stock = []
    #底仓价数组
    g.initial_price = {}
    #当前交易月数
    g.month = context.current_dt.month
    #每个月交易一次选股票函数
    run_monthly(select_stock_by_industry,1,'open')
    '''
    X_trainval = np.matrix([[1],[2],[3],[4],[5],[6]])
    y_trainval = np.matrix([[11],[17],[29],[42],[24],[23]])
   #支持线性向量机
   # from sklearn.svm import SVR
    #model = SVR(C=100, gamma=1)
   #线性回归 
    #from sklearn.linear_model import LinearRegression
    #model = LinearRegression()
    #岭回归
    #from sklearn.linear_model import Ridge
    #model = Ridge(random_state=60,alpha=200)
   #随机森林
    from sklearn.ensemble import RandomForestRegressor
    model = RandomForestRegressor(random_state=42,n_estimators=500,n_jobs=-1)
    # 拟合训练集，生成模型
    model.fit(X_trainval,y_trainval)
    # 预测值
    a = 1 
    ma =0
    mb =0
    while a < 365:
        y_pred = model.predict(a)
        if(ma<y_pred):
            ma=y_pred
            mb=a
        a=a+1
    print ('---------------------------------------------------------------------------')
    print (ma) 
    print (mb)
    g.interval=mb
    '''
# 选股
# 重点行业，低估值PE小，优质蓝筹市值大，高波动
def select_stock_by_industry(context):
    #每3个月更新
    month = context.current_dt.month
    if month%3 != g.month%3:
        return
    industry_list = [
    #'000300.XSHG'
    'C27','C39','I63',
    'I64','I65',
    'K70',
    'M73','M74',
    'N77','R86','R87'
    ]
    stocks = []
    for industry_code in industry_list:
        stock_set = get_industry_stocks(industry_code)
        #选fundamental比较好的前15只,pe_ration<30，market_cap，按market_cap取后20只股票。
        q = query(
            valuation.code, valuation.market_cap, valuation.pe_ratio
        ).filter(
            valuation.code.in_(stock_set),
            valuation.pe_ratio < 50
        ).order_by(
            valuation.market_cap.desc()
        ).limit(
        g.count
        )
        df = get_fundamentals(q)
        stock_set = list(df['code'])
        #取波动率最高的2只
        variance_list = []
        for stock in stock_set:
            variance_list.append(variance(stock))
        s1 =Series(variance_list,index = stock_set).rank()
        stocks = list(s1[s1 < 6].index)
        for stock in stocks:
            g.buy_stock.append(stock)
            g.initial_price[stock]=0
    set_universe(g.buy_stock)
    reset_position(context)
    return None
# 轮换选股后清除新股票池外的持仓
def reset_position(context):
    if context.portfolio.positions.keys() !=[]:
        for stock in context.portfolio.positions.keys():
            if stock not in g.buy_stock:
                order_target_value(stock, 0)
    return None
# 计算波动率
def variance(security_code):
    hist1 = attribute_history(security_code, 180, '1d', 'close',df=False)
    narray=numpy.array(hist1['close'])
    sum1=narray.sum()
    narray2=narray*narray
    sum2=narray2.sum()
    N = len(hist1['close'])
    mean=sum1/N
    var=sum2/N-mean**2
    return var

# 计算股票前n日收益率
def security_return(days,security_code):
    hist1 = attribute_history(security_code, days + 1, '1d', 'close',df=False)
    security_returns = (hist1['close'][-1]-hist1['close'][0])/hist1['close'][0]
    return security_returns

# 止损，根据前n日收益率
def conduct_nday_stoploss(context,security_code,days,bench):
    if  security_return(days,security_code)<= bench:
        for stock in g.buy_stock:
            order_target_value(stock,0)
            log.info("Sell %s for stoploss" %stock)
        return True
    else:
        return False
# 计算股票累计收益率（从建仓至今）
def security_accumulate_return(context,data,stock):
    current_price = data[stock].price
    cost = context.portfolio.positions[stock].avg_cost
    if cost != 0:
        return (current_price-cost)/cost
    else:
        return None

# 个股止损，根据累计收益
def conduct_accumulate_stoploss(context,data,stock,bench):
    if security_accumulate_return(context,data,stock) != None\
    and security_accumulate_return(context,data,stock) < bench:
        order_target_value(stock,0)
        log.info("Sell %s for stoploss" %stock)
        return True
    else:
        return False

# 选股：连续N日下跌
def is_fall_nday(days,stock):
    his = history(days+1,'1d','close',[stock],df =False)
    cnt = 0
    for i in range(days):
    	daily_returns = (his[stock][i+1] - his[stock][i])/his[stock][i]
    	if daily_returns <0:
    	    cnt += 1
    if cnt == 5:
    	return True
    else:
        return False

# 比较现价与N日均价
def compare_current_nmoveavg(data,stock,days,multi):
    current_price = data[stock].price
    moveavg = data[stock].mavg(days)
    if current_price > multi * moveavg:
        return True
    else:
        return False

# 初始底仓选择，判断没有initial_price，则建立基准价
def initial_price(context,data,stock):
    if g.initial_price[stock]==0:
        g.initial_price[stock]=data[stock].price
    return None

# 补仓、空仓：分n买入/卖出
def setup_position(context,data,stock,bench,status):
   #底仓价
    bottom_price= g.initial_price[stock]
    if bottom_price == 0:
        return
    #现有资金
    cash = context.portfolio.cash
    #现在的股价
    current_price = data[stock].price
    #现在仓位
    amount = context.portfolio.positions[stock].amount
    #现在的价值
    current_value = current_price*amount
    #总资金分为40份
    unit_value = g.cash/40
    #评判标准；涨幅，跌幅
    returns = (current_price-bottom_price)/bottom_price
    #卖出
    if (status == 'short'):
        if returns > bench and current_value > 6*unit_value:
            order_target_value(stock,6*unit_value)
        if returns > 2*bench and current_value > 3*unit_value:
            order_target_value(stock,3*unit_value)
        if returns > 3*bench and current_value >1*unit_value :
            order_target_value(stock,1*unit_value)
        if returns > 4*bench and current_value >0:
            order_target_value(stock,0)
    # 买入
    if (status == 'long') and cash >0:
        if returns < bench and current_value < 4*unit_value:
            order_target_value(stock,4*unit_value)
        if returns < 2*bench and current_value < 7*unit_value:
            order_target_value(stock,7*unit_value)
        if returns < 3*bench and current_value <9*unit_value :
            order_target_value(stock,9*unit_value)
        if returns < 4*bench and current_value < 10*unit_value:
            order_target_value(stock,10*unit_value)
    return True 

# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context, data):
    # 指数止损，前一天跌幅大于3%
    if conduct_nday_stoploss(context, '000001.XSHG', 2,-0.03):
        return
    g.day=g.day+1
    if(g.day%g.interval!=0):
        return 
    for stock in g.buy_stock:
    	if conduct_accumulate_stoploss(context,data,stock,-0.2):
    	    return
    	#1.连续5日下跌，不操作
    	if is_fall_nday(5,stock):
    		return
    	#2.大于5日平均或10日平均1.5倍以上,不操作
    	if compare_current_nmoveavg(data,stock,5,1.5)\
    	or compare_current_nmoveavg(data,stock,10,1.5):
    		return
    	#初始设置底仓
    	initial_price(context,data,stock)
    	#补仓步长：-3%，-5%，-8%，-12%
    	setup_position(context,data,stock,-0.08,'long')
    	#空仓步长：5%，10%，15%，20%
    	setup_position(context,data,stock,0.15,'short')

