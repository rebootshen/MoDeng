# coding=utf-8
import json
import threading
import pandas as pd
import wx
import os

from Config.AutoGenerateConfigFile import data_dir
from Config.Sub import read_config, write_config
from DataSource.Code2Name import name2code, code2name
from DataSource.auth_info import jq_login, logout
from Function.GUI.GUI_main.note_string import total_cmd
from Function.GUI.Sub.sub import text_append_color
from Function.SeaSelect.Sub.select_class import ExecuteSelectRole
from Function.SeaSelect.Sub.select_cmd_class import SelectCmd
from Global_Value.file_dir import  opt_record
from Global_Value.thread_lock import opt_record_lock


from pylab import *

# opt_record.json文件读写锁
from SDK.MyTimeOPT import get_current_datetime_str

opt_record_file_url = data_dir + 'easytrader_record.json'


class StkConfig:
    def __init__(self):
        pass

    @staticmethod
    def add_stk(kind, name, tc):
        """
        增加持仓
        :param name:
        :param tc:
        :return:
        """

        # 判断输入的是代码是名称
        if 'qh' in name:
            code = name[2:]
        elif name.isdigit():
            code = name
        else:
            code = name2code(name)
            if code == '未知代码':
                text_append_color(tc, name + ':不识别的股票名字！请尝试使用股票代码！')
                return

        # 向配置文件中写入 增加持仓的stk代码
        stk_now = read_config()[kind]
        if code not in stk_now:
            stk_now.append(code)
            write_config(kind, stk_now)
            text_append_color(tc, '增加“' + name + '”成功！')
        else:
            text_append_color(tc, '增加“' + name + '”失败！已存在！')

    @staticmethod
    def delete_stk(kind, name, tc):
        """
        从持仓中删除
        :param name:
        :param tc:
        :return:
        """
        # 判断输入的是代码是名称
        if name.isdigit():
            code = name
        else:
            code = name2code(name)
            if code == '未知代码':
                text_append_color(tc, name + ':不识别的股票名字！请尝试使用股票代码！')
                return

        # 向配置文件中删除 增加持仓的stk代码
        stk_now = read_config()[kind]
        if code in stk_now:
            stk_now.remove(code)
            write_config(kind, stk_now)
            text_append_color(tc, '删除“' + name + '”成功！')
        else:
            text_append_color(tc, '删除“' + name + '”失败！原先关注列表中没有 ' + name)

    @staticmethod
    def cat_stk(kind, tc):
        """
        查看相关stk列表
        :param kind:
        :return:
        """
        stk_list = read_config()[kind]
        stk_name = str([code2name(x) for x in stk_list])

        text_append_color(tc, stk_name.replace('[', '').replace(']', '').replace(',', '\n'))

class RealTrade(wx.Frame):
    def __init__(self, parent, title):
        super(RealTrade, self).__init__(parent, title=title, size=(700, 500))

        # 绑定关闭函数
        self.Bind(wx.EVT_CLOSE, self.on_close, parent)

        panel = wx.Panel(self)
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)

        self.t3 = wx.TextCtrl(panel, size=(600, 1000), style=wx.TE_MULTILINE | wx.TE_RICH2)

        hbox3.Add(self.t3, 1, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, 5)

        self.t3.Bind(wx.EVT_TEXT_ENTER, self.on_enter_pressed)
        self.t3.SetBackgroundColour('Black')
        self.t3.SetForegroundColour('Red')
        panel.SetSizer(hbox3)

        # 打印欢迎语
        text_append_color(self.t3, '输入帮助查看详细用法\n')
        text_append_color(self.t3, '\n请输入命令：\n', color=wx.YELLOW)
        self.Centre()
        self.Show()
        self.Fit()

    def input_analysis(self, input_str):
        text_append_color(self.t3, '\n\n')

        if '增加持仓' in input_str:
            ipt_split = input_str.split(' ')

            # 向配置文件中写入 增加持仓的stk代码
            StkConfig.add_stk(kind='buy_stk', name=ipt_split[1], tc=self.t3)

        elif '删除持仓' in input_str:
            ipt_split = input_str.split(' ')

            # 向配置文件中写入 增加持仓的stk代码
            StkConfig.delete_stk(kind='buy_stk', name=ipt_split[1], tc=self.t3)


        elif ('买入' in input_str) | ('卖出' in input_str):
            add_opt(input_str, opt_record_file_url, self.t3)

        elif '查看b记录' in input_str:
            cat_stk_opt_record(
                input_str=input_str,
                json_file_url=opt_record_file_url,
                tc=self.t3)
       
        else:
            text_append_color(self.t3, '没听懂，请明示！')

    
    def on_close(self, event):
        print('进入关闭响应函数！')
        global realtrade_on
        realtrade_on = False

        event.Skip()

    def on_key_typed(self, event):
        print(event.GetString())

    def on_enter_pressed(self, event):

        # 获取最后一行
        input_str = list(filter(lambda x: x != '', event.GetString().split('\n')))[-1]

        try:
            self.input_analysis(input_str)
            text_append_color(self.t3, '\n请输入命令：\n', color=wx.YELLOW)
        except Exception as e_:
            text_append_color(self.t3, 'realtrade出错了！原因：\n' + str(e_) + '\n\n')
            text_append_color(self.t3, '\n请输入命令：\n', color=wx.YELLOW)




def cat_stk_opt_record(input_str, json_file_url, tc):
    if opt_record_lock.acquire():
        r = '未知错误'
        try:
            r = cat_stk_b_opt_sub(stk_name=input_str.split(' ')[1], json_file_url=json_file_url)
        except Exception as e:
            r = '读写' + json_file_url + '文件失败！原因：\n' + str(e)
        finally:
            opt_record_lock.release()
            text_append_color(tc, r + '\n')


def cat_stk_b_opt_sub(stk_name, json_file_url):
    """

    :param stk_name:
    :param json_file_url:
    :return:
    """

    # 已有文件，打开读取
    if os.path.exists(json_file_url):
        with open(json_file_url, 'r') as f:
            opt_record = json.load(f)
    else:
        return '没有记录文件！'

    if name2code(stk_name) not in opt_record.keys():
        return '没有' + stk_name + '的数据！'

    if len(opt_record[name2code(stk_name)]['b_opt']) == 0:
        return stk_name + '没有操作记录！'

    return pd.DataFrame(opt_record[name2code(stk_name)]['b_opt']).sort_values(by='p', ascending=False).loc[:,
           ['time', 'p', 'amount']].to_string()


def add_opt(input_str, json_file_url, tc):
    if opt_record_lock.acquire():
        r = ['未知错误']
        try:
            r = add_opt_to_json_sub(input_str, json_file_url, tc)
        except Exception as e:
            r = ['读写opt_record.json文件失败！原因：\n' + str(e)]
        finally:
            opt_record_lock.release()
            for str_ in r:
                text_append_color(tc, str_ + '\n')


def add_opt_to_json_sub(input_str, json_file_url_, tc):
    # 返回字符串
    return_str = []

    # 已有文件，打开读取
    if os.path.exists(json_file_url_):
        with open(json_file_url_, 'r') as _f:
            _opt_record = json.load(_f)
    else:
        _opt_record = {}

    # 解析输入
    stk_name, opt, amount, p = input_str.split(' ')
    stk_code = name2code(stk_name)
    p, amount = float(p), float(amount)
    
    # 对输入格式进行检查
    if amount % 100 != 0:
        tc.AppendText('格式错误！参考格式：\n美的集团 卖出 400 51.3')
        return

    if stk_code in _opt_record.keys():
        opt_r_stk = _opt_record[stk_code]
    else:
        opt_r_stk = {
            'b_opt': [],
            'p_last': None,
            'has_flashed_flag': True,
            'total_earn': 0,
            'last_prompt_point': -1
        }

    if opt == '买入':
        opt_r_stk['b_opt'].append(dict(time=get_current_datetime_str(), p=p, amount=amount))

    if opt == '卖出':
        if len(opt_r_stk['b_opt']) > 0:
            opt_r_stk, earn_this = sale_stk_sub(opt_r_stk, amount, p, tc)

            return_str.append('earn：' + str(earn_this) + '\n')

    opt_r_stk['p_last'] = p
    opt_r_stk['has_flashed_flag'] = True

    # 保存数据
    _opt_record[stk_code] = opt_r_stk
    with open(json_file_url_, 'w') as _f:
        json.dump(_opt_record, _f)

    # 返回
    return return_str


def sale_stk_sub(stk_record, s_amount, s_p, tc):
    """

    :param stk_record:
    :return:
    """

    opt_r_stk = stk_record

    # 本次盈利
    earn_this = 0

    if len(opt_r_stk['b_opt']) > 0:

        p_min = np.min([x['p'] for x in opt_r_stk['b_opt']])
        opt_r_stk['b_opt'].sort(key=lambda x: x['p'] == p_min, reverse=False)

        # 循环清算
        while True:

            if opt_r_stk['b_opt'][-1]['amount'] <= s_amount:

                # 注销
                b_pop = opt_r_stk['b_opt'].pop(-1)

                # 清算
                s_amount = s_amount - b_pop['amount']

                # 计算盈利
                earn_this = earn_this + b_pop['amount'] * (s_p - b_pop['p'])

            else:

                # 清算
                opt_r_stk['b_opt'][-1]['amount'] = opt_r_stk['b_opt'][-1]['amount'] - s_amount

                # 计算盈利
                earn_this = earn_this + s_amount * (s_p - opt_r_stk['b_opt'][-1]['p'])

                break

            # 判断是否有
            if len(opt_r_stk['b_opt']) < 1:

                if s_amount > 0:
                    text_append_color(tc, '异常： 可卖标的数量超过持有量！\n')
                break

        opt_r_stk['total_earn'] = opt_r_stk['total_earn'] + earn_this

    return opt_r_stk, earn_this




if __name__ == '__main__':
    app = wx.App()
    RealTrade(None, 'easytrader')
    this.input_analysis(self, "查看b记录")
    app.MainLoop()
