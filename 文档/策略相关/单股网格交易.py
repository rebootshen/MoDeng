# 克隆自聚宽文章：https://www.joinquant.com/post/25363
# 标题：一个简单的单股网格交易回测程序
# 作者：wwj12000183

#2005年以前退市的股票填入会报错,如000003.XSHE这个股票2002年退市,填入会报错.
#本源码基准就是股票自己.
#顶仓 和初始资金设的太小可能会影响运行结果.第一遍建议设大一点.  请自行体会.
#建议第一遍先填一个大的初始资金和顶仓.第二遍参考日志结尾"最大使用资金"改初始资金.

def initialize(context):  #initialize 始化函数  context对象
    g.security = '002065.XSHE'   #设定股票代码
    set_benchmark(g.security)  #设置自己为基准
    run_daily(first_day, time='09:30') #first_day函数每天9.30运行,在函数内另行设定实际只运行一次
    g.b=0    #用于执行第一次建底仓时累加用
    g.退市取消=False
    g.停牌取消=False
    判断退市=str(get_security_info(g.security).end_date) #取得退市日期 并转换为字符串
    c="2200-01-01"  #没退市的股票  获取的退市日期是2200-01-01
    if 判断退市!=c: #判断股票是否退市,对2005年以后退市的股票有效如000033.XSHE有效,
        print("这是个退市股票,请换一个\n"*10)
        g.退市取消=True #退市取消
g.最大使用资金=0 #这个不用改,不要改
g.达到的最大仓位=0  #这个不用改,不要改

#--------下面是需要自定义的数据,上面第7行的股票代码也要改---------
#-------------------------------------------------------------
单次卖量 = -5000    #这个是负数，填-100的整数倍
单次买量=5000    #填100的整数倍
初仓=5000       #刚开始第一天买入的仓位
底仓=10000       #用于保留最小的仓位 底仓要小于顶仓
顶仓=50000      #用于限制最高持仓股数 顶仓要大于底仓
上涨多少卖出 = 0.80  #输入小数如0.05是表示5%   输入正数
下跌多少买入 = -0.40   #输入小数如0.05是表示5%  输入负数,负数,负数
#---------------------------------------------------------


#下面这个自定义函数用途是回测第一天买入底仓
def  first_day(context):
    if g.退市取消==True :return   #判断退市直接跳出函数,不再执行下面代码
    if g.b ==0:    #判断是之前没有买入过底仓,则运行
        初始底仓=order(g.security,初仓)  #买入底仓
        if 初始底仓==None:  #如果买入失败
            g.停牌取消=True     #就当停牌处理,当,当,当
            return    #停牌直接跳出函数,不再执行下面代码,等下个复牌日
        g.b=g.b+1    #建底仓成功后数值加1
        成交价=初始底仓.price   #获取成交价
        g.基准价格=初始底仓.price #每次的成交价都是新的基准
        成交数=初始底仓.amount #获取成交数量
        my_print(初始底仓,context,0)  #自定义的显示函数
       

       

#下面这个循环函数判断价格涨跌的百分比而买卖
def handle_data(context, data):  #这是聚宽自带函数
    if g.退市取消 or g.停牌取消==True : return  #判断退市或者停牌直接跳出函数,不再执行下面代码
    最新行情价=context.portfolio.positions[g.security].price   #如变量名
    基准涨跌幅=(最新行情价-g.基准价格)/g.基准价格  #算一下上次交易后的涨跌幅
    可卖出的仓=context.portfolio.positions[g.security].closeable_amount #如变量名
    今天开的仓=context.portfolio.positions[g.security].total_amount #如变量名
    底仓判断 = 今天开的仓 > 底仓 and 可卖出的仓!=底仓  #判断有没有到达底仓
    
    #以下是卖出
    #满足3个条件才能卖出  1.涨幅达到设置的百分百才能卖出 2.当天买入不能卖出  3.达到底仓不卖出
    if (基准涨跌幅 >= 上涨多少卖出)and (可卖出的仓>abs(单次卖量)) and 底仓判断  :
        # print("卖出")
        成交数据=order(g.security,my_ft(0,可卖出的仓,底仓,单次卖量))  #卖出 卖出量用my_ft函数判断
        g.基准价格=成交数据.price  #更新基准价格
        my_print(成交数据,context,data) #自定义的显示函数
     
    #以下是买入
    if (最新行情价-g.基准价格)/g.基准价格 <= 下跌多少买入:
        资金够=context.portfolio.available_cash > (最新行情价*单次买量)
        仓位有=顶仓-g.当前仓位>=100 #离顶仓可买仓位大于等于100时,返回真,否则返回假
        if 仓位有==False:return# 达到设定的顶仓 就不买了
        if 资金够 and 仓位有: #买入前判断可以资金够不够
            # print("买入")
            成交数据=order(g.security,my_ft(1,顶仓,单次买量,g.当前仓位))  #执行买入,买入的数据存到变量"成交数据"里 买入量用my_ft函数判断
            g.基准价格=成交数据.price  #更新基准价格
            my_print(成交数据,context,data) #自定义的显示函数
        else:
            print("你的资金不够再执行一次买入了,请调节资金后再来\n"*10)
            g.退市取消=1 #资金不够退市取消

        
def my_ft(f,a,b,c):    # 这个函数 判断买卖的数量是否超过顶仓和底仓的限制,如果超过就减少
    if f == 0: #以下判断卖量 (a,b,c 对应 可卖出的仓,底仓,单次卖量
        if a-b>=abs(c) : #正常卖 1500-1000 500     500
            return c #返回单次卖量
        if a-b<abs(c) : #减少卖 1000-1000  0   500
            return b-a #返回减少卖量

    if f == 1 : #以下判断买量 (a,b,c 对应 顶仓,单次买量,g.当前仓位)
        if a-b<=c: #减少买
            return a-c  #返回减少买量
        if a-b>c : #正常买
            return b #返回单次买量
 
 
def my_print(成交数据,context,data):#这是自定义的打印数据函数
    if g.退市取消 or g.停牌取消 == True :return  #判断退市或者停牌直接跳出函数,不再执行下面代码
    g.股票名称= get_security_info(g.security).display_name
    成交代码=成交数据.security
    成交价=成交数据.price
    g.成交价=成交数据.price
    成交数=成交数据.amount
    a=成交数据.is_buy
    if a == False:
        买卖="卖出"
    else:
        买卖="买入"
    # def fffhandle_data(context,data):
    初始资金=context.portfolio.starting_cash
    可用资金=round(context.portfolio.available_cash, 2) #round(a, 2)保留2位小数
    g.当前仓位=context.portfolio.positions[g.security].total_amount
    单股均价=context.portfolio.positions[g.security].acc_avg_cost
    单股均价=round(context.portfolio.positions[g.security].acc_avg_cost, 2) #round(a, 2)保留2位小数
    账户持仓价值=context.portfolio.positions_value

    if g.当前仓位>g.达到的最大仓位:    #算最大资金利用量
        g.达到的最大仓位=g.当前仓位    #算最大资金利用量
    if g.最大使用资金<(初始资金-可用资金):   #算最大仓位利用量
        g.最大使用资金=初始资金-可用资金     #算最大仓位利用量
        
    print ('=======================================================================================')
    print('{0}*{1}*{2}元*{3}{4}股   现有{5}股 均价{6} 更新基准价为{7} 价值{8}元,可用资金{9}'.format(成交代码,g.股票名称,成交价,买卖,成交数,g.当前仓位,单股均价,g.基准价格,账户持仓价值,可用资金))#打印price本次成交价
    #打印price本次成交的各种数据
    print ('=======================================================================================')

def on_strategy_end(context):   #这个代码功能是 回测结束后做个统计
    初始资金=context.portfolio.starting_cash
    print('初始资金{0},最大使用资金{1},达到的最大仓位{2}'.format(初始资金,round(g.最大使用资金, 2),g.达到的最大仓位))