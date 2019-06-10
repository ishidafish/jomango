from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import cx_Oracle, json, os, datetime
import sqlite3
import signal
import mysql.connector
import requests
import configparser

'''
参数的范例
params : 
[
    {   "sql" : "posupld",
        "rows": [
            {"ITEM":"1014303091143220",
             "LOC":"1001000189",
             "TRAN_DATE":"2018-04-01",
             "SALE_QTY":-10,
             "SALE_AMT":80,
             "ERROR_MESSAGE":"" },
            {"ITEM":"1014303091143225",
             "LOC":"1001000189",
              "TRAN_DATE":"2018-04-01",
              "SALE_QTY":-11,
              "SALE_AMT":90,
              "ERROR_MESSAGE":""}
        ]
    }
    {   "sql" : "posupld",
        "rows": [
            {"ITEM":"1014303091143220",
             "LOC":"1001000189",
             "TRAN_DATE":"2018-04-01",
             "SALE_QTY":-10,
             "SALE_AMT":80,
             "ERROR_MESSAGE":"" },
            {"ITEM":"1014303091143225",
             "LOC":"1001000189",
              "TRAN_DATE":"2018-04-01",
              "SALE_QTY":-11,
              "SALE_AMT":90,
              "ERROR_MESSAGE":""}
        ]
    }
]
'''

class screen:
    def __init__(self):
        pass
        self.save_cursor=False
    def cls(self):
        self.echo("c")
    def echo(self,code, msg='' ,code_1=''):
        print(chr(27),code,msg,('' if code_1 =='' else chr(27)+code_1),sep='')
    def reverse(self,msg):
        self.echo("[7m",msg,"[0m")

# 取得设定参数
class config:
    def __init__(self,iniFile='config.ini'):
        try:
            self.env = 'PRODUCT' if os.environ.get('DAPHNE_ENV')=='PRODUCT' else 'DEVELOP'
        except:
            self.env = 'DEVELOP'
        self.cfg = configparser.ConfigParser(interpolation=None)
        try:
            self.cfg.read(iniFile)
        except:
            print('读取设定档错误')
            return
        self.destination=self.cfg['DEFAULT']['destination']
        self.resultdb= 'resultdb_' + self.cfg['DEFAULT']['resultdb']
    def get(self, section, option):
        key =  option+'_'+ self.env if option.lower() in ('tns','host','posturl') else option
        try:
            return self.cfg[section][key]
        except:
            return None
    def __str__(self):
        return json.dumps(self.cfg, ensure_ascii=False,indent=None)
        
# 预设是使用当前目录下面的 config.ini
cfg=config()

# 控制 监视LOOP 的变数
start_momo, go_momo , momo, Ctrl_C = True, True, None, True


# 20180806 加上对Ctrl_C的控制
def signal_handler(signal,frame):
    # 使用 signal的原因是，可能在某些时候，我们并不要被keyboard干扰%%%
    global start_momo, go_momo, momo, Ctrl_C
    if not Ctrl_C :
        print('忽略Ctrl_C',end='',flush=True)
        return
    keyin = input("\n选择==>\n  :q 结束\n  :r 重启\n")
    if keyin ==':q': # 跟vi的指令相同,复杂一些，避免误动作
        start_momo, go_momo=False, False
    elif keyin ==':r':
        start_momo, go_momo=True, False

## 指定 Ctrl_C的控制Procedure
signal.signal(signal.SIGINT,signal_handler)


# 监控的主角,监控 path下面的 档案建立,唯一的參數就是subFolder的名稱(idx)，act=server or client
class FileObserver(Observer):
    global cfg
    def __init__(self, idx, act):
        Observer.__init__(self) 
        self.schedule(FileEventHandler(idx,act), cfg.get('DEFAULT','iqueue')+"/"+idx , False)
    def __del__(self):
        Observer.stop(self)
        Observer.join(self)
        del self


# 监控事件的处理分配,此处只处理了 建立好的档案
class FileEventHandler(FileSystemEventHandler):
    global cfg
    def __init__(self,idx,act):
        FileSystemEventHandler.__init__(self)
        #指定reqFile的所有將來存放位置
        self.ipath,self.opath,self.epath = cfg.get('DEFAULT','iqueue')+"/"+idx,cfg.get('DEFAULT','oqueue')+"/"+idx,cfg.get('DEFAULT','equeue')+"/"+idx
        self.reqs = reqs(idx,act) #reqs是處理reqFile的主程序，此處設定reqs瞄準監視folder(同self.ipath)
        for remainfile in os.listdir(self.ipath): ## 先找残余档案 做一遍 %%%
            file_path = os.path.join(self.ipath, remainfile)
            if not os.path.isdir(file_path):
                self.process(remainfile, check=True) ## check 若已經在(uid+seq)結果表有資料，就skip
    def on_moved(self, event):
        pass #format(event.src_path, event.dest_path)
    def on_created(self, event):
        global Ctrl_C, start_momo, go_momo # 20180806加上对 Ctrl_C的控制
        Ctrl_C = False # 执行中，不让Ctrl_C干扰
        if not event.is_directory:
            fn= os.path.basename(event.src_path)
            # 20180808 使用档案来控制主程序的 结束及重启
            # 使用某个特殊档案 filename 来 1.重启 2.结束 jobman, 
            # 如 com.daphne.jobman.restart,com.daphne.jobman.quit
            if fn=='com.daphne.jobman.restart':
                start_momo, go_momo=True, False
                # 在主程序 负责将class 消灭，这里不处理了
                os.rename(self.ipath+'/'+fn, self.opath+'/'+fn+'_'+datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') )
            elif fn=='com.daphne.jobman.quit':
                start_momo, go_momo=False, False
                os.rename(self.ipath+'/'+fn, self.opath+'/'+fn+'_'+datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') )
            else:
                self.process(fn, check=False) # 跟__init__时不同，既然是新建立的reqFile不需检查存在与否(有可能是retry)
        Ctrl_C = True
    def on_deleted(self, event):
        pass
    def on_modified(self, event):
        pass
    def process(self,fin, ext='req',check=False):
        fns,c = fin.split('.'),check
        try:
            if fns[1]==ext:
                print("-> 处理档案 "+ fns[0])
                self.reqs.process(fns[0],check=c) ## 这里
                os.rename(self.ipath+'/'+fin, self.opath+'/'+fin )
            else:
                print("档案类型不符:",fin )
                os.rename(self.ipath+'/'+fin, self.epath+'/'+fin )
        except:
            if os.path.exists(self.ipath+'/'+fin):
                os.rename(self.ipath+'/'+fin, self.epath+'/'+fin )
            print("档案类型不对,或是处理有错误:",fin)
    def __del__(self):
        del self.reqs
        del self


def getreq(dir, filename, ext=".req"):
    reqString, reqList = '', []
    try:
        with open(dir + '/' + filename + ext, 'r') as fin:
            reqString = fin.read()
    except:
        print("request档案无法开启")
        return(False)
    try:
        reqList=json.loads(reqString)
    except:
        print("request内容格式不符规定")
        return(False)
    return reqList

# 连接DB,执行请求
# 目前只有oracle

class oradb():
    global cfg
    maxRow = 50
    def __init__(self,usr=cfg.get(cfg.destination,'usr'),pwd=cfg.get(cfg.destination,'pwd'),tns=cfg.get(cfg.destination,'tns')):
        self.connection = cx_Oracle.connect(usr, pwd, tns)   
        self.cursor = self.connection.cursor()
        self.sqlcache, self.sqlString = {}, ''
    def reconnect(self,usr=cfg.get(cfg.destination,'usr'),pwd=cfg.get(cfg.destination,'pwd'),tns=cfg.get(cfg.destination,'tns')):
        # 发生断线时，重新建立， 但是如何捕捉断线，是个好问题，以后说
        self.cursor.close()
        self.connection.close()
        self.connection = cx_Oracle.connect(usr, pwd, tns)   
        self.cursor = self.connection.cursor()
        self.sqlcache, self.sqlString = {}, ''
    def getsql(self, dir, filename, ext=".sql"):
        path = dir+'/'+filename
        try:
            self.sqlString = self.sqlcache[path] # 尽可能的使用sqlcache,而不file IO
            return self.sqlString
        except:
            try:
                with open(path + ext, 'r') as fin:
                    self.sqlString = fin.read()
                self.sqlcache[path] = self.sqlString
                return self.sqlString
            except:
                self.sqlString = ''
                return  self.sqlString
    def query(self, sql_index, params):
        self.cursor.prepare(self.getsql(cfg.destination , sql_index))
        self.title, self.results, all_success = list(), list(), True
        for p in params:
            if not all_success:
                self.results.append([False,"前面的执行步骤已经产生错误，之后的不再执行"])
                continue
            self.result, self.rowcount, pb = [], 0, {}
            for k,v in p.items(): # cx_oracle能被我用成这样，佩服我自己((((((((()))))))))
                pb[k] = self.cursor.var(cx_Oracle.STRING if type(v)==type('霓') else cx_Oracle.NUMBER)
                pb[k].setvalue(0,v)
            try:
                rows = self.cursor.execute(None, pb) 
                if self.cursor.description== None: # SQL类型【不是】SELECT，这里是执行PL/SQL
                    ret = dict((k,v.getvalue()) for k,v in pb.items())
                    # 要从procedure里面 返回的 :error_message 决定执行成功与否，再决定flag true/false
                    # 如果 flag是 false，同样的 all_success 也是 false, 还没做。。。 
                    try:
                        return_message = ret['ERROR_MESSAGE']
                    except: 
                        return_message = None
                    if return_message is None:
                        flag=True
                        if cfg.get(cfg.destination,'rowcommit'):
                            self.connection.commit()
                    else:
                        flag, all_success =False , False
                        self.connection.rollback()
                    self.results.append([flag, ret])
                else: # SQL类型【是】SELECT，这里是执行 查询SQL, 两者要返回的结果不一样的
                    self.title = list(x[0] for x in self.cursor.description)
                    #想看看怎么存结果。。。。sqlite3 or mysql or csv
                    #一个sql会有多个resultset。这样的组合会晕,我想想
                    for row in rows:
                        if self.rowcount >= oradb.maxRow:
                            break
                        else:
                            self.result.append(dict(zip(self.title, row)))  
                            self.rowcount += 1
                    self.results.append(self.result)
            except cx_Oracle.DatabaseError as err:
                all_success = False
                error, = err.args
                self.results.append([False,{'ERROR_MESSAGE': error.message}])
                self.connection.rollback()
        
        # 整个params 全部做完 commit, 可能要改为判断全部都没错误 才commit, 否则rollback
        # 但是 现在没有一个判断对错的 准则，所以先挂着，不做这判断%%%(使用:error_message=‘’是种方式)
        # results 里面的 每个都是 true，整个params所执行的 才做commit,否则全部rollback
        if all_success:
            self.connection.commit() 
        else:
            self.connection.rollback() 

        self.results_json = json.dumps(self.results, ensure_ascii=False,indent=None)
    def __str__(self):
        return self.results_json
    def querycsv(self, sql_name, p):
        sqlstring=self.getsql(cfg.destination,sql_name)
        if len(sqlstring)>0:
            self.cursor.prepare(sqlstring)
        else:
            print("sql档案不存在")
            return 
        # csv的档案名称
        self.filename = sql_name +'_'+datetime.datetime.now().strftime('%Y%m%d%H%M%S')+ '.csv'
        fout=open(self.filename,'w')
        # pb应该由sqlstring里面找出参数，并初始为''...先不管
        self.rowcount, pb = 0, {}
        if p is not None:
            for k,v in p.items(): # cx_oracle能被我用成这样，佩服我自己((((((((()))))))))
                pb[k] = self.cursor.var(cx_Oracle.STRING if type(v)==type('霓') else cx_Oracle.NUMBER)
                pb[k].setvalue(0,v)
        rows = self.cursor.execute(None, pb) 
        # 制作CSV
        dummy = ','.join(list(x[0] for x in self.cursor.description))
        fout.write(dummy + "\n") # 标题
        print(dummy)
        for row in rows:
            dummy=','.join(str(x) if x is not None else '' for x in row)
            fout.write(dummy + "\n") #内容
            print(dummy)
        fout.close()
        print(self.filename+' done')
    def __del__(self):
        self.cursor.close()
        self.connection.close()
        del self

# 处理*.req档案里面所有的指令
class reqs():
    global cfg
    def __init__(self,idx,act):
        self.act=act
        if act=='server':
            self.db = oradb()
        # 建立了目标DB的连接，及处理结果的DB    
        self.path, self.act = cfg.get('DEFAULT','iqueue')+"/"+idx, act
        self.logdb = sql3(idx) if cfg.get('DEFAULT','resultdb')=='sqlite3' else msqldb(idx)
    def process(self, uid,check=False):
        reqList, seq = getreq(self.path, uid) , 0
        if self.act=='server':
            for req in reqList:
                # 颗粒是每个param，而没有到param里面的 rows %%%，到时候看看，懒得再细腻下去了
                # 若要细腻到 rows， 那就要到oradb那个class去insert logdb
                if check and self.logdb.exists(uid,seq):
                    print("已经处理过了的 uid:{0} seq:{1}".format(uid, seq))
                else:
                    # 抓取錯誤信息，如果TIMEOUT的話，reconnect，再執行，沒人發現，還沒做
                    self.db.query(req['sql'], req['rows']) # 真正做事的人，就是這行
                    print(req['sql'],self.db)  # 在stdout输出
                    self.logdb.insert(req['sql'],uid,seq,self.db.results_json) 
                seq += 1
            return(True)
        else: ## client 动作不完整，先搁着
            postData = {'params': json.dumps(reqList, ensure_ascii=False)}
            response = requests.post(cfg.get('client','postURL'), data=postData)
            print(response.text)
    def __del__(self):
        if self.act=='server':
            del self.db
        del self.logdb
        del self

# 储存处理*.req的结果      
# 先使用sqlite3,後來看看是否有必要改為mysql
class sql3():
    global cfg
    def __init__(self,idx):
        self.sql3name, self.idx =cfg.get('DEFAULT','iqueue') + '/' + idx + '_log.db' , idx
        if os.path.exists(self.sql3name):
            print("sqlite3> 重新开启记录当", self.sql3name)
            self.dbconn = sqlite3.connect(self.sql3name,check_same_thread = False)
            self.cursor = self.dbconn.cursor()
        else:
            print("sqlite3> 新建记录当", self.sql3name)
            self.dbconn = sqlite3.connect(self.sql3name,check_same_thread = False)
            self.cursor = self.dbconn.cursor()
            self.cursor.execute(cfg.get(cfg.resultdb,'create_table'))
            self.cursor.execute(cfg.get(cfg.resultdb,'create_index'))
        self.cursor.execute('PRAGMA journal_mode = wal')
        self.cursor.execute('PRAGMA synchronous = OFF')
        self.insertString,self.queryString=cfg.get(cfg.resultdb,'insert'),cfg.get(cfg.resultdb,'select')
        self.cursor.execute(self.insertString, ('START',self.idx,'0','0','START'))
        self.results_json = None
        self.dbconn.commit()
    def insert(self,sql,uid,seq,message):
        print("sqlite3> 记录档加入 "+sql, message)
        self.cursor.execute(self.insertString, (sql,self.idx, uid, seq, message))
        self.dbconn.commit()
    def query(self,uid,seq=None):
        temp=list()
        self.cursor.execute(self.queryString, (uid,seq))
        self.results=self.cursor.fetchall() # select [sql],[seq],[message] from messages order by seq,timestamp desc
        for rs in self.results:
            try:
                temp1 = json.loads(rs[2])
            except:
                temp1 = (rs[2],)
            temp.append( [rs[0],rs[1],temp1] )
        self.results_json = json.dumps(temp, ensure_ascii=False,indent=True)
    def exists(self,uid,seq=None):
        #此處只檢查uid是否已經存在，看看是否有必要使用uid+seq,先掛著，因為有可能reqFile只做了一半
        self.cursor.execute(self.queryString, (uid,seq))
        return( True if len(self.cursor.fetchall())>=1 else False)
    def __str__(self):
        return self.results_json    
    def __del__(self):
        self.cursor.close()
        self.dbconn.close()
        del self

class msqldb():
    global cfg
    def __init__(self,idx,host=cfg.get(cfg.resultdb,'host'), usr=cfg.get(cfg.resultdb,'usr'),pwd=cfg.get(cfg.resultdb,'pwd'),dbs=cfg.get(cfg.resultdb,'dbs')): 
        self.schema, self.tablename , self.idx= dbs, 'messages' , idx 
        print("mysql> 开启记录当", self.schema, self.tablename)
        self.dbconn = mysql.connector.connect(user=usr,password=pwd,host=host)
        self.cursor =  self.dbconn.cursor()
        # use schema
        try:
            self.cursor.execute(cfg.get(cfg.resultdb,'create_database'))
        except:
            self.cursor.execute(cfg.get(cfg.resultdb,'use_database'))
        # test table exists
        try:
            self.cursor.execute(cfg.get(cfg.resultdb,'create_table'))
            self.cursor.execute(cfg.get(cfg.resultdb,'create_index'))
        except:
            print('mysql> MESSAGES TABLE 已经存在')
        self.insertString,self.queryString=cfg.get(cfg.resultdb,'insert'),cfg.get(cfg.resultdb,'select')
        self.cursor.execute(self.insertString,('START',self.idx,'0',0,'START'))
        self.dbconn.commit()
    def insert(self,sql,uid,seq,message):
        print("mysql> 记录加入 "+ sql ,message)
        self.cursor.execute(self.insertString, (sql,self.idx, uid, seq, message))
        self.dbconn.commit()
    def query(self,uid,seq=None):
        temp=list()
        self.cursor.execute(self.queryString, {'uuid':uid,'seq':seq})
        self.results=self.cursor.fetchall() 
        for rs in self.results:  
            try:
                temp1 = json.loads(rs[2])
            except:
                temp1 = (rs[2],)
            temp.append( [rs[0],rs[1],temp1] )
        self.results_json = json.dumps(temp, ensure_ascii=False,indent=None)
    def exists(self,uid,seq=None):
        #此處只檢查uid是否已經存在，看看是否有必要使用uid+seq,先掛著，因為有可能reqFile只做了一半
        self.cursor.execute(self.queryString, (uid,seq))
        return( True if len(self.cursor.fetchall())>=1 else False)
    def __str__(self):
        return self.results_json


if __name__ == "__main__":
    pass

