
# coding=utf-8

import pandas as pd
import gdufSys as zw
import gdufQTDraw as zwdr
import gdufBacktest as zwbt


#=======================    
  
     
#----数据预处理函数   
def sta01_dataPre(account,xnam0):
    zwbt.sta_dataPre0xtim(account,xnam0);
    #----对各只股票数据，进行预处理，提高后期运算速度
    account.PB=pd.read_csv('G:\zwQuant\dat\yinzi\PB.csv')
    NAME=account.PB['ticker']
    L=[]
    for i,z in enumerate(NAME):
            L.append(str(z))
    L=pd.DataFrame(L)
    account.PB['ticker']=L[0]
    #下面的代码无论什么策略都要写一样的
    for xcod in zw.stkLibCode:
        d20=zw.stkLib[xcod];
        #  计算交易价格kprice和策略分析采用的价格dprice,kprice一般采用次日的开盘价
       
        d20['dprice']=d20['open']
       
        d20['kprice']=d20['dprice']
        if account.debugMod>0:
          
            fss='tmp\\'+account.prjName+'_'+xcod+'.csv'
            d20.to_csv(fss)   

#策略函数
def handle_data(account,Code):
   
    list1=Code
    time=account.xtim;
    list2=list(account.PB['ticker'][account.PB[time]>3])
    buylist=[i for i in list1 if i in list2 ]
    selllist=account.security_position
    return buylist,selllist
    
#买的信号
def sta01buy(account):
    time,code=account.xtim,account.stkCode;
    #等权买入，暂时弄得有些复杂这个玩意
    stknum=account.money/len(account.buylist)/zw.stkLib[code][time:time]['open'].values[0]
    #stknum=100
    return stknum   

#卖的信号
def sta01sell(account):
    stknum=-1;
    return stknum
    

    
   
def bt_endRets(account):            
    #---ok ，测试完毕
    # 保存测试数据，qxlib，每日收益等数据；xtrdLib，交易清单数据
    account.qxLib.to_csv(account.fn_qxLib,index=False,encode='utf-8')
    account.xtrdLib.to_csv(account.fn_xtrdLib,index=False,encode='utf-8')
    account.prQLib()
    #
    #-------计算交易回报数据
    zwbt.zwRetTradeCalc(account)
    zwbt.zwRetPr(account)
    zwdr.Draw(account)
   
#==================main
#--------init，设置参数

rss='dat\\'
universe=['600231','600401','600663']  #600401,*ST海润,*SThr 
account=zwbt.bt_init(universe,rss,'sta01',100000);
#
#---设置策略参数
account.stkInxCode='000300' 
account.staVars=['2010-01-01','2015-01-01']    
account.debugMod=1
account.handle_data=handle_data;
account.staFunbuy=sta01buy; #---绑定策略函数&运行回溯主函数
account.staFunsell=sta01sell;
#---根据当前策略，对数据进行预处理
sta01_dataPre(account,'sta01')
#----运行回溯主程序
day=20#回测频率
zwbt.gdufBackTest(account,day)
#----输出回溯结果
bt_endRets(account)
