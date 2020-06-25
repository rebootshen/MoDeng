import easytrader
import json
import os
from Global_Value.file_dir import yh_client_file_url, easytrader_record_file_url
from SDK.Debug_Sub import debug_print_txt
import pprint

class RealTrade:
    def __init__(self):
        self.user = easytrader.use('yh_client')
        self.user.prepare(yh_client_file_url)
        self.current_record = {}
        self.today_done = {}
        self.opt_dict_init = {
            'b_opt': [],
            's_opt': [],
            'usable_balance': 0,
            'has_flashed_flag': True
        }

    def check_status(self):
        #result = self.user.balance()
        #print(result)
        #debug_print_txt('main_log', '', str(result[0]) + ' \n inside check_status \n',True)
        return_str = []
        today_opt = []
        return_str = self.user.position   # Don't add (), otherwise will cause error!
        pprint.pprint(return_str)

        today_opt = self.user.today_entrusts
        print("today_opt:" + str(today_opt))  

        self.today_done = self.user.today_trades
        print("today_done:" + str(self.today_done))  

        length = len(return_str)
        for i in range(length):
            stk_code = return_str[i]['证券代码']
            amount = return_str[i]['可用余额']
            #print(stk_code)
            #print(amount)
            self.current_record[stk_code] = {}
            self.current_record[stk_code]['usable_balance'] = amount
        pprint.pprint(self.current_record)
        #print(self.current_record.keys())
        debug_print_txt('main_log', '', str(return_str) + ' \n inside check_status \n',True)
        debug_print_txt('main_log', '', str(self.current_record) + ' \n inside check_status \n',True)
        debug_print_txt('main_log', '', str(today_opt) + ' \n inside check_status \n',True)
        return self.current_record

    def buy(self, security, amount, price):
        """
        """
        result = self.user.buy(security, price, amount)  # 买入股票
        print(result)
        return(result)

    def sell(self, security, amount, price):
        """
        """
        result = self.user.sell(security, price, amount)  # 卖出股票
        print(result)
        return(result)

    def sendout_trade_record(self, json_file_url_):
        #debug_print_txt('main_log', '',' inside sendout_trade_record \n',True)
        # 返回字符串
        current_record = {}

        # 已有文件，打开读取
        if os.path.exists(json_file_url_):
            with open(json_file_url_, 'r') as _f:
                _opt_record = json.load(_f)
        else:
            _opt_record = {}

        #debug_print_txt('main_log', '',' len(_opt_record):'+ str(len(_opt_record))+' inside sendout_trade_record \n',True)
        if len(_opt_record) == 0:
            return current_record
        current_record = self.check_status()

        for stk_code in _opt_record.keys(): 
            opt_r_stk = _opt_record[stk_code]
            bb = {}
            ss = {}
 
            #debug_print_txt('main_log', '', stk_code  +' len:' +str(len(opt_r_stk['b_opt'])) +' buy sendout_trade_record \n',True)
            if len(opt_r_stk['b_opt']) != 0 and opt_r_stk['b_opt'][0]['status'] == 'PRICE':
                debug_print_txt('main_log', '', stk_code + ' amount:' + str(opt_r_stk['b_opt'][0]['amount'])  + ' buy price:' + str(opt_r_stk['b_opt'][0]['p']) + ' buy sendout_trade_record \n',True)
                bb = self.buy(stk_code, opt_r_stk['b_opt'][0]['amount'],  opt_r_stk['b_opt'][0]['p'])
                print("buy return:" + str(bb))
                opt_r_stk['b_opt'][0]['status'] = 'ORDER'
                opt_r_stk['b_opt'][0]['entrust_no'] = bb['entrust_no']

            #
            #debug_print_txt('main_log', '', stk_code  +' len:' +str(len(opt_r_stk['s_opt'])) +' sell sendout_trade_record \n',True)
            if stk_code in current_record.keys() and current_record[stk_code]['usable_balance'] > opt_r_stk['s_opt'][0]['amount']:
                if len(opt_r_stk['s_opt']) != 0 and opt_r_stk['s_opt'][0]['status'] == 'PRICE':
                    debug_print_txt('main_log', '', stk_code + ' amount:' + str(opt_r_stk['s_opt'][0]['amount'])  + ' sell price:' + str(opt_r_stk['s_opt'][0]['p']) + ' sell sendout_trade_record \n',True)
                    ss = self.sell(stk_code, opt_r_stk['s_opt'][0]['amount'],  opt_r_stk['s_opt'][0]['p'])
                    print("sell return:" + str(ss))
                    opt_r_stk['s_opt'][0]['status'] = 'ORDER'
                    opt_r_stk['s_opt'][0]['entrust_no'] = ss['entrust_no']

            opt_r_stk['has_flashed_flag'] = True
            _opt_record[stk_code] = opt_r_stk
        
        # 保存数据
        
        with open(json_file_url_, 'w') as _f:
            #json.dump(_opt_record, _f)
            json.dump(_opt_record, _f, ensure_ascii=False, indent = 2, separators=(',', ': '))

        # 返回
        #debug_print_txt('main_log', '', stk_code  +' end of sendout_trade_record \n',True)
        return _opt_record


if __name__ == "__main__":
    #user = easytrader.use('ths')
    #user.connect(r'D:\\stock\\weituo\银河证券\\xiadan.exe')
    #user.connect(r'D:\\yhStar\\Binarystar.exe')
    #user.connect(r'D:\\stock\\Star\\xiadan.exe')

    #user = easytrader.use('yh_client')
    #user.prepare('yh_client.json')
    rt = RealTrade()
    rt.check_status()

    #rt.buy("600095", 5000, 10.22)
    #rt.sell("600095", 5000, 10.83)

    # result = user.balance
    # print(result)

    # result = user.position
    # print(result)
    
    # result = user.today_entrusts
    # print(result)    
    # result = user.today_trades
    # print(result)   
    # result = user.cancel_entrusts
    # print(result) 
    #result = user.market_buy(security="002065", amount=100,ttype=None, limit_price=None)
    #print(result) 
    #result = user.market_sell(security="002065", amount=100,ttype=None, limit_price=None)
    #print(result)     
    #result = user.buy(security="000875", amount=5000, price=3.54)  # 买入股票
    #print(result)
    
    #result = user.buy(security="002065", amount=5000, price=11.01)  # 买入股票
    #print(result)
    #result = user.sell(security="002065", amount=5000, price=11.33)  # 卖出股票
    #print(result)
    #result = user.buy(security="600095", amount=5000, price=10.22)  # 买入股票
    #print(result)
    #result = user.sell(security="600095", amount=5000, price=10.83)  # 卖出股票
    #print(result)


    
    ##result = user.auto_ipo
   ## print(result)

    # time.sleep(5)
    # if result["success"] == True:						   # 如果买入下单成功，尝试撤单
        # print("撤单测试--->", end="")
        # print(trader.cancel_entrust(entrust_no=result["entrust_no"]))