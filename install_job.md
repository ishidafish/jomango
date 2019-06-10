<h3>0.Python必要模组</h3>

```bash
pip3 install cx_oracle
pip3 install watchdog
pip3 install mysql-connector-python
pip3 install requests
pip3 install configparser
```
<h3>1.安装程序</h3>
create folder , unzip jobman.zip

```bash
INSTALL_SRC = jobman.zip
INSTALL_DIR = FOLDER_NAME
mkdir ${INSTALL_DIR}
cp ${INSTALL_SRC} ${INSTALL_DIR}
cd ${INSTALL_DIR}
unzip ${INSTALL_SRC}
```
Makefile中,[tag]jobman_install有描述此过程。<br>
结果目录结构是是：
```
.
├── config.ini
├── equeue
│   └── 00
├── fish
│   ├── catch.py
│   └── __init__.py
├── iqueue
│   └── 00
├── jobman.py
├── mom
│   ├── insert_abc.sql
│   ├── item_master.sql
│   ├── posupld.sql
│   └── sqrt.sql
└── oqueue
    └── 00
```
档案简单描述:<br>
jobman.py 是主执行程序<br>

config.ini 是设定环境的档案，后面详叙之<br>
<div>
[mom]是集合所有对[目的数据库]的SQL Script目录，需在config.ini中设定，让jobman知道该往哪找SQL Script
</div>

<div>
[iqueue] 接收Client端进来的指令档，jobman在iNotify发生<font color=#FF0000> ON_CREATED </font> event时执行<br>
</div>

[oqueue] 正确执行过后，指令档会迁移至此<br>

[equeue] 执行有误过后，指令档会迁移至此<br> 

<div>
<font color=#ff0000>
com.daphne.jobman.quit</font><br>
<font color=#0000ff>
com.daphne.jobman.restart </font>
是两个特殊的档案，若进入监视的目录，将会使jobman quit 或是 restart<br>
</div>
<h3>2.设定config.ini</h3>

```ini
[DEFAULT]
# 决定使用哪个 子目录的 SQL
destination=mom
```
此处就是前面所提及的目的数据库的设定名称，因此可以是有不同的目的数据库，但是，一个jobman执行时,只会根据此设定使用一个目的
```ini
# mysql or sqlite3 ,决定使用 [resultdb_sqlite3] or [resultdb_mysql]
resultdb=mysql
iqueue=iqueue
oqueue=oqueue
equeue=equeue
```
resultdb的选项是mysql or sqlite3,sqlite3是开发的时候懒得去架设一个正经的数据库临时用的储存，所以mysql才是正式的选项。<br>

iqueue 是输入request files的目录,其下又有子目录才是jobman真正监看的目录，预设是00，可以从上面的tree看到<br>

oqueue，equeue其下目录结构必须与iqueue一样，分别代表着，执行成功及执行失败的话request file最后的去处，有助于发生问题时debug。
```ini
[mom]
usr=cmx
pwd=cmx
# 区分 正式 测试 从configParse读的时候 只药 tns 根据DAPHNE_ENV来决定 postfix
tns_product=momprd
tns_develop=momdev
# SQL 所在资料夹
env=mom
rowcommit=False 
```
由前面destination所指定的目的数据库的设定<br>
其中tns_product，tns_develop的选择由系统环境参数DAPHNE_ENV决定，若有设定<br>
export DAPHNE_ENV=PRODUCT<br>
则会使用tns_product,否则均使用tns_develop<br>

env 设定SQL Script的目录<br>

rowCommit 待说明request file内容时再描述之。
```ini
## another destination example
[momdev]
usr=cmx
pwd=cmx
# 区分 正式 测试 从configParse读的时候 只药 tns 根据DAPHNE_ENV来决定 postfix
tns_product=momprd
tns_develop=momdev
# SQL 所在资料夹
env=mom
rowcommit=False 
```
其他的目的数据库的范例
```ini
####
# 测试的时候 用local 的 sqlite3,只要更改default.resultdb值sqlite3，就可以使用这里
[resultdb_sqlite3]
# 区分 正式 测试
host_product=192.168.188.66
host_develop=127.0.0.1 
usr=jobman
pwd=ilovelulu
dbs=jobman
create_table=CREATE TABLE messages( 
    sql varhar(32),
    dir varchar(32),
    uuid varchar(64),
    seq number,
    message varchar(2048),
    timestamp varchar(64))
create_index=CREATE INDEX idx_messages  ON messages(uuid)
insert=INSERT INTO messages VALUES(?, ? , ? , ? , ? , datetime("now","localtime"))
select=SELECT sql,seq,message from messages 
    WHERE uuid=:uuid and (seq=:seq or :seq is null) 
    order by seq,timestamp desc
```
以上这段只在开发过程中使用过，可以忽视
```ini
[resultdb_mysql]
# 区分 正式 测试
host_product=192.168.188.66
host_develop=192.168.188.66
usr=nana
pwd=anan
dbs=jobman
create_database=CREATE DATABASE jobman DEFAULT CHARACTER SET 'utf8'
use_database=USE jobman
# 也许该使用 master-detail,以后再说
create_table=CREATE TABLE `messages` (
    `sql` varchar(32) DEFAULT NULL,
    `dir` varchar(32) DEFAULT NULL,
    `uuid` varchar(64) DEFAULT NULL,
    `seq` int(11) DEFAULT NULL,
    `message` varchar(16384) DEFAULT NULL,
    `timestamp` datetime DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB DEFAULT CHARSET=utf8

create_index=ALTER TABLE `jobman`.`messages` ADD INDEX `messages_uuid` (`uuid` ASC)
insert=INSERT INTO `jobman`.`messages`(`sql`,`dir`,`uuid`,`seq`,`message`) VALUES( %s, %s , %s , %s , %s)
select=SELECT `sql`,`seq`,`message` from `jobman`.`messages` WHERE `uuid`=%(uuid)s and ( `seq`=%(seq)s or %(seq)s is null) order by `seq`,`timestamp` desc
```
虽然很多，但是目的很单纯<br>
将执行的结果，储存在DB(<b>必须设定好</b>)，供Client查询
```ini
[client]
# 区分 正式 测试
postURL_product= http://192.168.188.66/job/add.php
postURL_develop= http://127.0.0.1/job/add.php

```
以后说

