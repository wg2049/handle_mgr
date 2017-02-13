# MySQL group replication 节点添加、节点删除、MGR状态检查、数据库起停工具
程序名：handle_mgr

### 程序结构：
```
handle_mgr/
|-- bin/
|   |-- __init__.py
|   |-- handle_mgr.py
|
|-- core/
|   |-- __init__.py
|   |-- main.py  
|-- conf/
|   |-- mgr.conf   ##handle_mgr配置文件
|   |-- example_mgr.conf  ##参考配置文件
|-- README

```

### 运行环境：
    Python3.0或以上版本环境均可。


### 执行方法：
    python3 handle_mgr.py
	
### 使用方法：
    1) 编辑配置文件conf/mgr.conf，以下为配置文件参数解析:
	  ##[mgr]必须存在
	  [mgr]
	  ##以下为MySQL实例登陆用户、密码、socket、MySQL程序的basedir、MySQL实例默认配置文件名
	  ##用户需要根据自己实际情况更改
      user = root    
      password = mysql   
      socket = /tmp/mysql3307.sock
      basedir = /usr/local/mysql57
      defaults-file = /57data/my.cnf
      
      ##以下为MySQL group replication相关的参数配置
	  ##用户需要根据实际情况更改。
      transaction_write_set_extraction = XXHASH64     
      loose-group_replication_group_name = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      loose-group_replication_start_on_boot = off
      loose-group_replication_local_address = "10.0.0.11:33071"
      loose-group_replication_group_seeds = "10.0.0.11:33071,10.0.0.13:33071,10.0.0.14:33071"
      loose-group_replication_bootstrap_group = off
      
	  ##以下为MySQL group replication内部通讯的用户及密码，
	  ##该用户由本程序创建，不需要提前创建，添加节点前若存在该用户会报错。
      mgr_user = 'rpl_user'@'%'
      mgr_password = rpl_pass
	  
    2) 根据系统提示输入需要的操作类型。
	   1 : Check the MGR status
       2 : Add MGR member
       3 : Delete MGR member
       4 : Start MySQL instance
       5 : Stop MySQL instance
       6 : Start GROUP_REPLICATION
       7 : Stop GROUP_REPLICATION
       8 : Exit

