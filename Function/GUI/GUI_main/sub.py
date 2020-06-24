# encoding=utf-8

""" =========================== 将当前路径及工程的跟目录添加到路径中，必须在文件头部，否则易出错 ============================ """
import json
import sys
import os
import multiprocessing as mp
import threading

import time

from Function.GUI.GUI_main.thread_sub import timer_ctrl, get_t_now, INIT_CPT_ID, HOUR_UPDATE_ID, \
    MSG_UPDATE_ID_A, MSG_UPDATE_ID_S, NOTE_UPDATE_ID_A, NOTE_UPDATE_ID_S, LAST_TIME_UPDATE_ID, FLASH_WINDOW_ID, \
    DAY_UPDATE_ID, pipe_msg_process
from Global_Value.file_dir import opt_record, easytrader_record_file_url
from Global_Value.thread_lock import opt_lock
from SDK.Debug_Sub import debug_print_txt

curPath = os.path.abspath(os.path.dirname(__file__))
if "MoDeng" in curPath:
    rootPath = curPath[:curPath.find("MoDeng\\") + len("MoDeng\\")]  # 获取myProject，也就是项目的根路径
elif "MoDeng-master" in curPath:
    rootPath = curPath[:curPath.find("MoDeng-master\\") + len("MoDeng-master\\")]  # 获取myProject，也就是项目的根路径
else:
    print('没有找到项目的根目录！请检查项目根文件夹的名字！')
    exit(1)

sys.path.append('..')
sys.path.append(rootPath)

import copy
import matplotlib

matplotlib.use('agg')
import win32gui
import wx
import wx.xrc
import wx.grid

from Function.GUI.DengShen.dengshen import DengShen
#from Function.GUI.RealTrade.real_trade import RealTrade
from Function.GUI.RealTrade.real_trade import RealTrade
rt = RealTrade()

from Config.AutoGenerateConfigFile import data_dir
from Config.Sub import dict_stk_list
from DataSource.Code2Name import code2name
from SDK.MyTimeOPT import get_current_date_str, get_current_datetime_str


class MyImageRenderer(wx.grid.GridCellRenderer):
    def __init__(self, img):
        wx.grid.GridCellRenderer.__init__(self)
        self.img = img

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        image = wx.MemoryDC()
        image.SelectObject(self.img)
        dc.SetBackgroundMode(wx.SOLID)
        if isSelected:
            dc.SetBrush(wx.Brush(wx.BLUE, wx.SOLID))
            dc.SetPen(wx.Pen(wx.BLUE, 1, wx.SOLID))
        else:
            dc.SetBrush(wx.Brush(wx.WHITE, wx.SOLID))
            dc.SetPen(wx.Pen(wx.WHITE, 1, wx.SOLID))
        dc.DrawRectangle(rect)
        width, height = self.img.GetWidth(), self.img.GetHeight()
        if width > rect.width - 2:
            width = rect.width - 2
        if height > rect.height - 2:
            height = rect.height - 2
        dc.Blit(rect.x + 1, rect.y + 1, width, height, image, 0, 0, wx.COPY, True)


class MyPanelText(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.Size(500, 300),
                          style=wx.TAB_TRAVERSAL)

        bSizer1 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_textCtrlNote = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
                                          size=wx.Size(550, 800))
        self.m_textCtrlNote.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        self.m_textCtrlNote.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))

        self.m_textCtrlMsg = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
                                         size=wx.Size(550, 800))
        self.m_textCtrlMsg.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        self.m_textCtrlMsg.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))

        bSizer1.Add(self.m_textCtrlNote, 0, wx.ALL, 5)
        bSizer1.Add(self.m_textCtrlMsg, 0, wx.ALL, 5)

        self.SetSizer(bSizer1)
        self.Layout()

    def __del__(self):
        pass


class MyPanelGrid(wx.Panel):

    def __init__(self, parent, stk_info):
        wx.Panel.__init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.Size(500, 300),
                          style=wx.TAB_TRAVERSAL)

        bSizer4 = wx.BoxSizer(wx.VERTICAL)

        self.my_grid4 = wx.grid.Grid(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)

        # Grid
        self.my_grid4.CreateGrid(len(stk_info), 6)
        self.my_grid4.EnableEditing(False)
        self.my_grid4.EnableGridLines(True)
        self.my_grid4.EnableDragGridSize(False)
        self.my_grid4.SetMargins(0, 0)

        # Columns
        self.my_grid4.EnableDragColMove(False)
        self.my_grid4.EnableDragColSize(True)
        self.my_grid4.SetColLabelSize(30)
        self.my_grid4.SetColLabelAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

        self.my_grid4.SetColLabelValue(0, "定时检测")
        self.my_grid4.SetColLabelValue(1, "小时M")
        self.my_grid4.SetColLabelValue(2, "小时-其他指标")
        self.my_grid4.SetColLabelValue(3, "日M")
        self.my_grid4.SetColLabelValue(4, "周/月M")
        self.my_grid4.SetColLabelValue(5, "日-其他指数")

        # Rows
        self.my_grid4.EnableDragRowSize(True)
        self.my_grid4.SetRowLabelSize(80)
        self.my_grid4.SetRowLabelAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        # self.my_grid4.SetRowLabelValue()

        # Add name to Rows
        self.add_row_name([(x[0], x[1]) for x in stk_info])

        self.my_grid4.SetDefaultCellAlignment(wx.ALIGN_LEFT, wx.ALIGN_TOP)
        self.my_grid4.DisableCellEditControl()

        # 设置行间隔
        # self.my_grid4.SetMargins(0, 2)

        bSizer4.Add(self.my_grid4, 0, wx.ALL, 5)

        self.SetSizer(bSizer4)
        self.Layout()

    def __del__(self):
        pass

    def add_row_name(self, stk_code_list):
        """
		添加行名称
		:param stk_code_list:
		:return:
		"""

        for info in stk_code_list:
            self.my_grid4.SetRowLabelValue(info[0], code2name(info[1]))

    def insert_pic_to_cell(self, r, c, img):
        """
		:param r:
		:param c:
		:param pic:
		:return:
		"""

        img_Rd = MyImageRenderer(wx.Bitmap(img))
        self.my_grid4.SetCellRenderer(r, c, img_Rd)
        self.my_grid4.SetColSize(c, img.GetWidth() + 2)
        self.my_grid4.SetRowSize(r, img.GetHeight() + 2)


class MyFrame(wx.Frame):
    def __init__(self, parent, pipe, title, debug=False):
        wx.Frame.__init__(self, parent, id=-1, title=title)

        # 绑定关闭函数
        self.Bind(wx.EVT_CLOSE, self.on_close, parent)

        # 绑定按键事件与函数
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)

        self.handle = self.GetHandle()
        self.nb = wx.Notebook(self)

        # 行信息对照表，防止贴图出错
        self.r2code = self.gen_r_to_code()
        self.index_page = [(1, 'Index'), (2, 'Buy'), (3, 'Concerned')]

        # 绑定ID与响应函数
        self.Connect(-1, -1, INIT_CPT_ID, self.on_init_pic)
        self.Connect(-1, -1, HOUR_UPDATE_ID, self.on_update_hour_pic)
        self.Connect(-1, -1, DAY_UPDATE_ID, self.on_update_day_pic)
        self.Connect(-1, -1, MSG_UPDATE_ID_A, self.on_update_msg_tc_a)
        self.Connect(-1, -1, MSG_UPDATE_ID_S, self.on_update_msg_tc_s)
        self.Connect(-1, -1, NOTE_UPDATE_ID_A, self.on_update_note_tc_a)
        self.Connect(-1, -1, NOTE_UPDATE_ID_S, self.on_update_note_tc_s)
        self.Connect(-1, -1, LAST_TIME_UPDATE_ID, self.on_update_last_time)
        self.Connect(-1, -1, FLASH_WINDOW_ID, self.flash_window)

        # 获取控制台panel对象
        self.nb.AddPage(MyPanelText(self.nb), "控制台")
        self.p_ctrl = self.nb.GetPage(0)
        self.on_init_pic()

        # 函数外部变量
        self.last_upt_t = get_t_now()
        self.Show()

        # 启动数据处理线程，专用于处理数据，防止软件操作卡顿
        self.thread = threading.Thread(target=timer_ctrl, args=(self, debug))
        self.thread.start()

        # 管道交互线程
        self.thread_pipe = threading.Thread(target=pipe_msg_process, args=(self, pipe, debug))
        self.thread_pipe.start()

    def on_close(self, event):
        print('进入主GUI的关闭响应函数！')

        # 保存操作日志
        if opt_lock.acquire():
            try:
                file_dir = data_dir + 'Opt_Record/'

                if not os.path.exists(file_dir):
                    os.makedirs(file_dir)
                with open(file_dir + get_current_date_str() + 'record.json', 'w') as f:
                    json.dump(opt_record, f)
                print('主GUI:记录保存成功！')
            finally:
                opt_lock.release()

        event.Skip()

    def on_init_pic(self):
        """
		:return:
		"""

        self.nb.AddPage(MyPanelGrid(self.nb, dict_stk_list['Index']), "指数")
        self.nb.AddPage(MyPanelGrid(self.nb, dict_stk_list['Buy']), "持仓")
        self.nb.AddPage(MyPanelGrid(self.nb, dict_stk_list['Concerned']), "关注")
        self.Refresh()

    def on_update_hour_pic(self, evt):

        if isinstance(evt, dict):
            # 获取新图片的数据
            pic_hour_macd_dict = evt['h']
            pic_hour_idx_dict = evt['h_idx']
        else:

            # 获取新图片的数据
            pic_hour_macd_dict = evt.data['h_macd']
            pic_hour_idx_dict = evt.data['h_idx']

        # 更新图片
        for page in self.index_page:

            p_index = page[0]
            p_name = page[1]

            # 获取page
            p_nb = self.nb.GetPage(p_index)

            # 循环插入图片 macd
            for stk_info in dict_stk_list[p_name]:
                stk = stk_info[1]
                img_h_macd = pic_hour_macd_dict[p_name][stk]
                p_nb.insert_pic_to_cell(img_h_macd[0], 1, img_h_macd[1])

                img_h_idx = pic_hour_idx_dict[p_name][stk]
                p_nb.insert_pic_to_cell(img_h_idx[0], 2, img_h_idx[1])

        self.Refresh()

    def on_update_day_pic(self, evt):

        if isinstance(evt, dict):
            pic_day_macd_dict = evt['d']
            pic_day_idx_dict = evt['d_idx']
            pic_wm_dict = evt['wm']
        else:
            pic_day_macd_dict = evt.data['day_macd']
            pic_day_idx_dict = evt.data['day_idx']
            pic_wm_dict = evt.data['wm']

        # 更新图片
        for page in self.index_page:

            p_index = page[0]
            p_name = page[1]

            # 获取page
            p_nb = self.nb.GetPage(p_index)

            for stk_info in dict_stk_list[p_name]:
                stk = stk_info[1]
                img_day_macd = pic_day_macd_dict[p_name][stk]
                p_nb.insert_pic_to_cell(img_day_macd[0], 3, img_day_macd[1])

                img_day_idx = pic_day_idx_dict[p_name][stk]
                p_nb.insert_pic_to_cell(img_day_idx[0], 5, img_day_idx[1])

                img_wm = pic_wm_dict[p_name][stk]
                p_nb.insert_pic_to_cell(img_wm[0], 4, img_wm[1])

        self.Refresh()

    @staticmethod
    def change_tc_color(data, tc):
        """
		改变textctrl中字符的打印颜色
		:param data:
		:param tc:
		:return:
		"""

        if isinstance(data, str):
            tc.SetDefaultStyle(wx.TextAttr(wx.LIGHT_GREY))  # 默认字体颜色为浅灰色
            return data

        elif isinstance(data, tuple):
            if data[0] is 'r':
                tc.SetDefaultStyle(wx.TextAttr(wx.RED))  # 红色字体
                return data[1]

            elif data[0] is 'g':
                tc.SetDefaultStyle(wx.TextAttr(wx.GREEN))  # 绿色字体
                return data[1]

            elif data[0] is 'y':
                tc.SetDefaultStyle(wx.TextAttr(wx.YELLOW))  # 黄色字体
                return data[1]

            else:
                tc.SetDefaultStyle(wx.TextAttr(wx.LIGHT_GREY))  # 默认字体颜色为浅灰色
                return data[1]
        else:
            tc.SetDefaultStyle(wx.TextAttr(wx.LIGHT_GREY))  # 默认字体颜色为浅灰色
            return data

    def on_update_note_tc_a(self, evt):
        """
		以“追加”的方式在“提示”对话框打印字符！
		:param evt:
		:return:
		"""

        if isinstance(evt, str):
            data = evt
        elif isinstance(evt, tuple):
            data = evt
        else:
            data = evt.data

        # 调整字体颜色
        str_note = self.change_tc_color(data, self.p_ctrl.m_textCtrlNote)

        if len(str_note):
            self.p_ctrl.m_textCtrlNote.AppendText(str_note + '\n')

    # self.p_ctrl.m_textCtrlNote.AppendText('\n\n检测时间：' + get_current_datetime_str() + '\n\n')

    def flash_window(self, evt=None):

        # 打印此次提示的时间
        self.on_update_note_tc_a(
            '以上提示发生时间：' + get_current_datetime_str() + '\n----------------------------------------\n\n')

        win32gui.FlashWindowEx(self.handle, 2, 3, 400)

    def on_update_note_tc_s(self, evt):
        """
		以“覆盖”的方式在“提示”对话框打印字符！
		:param evt:
		:return:
		"""
        if isinstance(evt, str):
            data = evt
        elif isinstance(evt, tuple):
            data = evt
        else:
            data = evt.data

        # 调整字体颜色
        str_note = self.change_tc_color(data, self.p_ctrl.m_textCtrlNote)

        if len(str_note):
            self.p_ctrl.m_textCtrlNote.SetValue(str_note)

    # self.p_ctrl.m_textCtrlNote.AppendText('\n\n检测时间：' + get_current_datetime_str() + '\n\n')
    # win32gui.FlashWindowEx(self.handle, 2, 3, 400)

    def on_update_msg_tc_a(self, evt):
        """
		更新textctrl中的文本，后缀A表示采用append（添加）的方式，而非S（覆盖）的方式
		:param evt:
		:return:
		"""

        if isinstance(evt, str):
            data = evt
        elif isinstance(evt, tuple):
            data = evt[1]
        else:
            data = evt.data

        # 调整字体颜色
        str_msg = self.change_tc_color(data, self.p_ctrl.m_textCtrlMsg)

        if len(str_msg):
            self.p_ctrl.m_textCtrlMsg.AppendText(str_msg + '\n')

    # self.p_ctrl.m_textCtrlMsg.AppendText('\n\n检测时间：' + get_current_datetime_str() + '\n\n')

    def on_update_msg_tc_s(self, evt):

        if isinstance(evt, str):
            data = evt
        elif isinstance(evt, tuple):
            data = evt[1]
        else:
            data = evt.data

        # 调整字体颜色
        str_msg = self.change_tc_color(data, self.p_ctrl.m_textCtrlMsg)

        if len(str_msg):
            self.p_ctrl.m_textCtrlMsg.SetValue(str_msg + '\n')

    def on_update_last_time(self, evt):
        """
		:param evt:
		"""
        self.last_upt_t = evt.data

    def gen_r_to_code(self):
        r2code = copy.deepcopy(dict_stk_list)

        for page in r2code.keys():
            r2code[page] = dict(enumerate(r2code[page]))

        return r2code

    def on_key_down(self, event):

        key_code = event.GetKeyCode()
        if key_code == wx.WXK_F1:

            print('检测到F1按下！')

            try:
                # 创建灯神，并显示
                ds = DengShen(self, '灯神')
                ds.Show()
            except Exception as e:
                self.on_update_note_tc_a('灯神异常退出! 原因：\n' + str(e))
                self.flash_window()

                debug_print_txt('main_log', '', '灯神异常退出! 原因：\n' + str(e))
            finally:
                event.Skip()
        elif key_code == wx.WXK_F2:
            print('检测到F2按下！')

            try:
                # 创建realtrader，并显示
                #rt = RealTrade(self, 'easytrader')
                #rt.Show()
                #rt.input_analysis("查看b记录 东华软件")

                self.on_update_note_tc_a('call easytrader real trading now!\n')
                #rt.buy("600095", 5000, 10.22)
                #rt.sell("600095", 5000, 10.83)
                rt.sendout_trade_record(easytrader_record_file_url)
            except Exception as e:
                self.on_update_note_tc_a('realtrade异常退出! 原因：\n' + str(e))
                self.flash_window()

                debug_print_txt('main_log', '', 'realtrade异常退出! 原因：\n' + str(e))
            finally:
                event.Skip()
        else:
            event.Skip()


def run_myframe_in_process(pipe_master, debug=False):
    """
	在特定进程中执行UI程序
	:return:
	"""

    app = wx.App()
    app.locale = wx.Locale(wx.LANGUAGE_CHINESE_SIMPLIFIED)
    frame = MyFrame(None, pipe_master, title="魔灯-V20200131", debug=debug)
    app.MainLoop()


if __name__ == '__main__':
    pass
