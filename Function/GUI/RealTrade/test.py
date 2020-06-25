import sys
sys.path.append('../../../')
from real_trade import RealTrade
from Global_Value.file_dir import yh_client_file_url, easytrader_record_file_url

if __name__ == "__main__":
    rt = RealTrade()
    #rt.check_status()
    rt.sendout_trade_record(easytrader_record_file_url)
    #rt.buy("600095", 5000, 10.22)
    #rt.sell("600095", 5000, 10.83)

