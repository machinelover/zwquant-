# -*- coding: utf-8 -*-
"""
Created on Mon Oct  2 22:48:15 2017

@author: ASUS
"""

import numpy as np
import pandas as pd
import matplotlib as mpl
from dateutil.parser import parse
import gdufSys as zw
import zwTools as zwt
import sys,os
from dateutil import rrule

def bt_init(universe,data,sta,money=1000000):
    '''
    初始化zw量化参数，stk股票内存数据库等
    【输入】：
        universe(list): 股票代码列表，例如：['002739','300239']   
        data (str): 股票数据目录
        sta (str): 策略名称
        money (int): 启动资金，默认是：1000000(100w)
        
    【输出】：
        account: 程序化全局变量account
    '''
    account=zw.gdufQuant(sta,money);  
    #------设置各种价格模式：
    #    priceWrk，策略分析时，使用的股票价格，一般是：dprice，复权收盘价
    #    priceBuy，买入/卖出的股票价格，一般是：kprice，一般采用次日的复权开盘价
    #    priceCalc，最后结算使用的股票价格，一般是：adj close，复权收盘价
    account.priceCalc='close';
    account.priceWrk='dprice';
    account.priceBuy='kprice';
    account.security_position=[];#持仓列表
    #----------设置绘图&数据输出格式
    mpl.style.use('seaborn-whitegrid');
    pd.set_option('display.width', 450)
    #-----设置数据源目录等场所，读取股票数据，stkLib
    account.data=data;
    
    if universe=='A':#若选用了全A股
        mmm=account.AllACode
        universe=list(mmm.index)
    #可以自行添加如HS300，ZZ500的板块的股票池，代码如上类似
    
    stkLibRd(universe,data); 

    #大盘指数.设置
    account.stkInxRDat='zwdat\\cn\\xday\\'    #大盘指数数据源路径
    account.stkInxPriceName='close'  #大盘指数数据列名称，默认是:close    
    #大盘指数代码,名称拼音,中文名称
    account.stkInxCode,account.stkInxCName='000001','上证指数'
    
    #  读取股票数据，
    xtim0=parse('9999-01-01');xtim9=parse('1000-01-01');
    for xcod in zw.stkLibCode:
        xt0,xt9=stkLibGetTimX(xcod)
        if xtim0>xt0:xtim0=xt0
        if xtim9<xt9:xtim9=xt9
         
    xtim0=xtim0.strftime('%Y-%m-%d');xtim9=xtim9.strftime('%Y-%m-%d')
    account.qxTimSet(xtim0,xtim9)
    return account
    
def gdufBackTestSonbuy(account):
    '''
    gdufBackTestSon(account):
    回溯测试子函数，测试一只股票code，在指定时间xtim的回溯表现数据
    会调用account.staFun指定的策略分析函数，获取当前的股票交易数目 account.stkNum
    并且根据股票交易数目 account.stkNum，判定是不是有效的交易策略
    【输入】
        account
    【输出】
         无
         '''
    #----运行策略函数，进行策略分析
    account.stkNum=account.staFunbuy(account);
    #----
    if account.stkNum!=0:
        #----检查，是不是有效交易
        flag,account.xtrdChk=xtrdChkFlag(account)
        if flag:
            #----如果是有效交易，加入交易列表
            xtrdLibAdd(account)
        elif account.trdNilFlag:
            xtrdLibNilAdd(account)

def gdufBackTestSonsell(account):            
    account.stkNum=account.staFunsell(account);
    if account.stkNum!=0:
        #----检查，是不是有效交易
        flag,account.xtrdChk=xtrdChkFlag(account)
        if flag:
            #----如果是有效交易，加入交易列表
            xtrdLibAdd(account)
        elif account.trdNilFlag:
            xtrdLibNilAdd(account)

def gdufBackTest(account,day):
    '''
    回溯测试主程序
    【输入】
    	account
    	
    【输出】
         无
         '''
    # 增加数据源波动率参数    
    stkLibSetDVix()
    #计算回溯时间周期，也可以在此，根据nday调整回溯周期长度
    #或者在 qt_init数据初始化时，通过qx.qxTimSet(xtim0,xtim9)，设置回溯周期长度
    nday=account.periodNDay;
    if account.debugMod>0:
        xcod=zw.stkLibCode[0];
        fss='tmp\\'+account.prjName+'_'+xcod+'.csv'
        zw.stkLib[xcod].to_csv(fss)      
    #-------------- 
    #按时间循环，进行回溯测试
    for tc in range(0,nday,day):#这里的20用于调仓频率
        xtim=account.cal[0+tc]
        
        #每个测试时间点，开始时，清除qx相关参数
        account.qxTim0SetVar(xtim);  
        xpriceFlag=False;  #有效交易标志Flag
        #按设定的股票代码列表，循环进行回溯测试
        Code=[]
        if len(account.AllACode.index)>len(zw.stkLibCode):
            Code1=list(account.AllACode[account.AllACode[xtim]==1].index)
            Code2=zw.stkLibCode
            Code=[i for i in Code1 if i in Code2]
        else:
            Code=list(account.AllACode[account.AllACode[xtim]==1].index)#选择当天开市的股票
        #STcode=list(account.ST[account.ST['secShortName'].str.contains('S')==True].index)#剔除ST股
        #Code=[i for i in Code if i not in STcode]
        account.buylist,account.selllist=account.handle_data(account,Code)
        print(xtim)
        for xcod in account.selllist:
            account.stkCode=str(xcod);    
            #xdatWrk是当前xcod，=stkLib[xcod]
            #xbarWrk是当前时间点的stkLib[xcod]
            #注意,已经包括了，qt_init里面的扩充数据列
            if account.stkCode in list(account.AllACode[account.AllACode[xtim]==1].index):
                account.xbarWrk,account.xdatWrk=xbarGet8TimExt(account.stkCode,account.xtim);
                if not account.xbarWrk[account.priceWrk].empty:
                    #-----dvix 波动率检查  
                    dvix=stkGetVars(account,'dvix');
                    dvixFlag=zwt.xinEQ(dvix,account.dvix_k0,account.dvix_k9)or(dvix==0)or(np.isnan(dvix))
                    if dvixFlag:
                        xpriceFlag=True
                        # 调用回溯子程序，如果是有效交易，设置成功交易标志xtrdFlag
                        gdufBackTestSonsell(account)
                        
                    else:
                    
                        pass;
        if len(account.xtrdLib['cash'])!=0:
            account.money=account.xtrdLib['cash'].values[-1]
        for xcod in account.buylist:
            account.stkCode=str(xcod);    
            #xdatWrk是当前xcod，=stkLib[xcod]
            #xbarWrk是当前时间点的stkLib[xcod]
            #注意,已经包括了，qt_init里面的扩充数据列
            account.xbarWrk,account.xdatWrk=xbarGet8TimExt(account.stkCode,account.xtim);
            if not account.xbarWrk[account.priceWrk].empty:
                #-----dvix 波动率检查  
                dvix=stkGetVars(account,'dvix');
                dvixFlag=zwt.xinEQ(dvix,account.dvix_k0,account.dvix_k9)or(dvix==0)or(np.isnan(dvix))
                if dvixFlag:
                    xpriceFlag=True
                    # 调用回溯子程序，如果是有效交易，设置成功交易标志xtrdFlag
                    gdufBackTestSonbuy(account)
                    
                else:
                
                    pass;
        account.money=account.xtrdLib['cash'].values[-1]
        securityMinus(account,list(account.xtrdLib['code'][account.xtrdLib['chichangnum']<=0][account.xtrdLib['date']==xtim]))
        securityADD(account,list(account.xtrdLib['code'][account.xtrdLib['num']>0][account.xtrdLib['date']==xtim]))
        #如果所有股票代码列表循环完毕，成功交易标志为真
        #在当前测试时间点终止，设置有关交易参数
        
        if xpriceFlag:
            account.wrkNDay+=1
            account.qxTim9SetVar(account.xtim);
    print(account.xtrdLib)#交易记录

    
def securityMinus(account,xtrdLib):
    account.security_position=[i for i in account.security_position if i not in xtrdLib]
   

def securityADD(account,xtrdLib):
    account.security_position=list(set(account.security_position) | set(xtrdLib))
    
  
def sta_dataPre0xtim(account,xnam0):
    ''' 策略参数设置子函数，根据预设时间，裁剪数据源stkLib
    
    Args:
        qx (zwQuantX): zwQuantX数据包 
        xnam0 (str)： 函数标签

    '''

    #设置当前策略的变量参数
    account.staName=xnam0
    account.rfRate=0.05;  #无风险年收益，一般为0.05(5%)，计算夏普指数等需要
    #qx.stkNum9=20000;   #每手交易，默认最多20000股
    #
    #按指定的时间周期，裁剪数据源
    xt0k=account.staVars[-2];xt9k=account.staVars[-1];
    if (xt0k!='')or(xt9k!=''):
        #xtim0=parse('9999-01-01');xtim9=parse('1000-01-01');
            #xtim0=xtim0.strftime('%Y-%m-%d');xtim9=xtim9.strftime('%Y-%m-%d')
        if xt0k!='':
            if account.xtim0<xt0k:account.xtim0=xt0k;
        if xt9k!='':                
            if account.xtim9>xt9k:account.xtim9=xt9k;
        account.qxTimSet(account.xtim0,account.xtim9)
        stkLibSet8XTim(account.xtim0,account.xtim9);#    print('zw.stkLibCode',zw.stkLibCode)
    
    #---stkInx 读取大盘指数数据，并裁剪数据源
    #print('finx',qx.stkInxCode)
    if account.stkInxCode!='':    
        stkInxLibRd(account)
        stkInxLibSet8XTim(account,account.xtim0,account.xtim9)
        
    #============
    #---设置qxUsr用户变量，起始数据
    account.qxUsr=qxObjSet(account.xtim0,0,account.money,0);

def qxObjSet(xtim,stkVal,dcash,dret):
    ''' 设置 xtrdLib 单次交易节点数据
    
    Args:
        xtim (str): 交易时间
        stkVal (int): 股票总价值
        dcash (int): 资金
        dret (float): 回报率

    '''
    qx10=pd.Series(zw.qxLibNil,index=zw.qxLibName);
    qx10['date']=xtim;qx10['cash']=dcash;
    #stkVal=xbarStkSum(qx10['xBars'],xtim);
    #stkVal=0
    qx10['stkVal']=stkVal;
    qx10['val']=stkVal+dcash;
    
    return qx10;   

def stkInxLibSet8XTim(account,dtim0,dtim9):
    ''' 根据时间段，切割大盘指数数据 zw.stkInxLib
    
    Args:
        dtim0（str）：起始时间
        dtim9（str）:结束时间
            
    :ivar
    zw.stkInxLib，大盘指数数据
    '''
    df10=zw.stkInxLib;
    #print(df10.head())
    if dtim0=='':
        df20=df10;
    else:
        #print (dtim0)
        #print (df10)
        df20=df10[(df10.index>=dtim0)&(df10.index<=dtim9)]
        
    zw.stkInxLib=df20.sort_index();


def stkInxLibRd(account):    
    '''
		读取指定的大盘数据到zw.stkInxLib
		
		Args:
            
    :
    qx.stkInxRDat='\\zwdat\\cn\\xday\\''    #大盘指数数据源路径
    qx.stkInxCode='000001'    #大盘指数代码
    qx.stkInxName='sz001'    #大盘指数名称，拼音
    qx.stkInxCName='上证指数'    #大盘指数中文名称，拼音
    #
    zw.stkInxLib=None  #全局变量，大盘指数，内存股票数据库
    
    '''
    if account.stkInxCode!='':
        fss=account.stkInxRDat+account.stkInxCode+".csv";
        xfg=os.path.exists(fss);
        if xfg:
            df10=pd.read_csv(fss,index_col=0,parse_dates=[0]);
            df10=df2zwAdj(df10)
            zw.stkInxLib=df10.sort_index();

def stkLibSet8XTim(dtim0,dtim9):
    ''' 根据时间段，切割股票数据
    
    Args:
        dtim0（str）：起始时间
        dtim9（str）:结束时间
            
    :ivar xcod (int): 股票代码
    '''
    for xcod in zw.stkLibCode:
        df10=zw.stkLib[xcod]
        if dtim0=='':
            df20=df10;
        else:
            df20=df10[(df10.index>=dtim0)&(df10.index<=dtim9)]
        #
        #zw.stkLibCode.append(xcod);
        zw.stkLib[xcod]=df20.sort_index();
        #print(zw.stkLib[xcod])
        #print(df20)
def stkLibRd(xlst,rdir):    
    '''
		读取指定的股票数据到stkLib，可多只股票，以及股票代码文件名
		
		Args:
        xlst (list): 指定股票代码列表,
          如果xlst参数首字母是'@'，表示是股票代码文件名，而不是代码本身
          用于批量导入股票代码 
        rdir (str)：数据类存放目录 
            
    :ivar xcod (int): 股票代码
    
    '''
    zw.stkLib={}   #全局变量，相关股票的交易数据
    zw.stkLibCode=[]  #全局变量，相关股票的交易代码
    

    for xcod in xlst:
        fss=rdir+str(xcod)+".csv";
        xfg=os.path.exists(fss);
        if xfg:
            df10=pd.read_csv(fss,index_col=0,parse_dates=[0]);
            df10=df2zwAdj(df10)
            zw.stkLib[str(xcod)]=df10.sort_index();
            zw.stkLibCode.append(str(xcod));

def stkLibGetTimX(xcod):
    '''
    返回指定股票代码首个、末个交易日时间数据
    
    Args:
        xcod (int): 股票代码
        '''
    d10=zw.stkLib[xcod]
    d01=d10.index;
    xtim0=d01[0];
    xtim9=d01[-1];
    #xtim0s=xtim0.strftime()
    
    return xtim0,xtim9
    
def xtrdChkFlag(account):
    ''' 检查是不是有效交易
    
    Args:
        account: zwQuantX数据包
        #account.stkNum，>0，买入股票；<0，卖出股票；-1；卖出全部股票
        #预设参数：account.qxUsr 
    
    Return：
        xfg,True,有效交易；False，无效交易
        b2：有效交易的数据包 Bar
        
    :ivar xnum (int): 用户持有资产总数
    '''

    kfg=False;b2=None;account.trdNilFlag=False;  
    dcash9=account.qxUsr['cash'];
    dnum=account.stkNum;dnum5=abs(dnum);
    numFg=zwt.xinEQ(dnum5,account.stkNum0,account.stkNum9)
   
    if dnum>0:
        
        kprice=stkGetVars(account,account.priceBuy)  
        dsum=kprice*(dnum-divmod(dnum,100)[1]);
        #股票买入股票总数，必须在限额内：100-2w手，总值不能超过现金数，买空需修改此处
        if numFg:
            if dsum<dcash9:
                account.stkNum=int(dnum-divmod(dnum,100)[1])
                kfg=True
            elif (dsum-kprice*100)<dcash9:
                account.stkNum=int(dnum-divmod(dnum,100)[1]-100)
                dsum=dsum-kprice*100
                kfg=True
            else:account.trdNilFlag=True;      
    else:
        if account.stkCode in account.qxUsrStk:
            
            xnum=account.qxUsrStk[account.stkCode] 
            if dnum==-1:
                account.stkNum=-xnum;
                kfg=True;
            else:
                kfg=zwt.iff2(dnum5<=xnum,True,False);
            #    
            account.trdNilFlag=not kfg; 
        elif dnum!=-1:    
            account.trdNilFlag=True;   

    #        
    if kfg or account.trdNilFlag:
        b2=xtrdObjSet(account);	#设置交易节点                 
    else:
        account.stkNum=0;
        
    
    return kfg,b2;
    
def xtrdLibAdd(account):
    ''' 添加交易到 xtrdLib
    
    Args:
       account

    '''

    account.qxIDSet();
    
    account.xtrdChk['ID']=account.qxID;
    
    xusr4xtrd(account,account.xtrdChk);#qx.qxUsr['cash']=qx.qxUsr['cash']-b2['sum']
    account.xtrdLib=account.xtrdLib.append(account.xtrdChk.T,ignore_index=True)
    
def xtrdLibNilAdd(account):
    ''' 添加交易到空头记录 xtrdNilLib
    
    Args:
        account

    '''
    account.xtrdChk['ID']='nil';
    account.xtrdNilLib=account.xtrdNilLib.append(account.xtrdChk.T,ignore_index=True)  
    
def stkLibSetDVix():
    ''' 根据时间段，切割股票数据
    
    Args:
        dtim0（str）：起始时间
        dtim9（str）:结束时间
            
    :ivar xcod (int): 股票代码
    '''
    for xcod in zw.stkLibCode:
        df10=zw.stkLib[xcod]
        df10['dvix']=df10['dprice']/df10['dprice'].shift(1)*100
        #
        zw.stkLib[xcod]=np.round(df10,2);

def xbarGet8TimExt(xcod,xtim):
    '''  根据指定股票代码。时间，获取数据包及股票数据
    
    Args:
        xcod (int): 股票代码
        xtim (str): 交易时间
        '''

    d10=zw.stkLib[xcod]
    d02=d10[xtim:xtim];
    
    return d02,d10
    
def stkGetVars(account,ksgn):
    '''
      获取股票代码，指定字段的数据
    
    Args:
        account
        ksgn (str): account.stkCode,account.xtim,account.stkSgnPrice 
        '''
    d10=zw.stkLib[account.stkCode]
    d01=d10[account.xtim:account.xtim];
    #
    dval=0;
    if len(d01)>0:
        d02=d01[ksgn]
        dval=d02[0];
    
    return dval
    
def df2zwAdj(df0):
    ''' 股票数据格式转换，转换为 zw 增强版格式，带 adj close
    
    Args:
        df0 (pd.DataFrame): 股票数据
        '''
    
    clst=["open","high","low","close","volume","adj close"]; 
    df2 =pd.DataFrame(columns=clst)
    df0 =df0.rename(columns={'Date':'date','Open':'open','High':'high','Low':'low','Close':'close','Volume':'volume',"Adj Close":"adj close"})
    #df0=df0.round(decimals=2) 
    
    df0['date']=df0.index;
    df2['date']=df0['date'];
    df2['open']=df0['open'];df2['high']=df0['high'];
    df2['low']=df0['low'];df2['close']=df0['close'];
    df2['volume']=df0['volume'];
    #'adj close'
    ksgn='adj close'
    if ksgn in df0.columns:
        df2[ksgn]=df0[ksgn]
    else:
        df2[ksgn]=df0['close'];
        
    #----index
    df2=df2.set_index(['date'])
    
    return df2    
    
def xusr4xtrd(account,b2):    
    ''' 根据交易数据，更新用户数据 qxUsr
    
    Args:
        qx (zwQuantX): zwQuantX数据包
        b2 (pd.Series): 有效交易的数据包 Bar
            
    :ivar xcod (int): 股票代码
    '''

    xcod=b2['code'];
    if xcod!='':
        xfg=xcod in account.qxUsrStk;
        #s2=zwBox.xobj2str(b2,zw.xbarName);print(xfg,'::b2,',s2)
    
        if xfg:
            xnum=account.qxUsrStk[xcod];
            xnum2=xnum+b2['num'];
            account.qxUsrStk[xcod]=xnum2;
            b2['chichangnum']=xnum2
            if xnum2==0:del(account.qxUsrStk[xcod]);
        else:
            account.qxUsrStk[xcod]=b2['num'];
            b2['chichangnum']=account.qxUsrStk[xcod]
        account.qxUsr['cash']=account.qxUsr['cash']-b2['sum']

def xusrStkNum(account,xcod):
    ''' 返回用户持有的 xcod 股票数目
    
    Args:
        qx (zwQuantX): zwQuantX数据包
        xcod (int): 股票代码
        '''

    dnum=0;
    if xcod in account.qxUsrStk:
        dnum=account.qxUsrStk[xcod];
    return dnum
    
def xtrdObjSet(account):
    ''' 设置交易节点数据
    
    Args:
        qx (zwDatX): zwQuant数据包   
    #xtrdName=['date','ID','mode','code','dprice','num','kprice','sum','cash'];
        '''
    b2=pd.Series(zw.xtrdNil,index=zw.xtrdName);
    b2['date']=account.xtim;b2['code']=account.stkCode;b2['num']=account.stkNum;
    if account.stkNum!=0:
        b2['mode']=zwt.iff3(account.stkNum,0,'sell','','buy');
        b2['dprice']=stkGetVars(account,account.priceWrk)
        #kprice=stkGetVars(qx,qx.priceBuy)  
        kprice=stkGetPrice(account,account.priceBuy)  
        b2['kprice']=kprice
        b2['sum']=kprice*account.stkNum;
        dcash9=account.qxUsr['cash'];
        b2['cash']=dcash9-kprice*b2['num']
    
    #print('\nb2\n',b2)
  
    return b2;
    
def stkGetPrice(account,ksgn):
    '''
      获取当前价格
    
    Args:
        qx (zwQuantX): zwQuantX交易数据包
        ksgn (str): 价格模式代码
        '''
    d10=zw.stkLib[account.stkCode]
    d01=d10[account.xtim:account.xtim];
    #
    price=0;
    if len(d01)>0:
        d02=d01[ksgn]
        price=d02[0];
        if pd.isnull(price):
            d02=d01['dprice']
            price=d02[0];
    
    return price    
    
def xusrUpdate(account):
    ''' 更新用户数据
    
    Args:
        qx (zwQuantX): zwQuantX数据包 
        
        '''
        
    account.qxUsr['date']=account.xtim;
    #dcash=qx.qxUsr['cash']
    #qx.qxUsr['cash']=dcash-b2['sum']
    stkVal=stkValCalc(account,account.qxUsrStk); 
    account.qxUsr['stkVal']=stkVal;
    dval0=account.qxUsr['val'];
    dval=account.qxUsr['cash']+stkVal;
    account.qxUsr['val']=dval;
    account.qxUsr['dret']=(account.qxUsr['val']-dval0)/dval0;
    #print('\n::xbarUsr\n',qx.qxUsrStk)
    #print('stkVal',stkVal)
    
    #---------drawdown.xxx
    if dval>account.downHigh:
        account.downHigh=dval;
        account.downLow=dval;
        #qx.downHighTime=date.today();
        account.downHighTime=account.xtim;
        #qx.downHighTime=datetime.dateTime;
    else:
        account.downLow=min(dval,account.downLow);
    #----------    
    account.qxUsr['downHigh']=account.downHigh
    account.qxUsr['downLow']=account.downLow
    kmax=downKMax(account.downLow,account.downHigh);
    account.downKMax=min(account.downKMax,kmax);
    account.qxUsr['downKMax']=account.downKMax;
    #xday=parse(qx.xtim)-parse(qx.downHighTime);
    nday = rrule.rrule(rrule.DAILY,dtstart=parse(account.downHighTime), until=parse(account.xtim)).count()
    
    dmax=max(account.downMaxDay,nday-1)
    account.downMaxDay=dmax
    account.qxUsr['downDay']=account.downMaxDay;  

def downKMax(dlow,dhigh):
    '''
    downKMax(dlow,dhigh):
        回缩率计算函数
        低位，高位，指的是投资组合的市场总值
    【输入】：
    dlow，当前的低位，低水位，也称，lowerWatermark
    dhigh，当前的高位，高水位，也称，highWatermark
    【输出】
    回缩率,百分比数值
    '''
    
    if dhigh>0:
        kmax=(dlow-dhigh)/float(dhigh)*100
    else:
        kmax=0
    
    return kmax
    
def stkValCalc(account,xdicts):
    ''' 计算 xdicts 内所有的股票总价值
    
    Args:
        qx (zwQuantX): zwQuantX数据包
        xdicts (list)：所选股票代码列表 
            
    :ivar xcod (int): 股票代码
    '''
    dsum9=0;
    for xcod,xnum in xdicts.items():
        account.stkCode=xcod;
        #price=stkGetPrice(account,'dprice')
        price=stkGetPrice(account,'close')
        dsum=price*xnum;
        dsum9=dsum9+dsum;
        #print('@c',qx.xtim,price,dsum,dsum9)
        
    return dsum9

    
def stkGetPrice9x(account,ksgn):
    '''
      获取首个、末个交易日数据
    
    Args:
        qx (zwQuantX): zwQuantX交易数据包
        ksgn (str): 价格模式代码
        '''
    d10=zw.stkLib[account.stkCode]
    #d05=d10[qx.stkSgnPrice]
    d05=d10[ksgn]
    price0=d05[0];price9=d05[-1];
    
    return price0,price9
    
def zwRetTradeCalc(account):
    ''' 输出、计算交易数据
    
    Args:
        qx (zwQuantX): zwQuantX数据包
        
        '''
    
    trdNum=len(account.xtrdLib);
    #print('trdNum',trdNum)
    #
    numAdd=0;numDec=0;
    sumAdd=0;sumDec=0;
    xbar=account.qxLib.iloc[-1];
    xtim9=xbar['date']
    for xc in range(trdNum):
        xbar=account.xtrdLib.iloc[xc];
        
        #print(xbar)
        #kprice=xbar['kprice']
        dnum=xbar['num']
        #print('dprice',dprice)
        account.stkCode=xbar['code']
        #qx.xtim=xbar['date']
        price=xbar['kprice']
        #ksgn='dprice';
        
        #price=stkGetPrice(qx,ksgn);
        account.xtim=xtim9;ksgn=account.priceCalc;
        price0,price9=stkGetPrice9x(account,ksgn);
        #print(qx.stkCode,dprice,'$',dprice0,dprice9)
        #---
        #if dnum>0:sumPut=sumPut+price*dnum;
        #if dnum<0:sumGet=sumGet+price9*dnum;:
        #
        dsum=dnum*(price9-price);
        #料敌从宽，平局，考虑到交易成本，作为亏损处理，
        if dsum>0:
            numAdd+=1;sumAdd=sumAdd+dsum;
        else:
            numDec+=1;sumDec=sumDec+dsum;
            
                    
        #print('trdNum',trdNum,numAdd,numDec,'$',dprice,dprice9,sumAdd,sumDec)
    #---------
    sum9=sumAdd+sumDec;#sumx=sumPut+sumGet;
    print('交易总次数：%d' %trdNum)
    print('交易总盈利：%.2f' %sum9)
    #print('交易总支出：%.2f' %sumPut)
    #print('交易总收入：%.2f' %sumGet)
    #print('交易收益差：%.2f' %sumx)
    print('')
    print('盈利交易数：%d' %numAdd)
    print('盈利交易金额：%.2f' %sumAdd)
    print('亏损交易数：%d' %numDec)
    print('亏损交易金额：%.2f' %sumDec)
    #print('@t',qx.xtim)
    account.xtim=xtim9
    
def zwRetPr(account):
    ''' 输出、计算回报率
    
    Args:
        qx (zwQuantX): zwQuantX数据包

    '''    
    #---回报测试
    
    retAvg=np.mean(account.qxLib['dret']);
    retStd=np.std(account.qxLib['dret']);
    dsharp=sharpe_rate(account.qxLib['dret'],account.rfRate)
    dsharp0=sharpe_rate(account.qxLib['dret'],0)
    dcash=account.qxUsr['cash'];
    dstk=stkValCalc(account,account.qxUsrStk); 
    dval=dstk+dcash;
    dret9=(dval-account.mbase)/account.mbase
    
    
    print('')
    print("最终资产价值 Final portfolio value: $%.2f" % dval)
    print("最终现金资产价值 Final cash portfolio value: $%.2f" % dcash)
    print("最终证券资产价值 Final stock portfolio value: $%.2f" % dstk)
    print("累计回报率 Cumulative returns: %.2f %%" % (dret9*100))
    print("平均日收益率 Average daily return: %.3f %%" %(retAvg*100))
    print("日收益率方差 Std. dev. daily return:%.4f " %(retStd))
    print('')
    print("夏普比率 Sharpe ratio: %.3f,（%.2f利率）" % (dsharp,account.rfRate))    
    print("无风险利率 Risk Free Rate: %.2f" % (account.rfRate))
    print("夏普比率 Sharpe ratio: %.3f,（0利率）" % (dsharp0))    
    print('')
    print("最大回撤率 Max. drawdown: %.4f %%" %(abs(account.downKMax)))
    print("最长回撤时间 Longest drawdown duration:% d" %account.downMaxDay);
    print("回撤时间(最高点位) Time High. drawdown: " ,account.downHighTime)
    print("回撤最高点位 High. drawdown: %.3f" %account.downHigh)
    print("回撤最低点位 Low. drawdown: %.3f" %account.downLow)
    print('')
    print("时间周期 Date lenght: %d (Day)" %account.periodNDay)
    print("时间周期（交易日） Date lenght(weekday): %d (Day)" %account.wrkNDay)
    
    print("开始时间 Date begin: %s" %account.xtim0)
    print("结束时间 Date lenght: %s" %account.xtim9)
    print('')
    print("项目名称 Project name: %s" % account.prjName)    
    print("策略名称 Strategy name: %s" % account.staName)    
    print("股票代码列表 Stock list: ",zw.stkLibCode)    
    print("策略参数变量 staVars[]: ",account.staVars)    
    print('')
    
def sharpe_rate(rets,rfRate,ntim=252):
    '''
    sharpe_rate(rets,rfRate,ntim=252):
        计算夏普指数
    【输入】
    	rets (list): 收益率数组（根据ntim，按日、小时、保存）
      rfRate (int): 无风险收益利润
      ntim (int): 交易时间（按天、小时、等计数）
         采用小时(60分钟)线数据，ntim= 252* 6.5 = 1638.
    【输出】
        夏普指数数值
        '''
    rsharp= 0.0
    if len(rets):
        # print('rets',rets)
        rstd = np.array(rets).std(ddof=1) #np.stddev(rets, 1)  #收益波动率
        #print('rstd',rstd,rets[-1]) #,returns[]
        if rstd != 0:
            rfPerRet = rfRate / float(ntim)
            rmean=np.array(rets).mean()
            avgExRet = rmean - rfPerRet
            dsharp = avgExRet / rstd
            rsharp = dsharp * np.sqrt(ntim)
            #print('rmean,avgExRet,dsharp',rmean,avgExRet)
            #print('dsharp,rshapr',dsharp,rsharp) 
    return rsharp
      