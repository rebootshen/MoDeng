import sys
sys.path.append('../../../')
from real_trade import RealTrade

if __name__ == "__main__":
    rt = RealTrade()
    rt.check_status()
    #rt.buy("600095", 5000, 10.22)
    #rt.sell("600095", 5000, 10.83)

