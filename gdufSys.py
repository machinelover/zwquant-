# -*- coding: utf-8 -*-
"""
Created on Fri Oct  6 11:25:17 2017

@author: ASUS
"""

import sys,os
import pandas as pd
from dateutil.parser import parse
from dateutil import rrule
import zwTools as zwt
import gdufBacktest as zwbt

#----init.dir 目录设置

_rdat0="\\zwDat\\"
_rdatCN=_rdat0+"cn\\"
_rdatUS=_rdat0+"us\\"
_rdatInx=_rdat0+"inx\\"
_rdatMin=_rdat0+"min\\"
_rdatTick=_rdat0+"tick\\"
_rdatTickReal=_rdat0+"tickreal\\"

_rdatZW=_rdat0+"zw\\"

_rTmp="\\zwPython\\zwQuant\\demo\\tmp\\"
#----init.stk.var 初始化数据设置
_stkTradeTaxi=0.002
_stkRateRF=0.03
_stkKRateBreak=10

##---qx.misc.xxx
#qxMinName=['time','open','high','low','close','volume','amount','vol_norm','amo_norm','vol_buy','amo_buy','vol_sell','amo_sell']
#qxTickName=['time','price','change','volume','amount','type']
#qxTickNameNew=['date','price','change','volume','amount','type']
##
#qxKPriceName=['open','high','low','close','adj close','dprice','kprice']
##---qxLib.xxxx
#ohlcLst=['open','high','low','close']
#ohlcExtLst=['date','open','high','low','close','volume','adj close']
xtrdName=['date','ID','mode','code','dprice','num','kprice','sum','chichangnum','cash'];
xtrdNil=['','','','',0,0,0,0,0,0];
qxLibName=['date','stkVal','cash','dret','val','downLow','downHigh','downDay','downKMax'];
qxLibNil=['',0,0,0,0,0,0,0,0];  #xBars:DF

stkInxLib=None  #全局变量，大盘指数，内存股票数据库
stkLib={}       #全局变量，相关股票的交易数据，内存股票数据库
stkLibCode=[]   #全局变量，相关股票的交易代码，内存股票数据库
stkCodeTbl=None  #全局变量，相关股票的交易代码，名称对照表

#----zw.var...
__version__='2016.M5'

#颜色变量
#注意，opecv内部的颜色不是常用的RGB模式，而是采用BGR排列
_corBlack=(0,0,0)
_corWhite=(255,255,255)
_corGray=(128,128,128)
_corBlue=(0,0,255)
_corGreed=(0,255,0)
_corRed=(255,0,0)

_corRedCV=(0,0,255)
_corBlueCV=(255,0,0)
class gdufBar(object):
    ''' 记录每笔交易Bar数据包
    
    Args:
        Csv数据源。
        (datetime, open, close, high, low, volume)
        
    :ivar xtim: 交易时间
    :ivar mode: 买or卖
    :ivar code: 股票代码
    :ivar num: 交易量
    :ivar price: 成交价
    :ivar sum： 交易总额
    '''

    def __init__(self,xtim,mode='',code='',num=0,price=0):    
        self.time=xtim;        
        self.mode=mode;  #'',buy,sell
        self.code=code;
        self.num=num;        
        self.price=price
        self.sum=price*num
         
    def prXBar(self):
        print('')
        print('date,',self.time);
        print('mode,',self.mode);
        print('code,',self.code);
        print('num,',self.num);
        print('price,',self.price);
        print('sum,',self.sum);




class gdufQuant(object):
    ''' 定义了量化交易所需的各种变量参数、相关的类函数
    
    Args:
        csv数据源。
        (datetime, open, close, high, low, volume)
        '''

    def __init__(self,prjNam,dbase0=10000):
        ''' 默认初始化函数
        Args:
            prjNam (list): 项目名称
            dbase0 (int): 启动资金
        '''
        self.security_position=[];#持仓列表
        self.AllACode=pd.read_csv('dat\\A\\isopen.csv',index_col='ticker')#全A股开市情况
        NAME=self.AllACode.index
        L=[]
        for i,z in enumerate(NAME):
            if len(str(z))==1:
                L.append('00000'+str(z))
            elif len(str(z))==2:
                L.append('0000'+str(z))
            elif len(str(z))==3:
                L.append('000'+str(z))
            elif len(str(z))==4:
                L.append('00'+str(z))
            elif len(str(z))==5:
                L.append('0'+str(z))
            else:
                L.append(str(z))
        L=pd.DataFrame(L)
        self.AllACode.index=L[0]
        self.ST=pd.read_csv('dat\\A\\ST.csv',index_col='ticker',encoding='gbk')#全A股是否为ST股
        NAME=self.ST.index
        L=[]
        for i,z in enumerate(NAME):
            if len(str(z))==1:
                L.append('00000'+str(z))
            elif len(str(z))==2:
                L.append('0000'+str(z))
            elif len(str(z))==3:
                L.append('000'+str(z))
            elif len(str(z))==4:
                L.append('00'+str(z))
            elif len(str(z))==5:
                L.append('0'+str(z))
            else:
                L.append(str(z))
        L=pd.DataFrame(L)
        self.ST.index=L[0]
        #可以自行添加如HS300，ZZ500的板块的股票池，代码如上类似
        #taxi,佣金，扣税;
        self.prjName=prjNam;
        self.fn_qxLib='tmp\\'+prjNam+'_qxLib.csv';
        self.fn_xtrdLib='tmp\\'+prjNam+'_xtrdLib.csv';
        #---
        self.mbase=dbase0;
        self.money=dbase0;
        #
        xtim0='';xtim9='';
        self.xtim0=xtim0
        self.xtim9=xtim9
        self.xtim=xtim0     
        self.DTxtim0=None
        self.DTxtim9=None
        self.cal=[]
        if self.xtim0!='':self.DTxtim0=parse(self.xtim0);
        if self.xtim9!='':self.DTxtim9=parse(self.xtim9);
        
        #
        self.stkKCash=0.9;     #默认，每次买入90%的资金  
        self.stkNum0=10;      #每手交易，默认最少10股
        self.stkNum9=20000;   #每手交易，默认最多20000股
        self.rfRate=0;        #无风险利率，例如计算夏普指数sharp radio
        self.dvix_k0=80       #dvix波动率下限
        self.dvix_k9=120      #dvix波动率上限
        # stkInx,大盘指数
        self.stkInxCode=''    #大盘指数代码
        self.stkInxCName=''    #大盘指数中文名称，拼音
        self.stkInxPriceName='close'  #大盘指数数据列名称，默认是:close
        self.stkInxRDat=''    #大盘指数数据源路径
        #---wrk.stk.var 
        
        self.stkCName=''
        self.stkName=''
        self.stkCode=''
        self.stkNum=0
        self.stkPrice=0;
            
        self.trdNilFlag=False;  #空头交易标志
        self.trdCnt=0;
        self.qxID=0;      #ID=date+'_'+trdCnt(0000)
        self.rdat='';     #股票数据文件目录
        #self.rxdat='';    #指数文件目录
        
        #
        self.periodMode='day'; #day,hour,min
        self.periodCount=0;
        self.periodNWork=0;  #工作日(时)长
        self.periodNDay=rrule.rrule(rrule.DAILY,dtstart=self.DTxtim0,until=self.DTxtim9).count()
        self.wrkNDay=0
        #-----ret
        self.mvalSum=0;
        self.mvalGet=0;
        self.mvalCash=0;
        self.mvalOther=0;   #其他资产价值，例如股票价值stkVal
        self.kretYear=0
        self.kretDay=0
        self.kretDayStd=0
        #---
        self.pltTop=None;
        self.pltTop2=None;
        self.pltMid=None;
        self.pltMid2=None;
        self.pltBot=None;
        self.pltBot2=None;
        #---
        self.staFunbuy='';
        self.staFunsell='';
        self.staVars=['','']  #策略变量输入数据列表
        self.staName='';

        
        #---drawdown.var
        self.downHigh=0;
        self.downLow=0;
        self.downHighTime=None;
        self.downMaxDay=0;
        self.downKMax=0;
        
        #---qxLib.xxx.init
        #xBarName=['date','ID','mode','code','num','price','sum'];
        #qxLibName=['date','ID','stkVal','cash','dret','val'];
        self.qxLib=pd.DataFrame(columns=qxLibName,index=['date']);    #所有交易记录清单列表
        self.qxLib.dropna(inplace=True);
        self.xtrdLib=pd.DataFrame(columns=xtrdName,index=['date']);   #所有xBars股票交易记录清单列表         
        self.xtrdLib.dropna(inplace=True);
        self.xtrdNilLib=pd.DataFrame(columns=xtrdName,index=['date']);   #所有Nil空头交易记录清单列表         
        self.xtrdNilLib.dropna(inplace=True);        
        self.qxUsr=pd.Series(index=qxLibName)    #用户资产数据
        self.qxUsrStk={};                        #用户持有的股票资产数据
        self.xbarWrk=None;
        self.xdatWrk=None;
        self.xtrdChk=None;
        
         
        #----misc
        #debug
        #',__name__,',@fun:',sys._getframe().f_code.co_name)
        #上级主叫函数 sys._getframe().f_back.f_code.co_name
        self.debugMod=0;  #调试Mod，0：不调试；1：主模块，',__name__=__main__；3：子模块 5；
        
        #------设置各种环境的价格模式：
        #    priceWrk，策略分析时，使用的股票价格，一般是：dprice，复权开盘价
        #    priceBuy，买入/卖出的股票价格，一般是：kprice，一般采用次日的复权开盘价
        #    priceCalc，最后结算使用的股票价格，一般是：adj close，复权收盘价
        #    qxKPriceName=['open','high','low','close','adj close','dprice','kprice']
        self.priceWrk='dprice';
        self.priceBuy='kdprice';
        self.priceCalc='close';
        #
        #-----init.set



    def qxTimSet(self,xtim0,xtim9):
        ''' 设置时间参数
           
        Args:
            xtim0 (str): 起始时间
            xtim9 (str): 截止时间
        '''
    
        self.xtim0=xtim0
        self.xtim9=xtim9
        self.xtim=xtim0 
        self.DTxtim0=parse(self.xtim0);
        self.DTxtim9=parse(self.xtim9);
        a=pd.read_csv('dat\\cal\\cal.csv')
        a=pd.to_datetime(list(a['date']))
        
        #在这里自行抽出属于星期几的工作日
        #a=pd.to_datetime(list(a['date'][a['day']=='Friday']))
        
        b=pd.to_datetime(list(rrule.rrule(rrule.DAILY,dtstart=self.DTxtim0,until=self.DTxtim9)))
        a=list(a.strftime('%Y-%m-%d'))
        b=list(b.strftime('%Y-%m-%d'))
        cal=[i for i in b if i in a]
        self.periodNDay=len(cal)
        self.cal=cal
        
        
    def qxTim0SetVar(self,xtim):
        ''' 回溯测试时间点开始，初始化相关参数
            
        '''
    
        self.xtim=xtim;
        self.qxUsr['date']=xtim;
        #self.trdCnt=0;
        self.qxID=0;
        
       
    def qxTim9SetVar(self,xtim):
        ''' 回溯测试时间点结束，整理相关数据
          
        '''
    
        self.xtim=xtim;
        self.qxUsr['date']=xtim;
        zwbt.xusrUpdate(self);
        #self.qxLib.append(self.qxUsr.T,ignore_index=True);
        self.qxLib=self.qxLib.append(self.qxUsr.T,ignore_index=True);
        #self.qxLib.dropna(inplace=True);
        

    def qxIDSet(self):
        ''' 生成订单流水号编码ID
           #ID=prjName+'_'+trdCnt(000000)
        '''
    
        self.trdCnt+=1;
        nss='{:06d}'.format(self.trdCnt);
        #tim=parse(self.xtim);
        #timStr=tim.strftime('%Y%m%d')
        self.qxID=self.prjName+'_'+nss;
        #print(s2,',',qx.trdCnt)
        #print('trdID',qx.trdID)
    
        return self.qxID    
        
            
    #def xobj2str(xobj,xnamLst):            
    def prQxUsr(self):
        ''' 输出用户变量保存的数据
            #qxLibName=['date','ID','stkVal','cash','dret','val'];
        '''

        print('\n::qxUsr');
        dss=zwt.xobj2str(self.qxUsr,qxLibName);
        print(dss,'\n')
        
        
    def prQLib(self):
        ''' 输出各种回溯交易测试数据，一般用于结束时
            #qxLibName=['date','ID','stkVal','cash','dret','val'];
        '''
    
#        print('')
#        self.prQxUsr();
#        print('::qxUsr.stk',self.prjName)
#        print(self.qxUsrStk)
#        print('::xtrdLib',self.fn_xtrdLib)
#        #print(self.xtrdLib.tail())
#        print(self.xtrdLib)
#        print('')
#        print('::qxLib.head',self.fn_qxLib)
#        #print(self.qxUsr);
#        print(self.qxLib.head())
#        print('')
#        print('::qxLib.tail')
#        print(self.qxLib.tail())
#        print('')
        
    def prTrdLib(self):
        ''' 输出xtrdLib、xtrdNilLib 各种实盘、空头交易数据，一般用于结束时
            
        '''
        print('\n::xtrdNilLib 空头交易')
        print(self.xtrdNilLib)
        print('\n::xtrdLib 实盘交易',self.fn_xtrdLib)
        print(self.xtrdLib)
        

class zwDatX(object):
    ''' 设置各个数据目录，用于zwDat项目
        Args:
            Csv数据源。
            (datetime, open, close, high, low, volume)
    '''

    def __init__(self,rs0=_rdat0):  
        #----tick5.rss
        self.rdat=rs0;                  #   \zwDat\
        self.rtickTim=rs0+'tick\\';  #   \zwDat\ticktim\  2012-01\
        self.rtickTimMon=self.rtickTim+'2010-01\\';  #   \zwDat\ticktim\  2012-01\
        # xxx.lib
        self.stkCodeLib=[]
        # fn_xxx
        self.fn_stkCode=''
        
        #--xtim.xxx
        self.xtimTick0="09:00"
        self.xtimTick9="15:00"
        #
        self.xtimSgn=""
        self.xtim0Sgn=""
        self.xtim9Sgn=""
        self.xday0k="2005-01-01"
        self.xday9k=""
        self.xdayNum=0
        self.xdayInx=0
        self.DTxtim9=None
        self.DTxtim0=None
        self.DTxtim=None
        #self.xtim9=""
        #self.xtim0=""
        #  code.xxx
        self.code=""
        self.codeSgn=""
        self.codeCnt=0
        self.codeNum=0
        self.codeInx0k=-1
        #
        self.rmin0k=_rdatMin;
        self.rminWrk=self.rmin0k+'M05\\'
        
        #self.fn_min=[]
        self.min_ksgns=['05','15','30','60'] #分时数据时间模式列表，一般是[5，15，30，60]，也可以自行设置
        self.min_ksgnWrk='M05'
        self.min_knum=5
        #self.min_kdat=[5,15,30,60]
        ###
        self.datTick=[]
        self.datMin={} #pd.DataFrame(columns=qxMinName);

        
        
        
        #self.xday0=''
        #self.xtickAppNDay=3      #tick装换时，追加模式下，默认追加的日期文件数
        #self.xtickAppFlag=False  #默认=False，tick数据追加模式标志,如果=True,强行将所有tick文件转换为分时数据
        #self.xday0ChkFlag=True   #  默认=True，如果qx.xday0ChkFlag=Flase，强制从xday0k日开始抓取数据，主要用于用于补漏
        
        
        
        #---------
        self.rTmp=_rTmp;        
        self.rdat=rs0;       
        
        self.rdatCN=_rdatCN;
        self.rdatUS=_rdatUS;
        self.rdatInx=_rdatInx;
        
        
        self.rdatZW=_rdatZW;
        self.rZWcnXDay=_rdatZW+"cnXDay\\"
        self.rZWcnDay=_rdatZW+"cnDay\\"
        self.rZWusDay=_rdatZW+"usDay\\"
        #
        self.rDay=rs0+"day\\" 
        self.rXDay=rs0+"xday\\"
        
        #self.rDay9=rs0+"day9\\" #?????
        
        #  min.dat
        #self.rTick=_rdatMin+"tick\\"

        #
        
        #
        #self.datTick=pd.DataFrame(columns=qxTickNameNew,index=['date']);
        #self.datTick.dropna(inplace=True);
        
        #self.datM05.dropna(inplace=True);
        #self.datM15=pd.DataFrame(columns=qxMinName);
        #self.datM30=pd.DataFrame(columns=qxMinName);
        #self.datM60=pd.DataFrame(columns=qxMinName);
        #
        #
          
    def prDat(self):  
        ''' 输出相关数据目录
        '''
      
        print('')
        print('rTmp,',self.rTmp)        
        
        print('rdat,',self.rdat)
        print('rdatCN,',self.rdatCN)
        print('rdatUS,',self.rdatUS)
        print('rdatInx,',self.rdatInx)
        
        print('')
        print('rdatZW,',self.rdatZW)
        print('rZWcnXDay,',self.rZWcnXDay)
        print('rZWcnDay,',self.rZWcnDay)
        print('rZWusDay,',self.rZWusDay)
        
        print('')
        print('XDay,',self.rXDay)
        #print('Day9,',self.rDay9)
        print('Day,',self.rDay)
        
        #print('')
        #print('rdatMin,',self.rdatMin)
        
        print('')
        print('code,',self.code)
        print('name,',self.codeSgn)
