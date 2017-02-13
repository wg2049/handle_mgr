#!/usr/bin/env  python3
# author: wugong
import re
import os
import configparser
import shutil
import datetime
import pymysql
import time

def stop_instance(cf_file):  ##stop mysql instance 关闭实例
    config = configparser.ConfigParser()
    config.read(cf_file)
    BASEDIR = config['mgr']['basedir']
    USER = config['mgr']['user']
    PASS = config['mgr']['password']
    SOCKET = config['mgr']['socket']

    CMD = "cd " + BASEDIR +" ; "+ "bin/mysqladmin " + " -u"+USER+" -p"+PASS+" -S"+SOCKET +" shutdown"
    os.system(CMD)
    print("The instance stopped!")
    return 0

def start_instance(cf_file):   ##startup mysql instance 启动实例
    config = configparser.ConfigParser()
    config.read(cf_file)
    BASEDIR = config['mgr']['basedir']
    DEFAU_FILES = config['mgr']['defaults-file']
    CMD = "cd " + BASEDIR +" ; "+ "bin/mysqld_safe " + " --defaults-file="+ DEFAU_FILES + " &"
    os.system(CMD)
    print("The instance started")

def deal_conf(cf_file):  ##deal the mysql option file，处理MySQL配置文件，对原文件做备份
    mgrconf = configparser.ConfigParser()
    mgrconf.read(cf_file)
    mysql_cf = mgrconf['mgr']['defaults-file']
    now = datetime.datetime.now().strftime("%Y%m%d%H%M")
    newfile = mysql_cf + "_bk_" + now
    shutil.copyfile(mysql_cf, newfile)
    mycnf = configparser.ConfigParser()
    mycnf.read(mysql_cf)
    if not mycnf.has_section('mysqld'):
        mycnf.add_section("mysqld")
    mycnf['mysqld']['gtid_mode'] = 'on'
    mycnf['mysqld']['enforce_gtid_consistency'] = 'ON'
    mycnf['mysqld']['master_info_repository'] = 'TABLE'
    mycnf['mysqld']['relay_log_info_repository'] = 'TABLE'
    mycnf['mysqld']['binlog_checksum'] = 'NONE'
    mycnf['mysqld']['log_slave_updates'] = 'ON'
    mycnf['mysqld']['log_bin'] = 'binlog'
    mycnf['mysqld']['binlog_format'] = 'ROW'
    mycnf['mysqld']['transaction_write_set_extraction'] = mgrconf['mgr']['transaction_write_set_extraction']
    mycnf['mysqld']['loose-group_replication_group_name'] = mgrconf['mgr']['loose-group_replication_group_name']
    mycnf['mysqld']['loose-group_replication_start_on_boot'] = mgrconf['mgr']['loose-group_replication_start_on_boot']
    mycnf['mysqld']['loose-group_replication_local_address'] = mgrconf['mgr']['loose-group_replication_local_address']
    mycnf['mysqld']['loose-group_replication_group_seeds'] = mgrconf['mgr']['loose-group_replication_group_seeds']
    mycnf['mysqld']['loose-group_replication_bootstrap_group'] = mgrconf['mgr']['loose-group_replication_bootstrap_group']
    with open(mysql_cf, 'w') as f:
        mycnf.write(f)

def mgr_status(cf_file):   ##check the mgr status 检查MGR的状态，组成员、primary site.
    mgrconf = configparser.RawConfigParser()
    mgrconf.read(cf_file)
    USER = mgrconf['mgr']['user']
    PASS = mgrconf['mgr']['password']
    SOCKET = mgrconf['mgr']['socket']
    mysqlcon = pymysql.connect(user=USER, password=PASS, unix_socket=SOCKET)
    cur = mysqlcon.cursor()
    def exe_sql(sql_txt):
        cur.execute(sql_txt)
        index = cur.description
        col = []
        for i in index:
            col.append(i[0])
        print("SQL> ",sql_txt)
        print(" ", ', '.join(col), "\n ", "".center(len(str(col)), "-"))
        for i in cur:
            print(" ", re.findall('^\((.+)\)$', str(i))[0].replace("'", ""))
        print("\n\n")
    sql1="SELECT * FROM performance_schema.replication_group_members"
    sql2="select a.* from performance_schema.replication_group_members a,performance_schema.global_status b where a.member_id=b.VARIABLE_VALUE and b.VARIABLE_NAME= 'group_replication_primary_member'"
    print("Check the current group members:")
    exe_sql(sql1)
    print("Check the primary site:")
    exe_sql(sql2)
    cur.close()
    mysqlcon.close()

def add_members(cf_file):  ##create user,change master,install plugin,start group_replication
    mgrconf = configparser.RawConfigParser()
    mgrconf.read(cf_file)
    mgr_user = mgrconf['mgr']['mgr_user']
    mgr_password = mgrconf['mgr']['mgr_password']
    USER = mgrconf['mgr']['user']
    PASS = mgrconf['mgr']['password']
    SOCKET = mgrconf['mgr']['socket']
    mysqlcon = pymysql.connect(user=USER,password=PASS,unix_socket=SOCKET)
    cur = mysqlcon.cursor()
    CR_USER = "CREATE USER " + mgr_user + " IDENTIFIED BY " + "'" + mgr_password + "'"
    GR_USER = "GRANT REPLICATION SLAVE ON *.* TO " + mgr_user
    MASTER_USER=mgr_user.split("@")[0]
    CG_MASTER="CHANGE MASTER TO MASTER_USER="+MASTER_USER+", MASTER_PASSWORD='"+mgr_password+"'  FOR CHANNEL 'group_replication_recovery'"
    print(CG_MASTER)

    cur.execute("SET SQL_LOG_BIN=0")
    cur.execute(CR_USER)
    cur.execute(GR_USER)
    cur.execute(CG_MASTER)
    cur.execute("FLUSH PRIVILEGES")
    cur.execute("SET SQL_LOG_BIN=1")
    cur.execute("INSTALL PLUGIN group_replication SONAME 'group_replication.so'")
    cur.execute("set global group_replication_allow_local_disjoint_gtids_join=on")
    cur.execute("START GROUP_REPLICATION")
    cur.close()
    mysqlcon.close()
    time.sleep(5)
    mgr_status(cf_file)

def del_members(cf_file):  ##stop group replication 关闭group replication
    mgr_status(cf_file)
    mgrconf = configparser.RawConfigParser()
    mgrconf.read(cf_file)
    mgr_user = mgrconf['mgr']['mgr_user']
    mgr_password = mgrconf['mgr']['mgr_password']
    USER = mgrconf['mgr']['user']
    PASS = mgrconf['mgr']['password']
    SOCKET = mgrconf['mgr']['socket']
    DR_USER = "DROP USER " + mgr_user
    mysqlcon = pymysql.connect(user=USER, password=PASS, unix_socket=SOCKET)
    cur = mysqlcon.cursor()
    cur.execute("STOP GROUP_REPLICATION")
    cur.execute("UNINSTALL PLUGIN GROUP_REPLICATION")
    cur.execute("SET SQL_LOG_BIN=0")
    cur.execute(DR_USER)
    cur.execute("SET SQL_LOG_BIN=1")
    cur.close()
    mysqlcon.close()

def start_stop_mgr(cf_file,tag):  ##start group replication 关闭group replication
    mgr_status(cf_file)
    mgrconf = configparser.RawConfigParser()
    mgrconf.read(cf_file)
    mgr_user = mgrconf['mgr']['mgr_user']
    mgr_password = mgrconf['mgr']['mgr_password']
    USER = mgrconf['mgr']['user']
    PASS = mgrconf['mgr']['password']
    SOCKET = mgrconf['mgr']['socket']
    mysqlcon = pymysql.connect(user=USER, password=PASS, unix_socket=SOCKET)
    cur = mysqlcon.cursor()
    if tag == 0:
        cur.execute("STOP GROUP_REPLICATION")
    elif tag == 1:
        cur.execute("START GROUP_REPLICATION")
    cur.close()
    mysqlcon.close()
