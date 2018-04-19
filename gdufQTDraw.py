# -*- coding: utf-8 -*- 
'''
    模块名：zwQTDraw.py
    默认缩写：zwdr,示例：import wQTDraw as zwdr
   【简介】
    zwQT量化软件，绘图模块
     
    zw量化，py量化第一品牌
    网站:http://www.ziwang.com zw网站
    py量化QQ总群  124134140   千人大群 zwPython量化&大数据 
     
    开发：zw量化开源团队 2016.04.01 首发
  
'''




import pandas as pd
import matplotlib.pyplot as plt


#----
def Draw(account):
    #基准
    benchmark=pd.read_csv('G:\\zwQuant\\zwDat\\cn\\xday\\'+account.stkInxCode+'.csv')
    benchmark.index=benchmark['date']
    prebenchmark=benchmark['close'].shift(1)
    nowbenchmark=benchmark['close'].shift(-1).shift(1)
    Return=nowbenchmark/prebenchmark-1.0
    Return.index=benchmark['date']
    Return=Return+1.0
    start=account.staVars[-2]
    end=account.staVars[-1]
    Return=Return[start:end].cumprod()-1.0
    plt.figure(figsize=(10,8))
    plt.plot(pd.to_datetime(Return.index),Return,label='benchmark')
    #策略
    account.qxLib.index=account.qxLib['date']
    nowSighmark= account.qxLib['val'].shift(1)
    preSighmark=account.qxLib['val']
    ReturnSigh=preSighmark/nowSighmark-1.0
    ReturnSigh.ix[0] = account.qxLib['val'].ix[0]/account.mbase- 1.0
    ReturnSigh.index=account.qxLib['date']
    ReturnSigh=ReturnSigh+1.0
    start=account.staVars[-2]
    end=account.staVars[-1]
    ReturnSigh=ReturnSigh[start:end].cumprod()-1.0
    plt.plot(pd.to_datetime(ReturnSigh.index),ReturnSigh,label='Signal')
    plt.legend()