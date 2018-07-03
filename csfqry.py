#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""remote shell"""

import sys
import os
import time
# import multiprocessing
import subprocess
import Queue
import signal
import getopt
# import cx_Oracle as orcl
import socket
import json
# import hostdirs
# from multiprocessing.managers import BaseManager
# import pexpect
# import pexpect.pxssh
import base64
import logging
import re
# import sqlite3
# from config import *

reload(sys)
sys.setdefaultencoding('utf8')

class Conf(object):
    def __init__(self, cfgfile):
        self.cfgFile = cfgfile
        self.logLevel = None
        self.aClient = []
        self.fCfg = None
        self.csfDir = None

    def loadLogLevel(self):
        try:
            fCfg = open(self.cfgFile, 'r')
        except IOError, e:
            print('Can not open configuration file %s: %s' % (self.cfgFile, e))
            exit(2)
        for line in fCfg:
            line = line.strip()
            if len(line) == 0:
                continue
            if line[0] == '#':
                continue
            if line[:8] == 'LOGLEVEL':
                param = line.split(' = ', 1)
                logLevel = 'logging.%s' % param[1]
                self.logLevel = eval(logLevel)
                break
        fCfg.close()
        return self.logLevel

    def loadCsfDir(self):
        try:
            fCfg = open(self.cfgFile, 'r')
        except IOError, e:
            print('Can not open configuration file %s: %s' % (self.cfgFile, e))
            exit(2)
        for line in fCfg:
            line = line.strip()
            if len(line) == 0:
                continue
            if line[0] == '#':
                continue
            if line[:6] == 'csfdir':
                param = line.split(' = ', 1)
                csfDir = param[1]
                self.csfDir = csfDir
                break
        fCfg.close()
        return self.csfDir

    def openCfg(self):
        if self.fCfg: return self.fCfg
        try:
            self.fCfg = open(self.cfgFile, 'r')
        except IOError, e:
            logging.fatal('can not open configue file %s', self.cfgFile)
            logging.fatal('exit.')
            exit(2)
        return self.fCfg

    def closeCfg(self):
        if self.fCfg: self.fCfg.close()

    def loadClient(self):
        # super(self.__class__, self).__init__()
        # for cli in self.aClient:
        #     cfgFile = cli.
        try:
            fCfg = open(self.cfgFile, 'r')
        except IOError, e:
            logging.fatal('can not open configue file %s', self.cfgFile)
            logging.fatal('exit.')
            exit(2)
        clientSection = 0
        client = None
        for line in fCfg:
            line = line.strip()
            if len(line) == 0:
                clientSection = 0
                if client is not None: self.aClient.append(client)
                client = None
                continue
            if line == '#provisioning client conf':
                if clientSection == 1:
                    clientSection = 0
                    if client is not None: self.aClient.append(client)
                    client = None

                clientSection = 1
                client = Centrex()
                continue
            if clientSection < 1:
                continue
            logging.debug(line)
            param = line.split(' = ', 1)
            if param[0] == 'server':
                client.serverIp = param[1]
            elif param[0] == 'sockPort':
                client.port = param[1]
            elif param[0] == 'GLOBAL_USER':
                client.user = param[1]
            elif param[0] == 'GLOBAL_PASSWD':
                client.passwd = param[1]
            elif param[0] == 'GLOBAL_RTSNAME':
                client.rtsname = param[1]
            elif param[0] == 'GLOBAL_URL':
                client.url = param[1]
        fCfg.close()
        logging.info('load %d clients.', len(self.aClient))
        return self.aClient

    def loadEnv(self):
        # super(self.__class__, self).__init__()
        # for cli in self.aClient:
        #     cfgFile = cli.
        try:
            fCfg = open(self.cfgFile, 'r')
        except IOError, e:
            logging.fatal('can not open configue file %s', self.cfgFile)
            logging.fatal('exit.')
            exit(2)
        envSection = 0
        client = None
        for line in fCfg:
            line = line.strip()
            if len(line) == 0:
                continue
            if line == '#running envirment conf':
                if clientSection == 1:
                    clientSection = 0
                    if client is not None: self.aClient.append(client)
                    client = None

                clientSection = 1
                client = KtClient()
                continue
            if clientSection < 1:
                continue
            logging.debug(line)
            param = line.split(' = ', 1)
            if param[0] == 'prvnName':
                client.ktName = param[1]
            elif param[0] == 'dbusr':
                client.dbUser = param[1]
            elif param[0] == 'type':
                client.ktType = param[1]
            elif param[0] == 'dbpwd':
                client.dbPwd = param[1]
            elif param[0] == 'dbhost':
                client.dbHost = param[1]
            elif param[0] == 'dbport':
                client.dbPort = param[1]
            elif param[0] == 'dbsid':
                client.dbSid = param[1]
            elif param[0] == 'table':
                client.orderTablePre = param[1]
            elif param[0] == 'server':
                client.syncServer = param[1]
            elif param[0] == 'sockPort':
                client.sockPort = param[1]
        fCfg.close()
        logging.info('load %d clients.', len(self.aClient))
        return self.aClient


class ReHost(object):
    def __init__(self, hostName, hostIp):
        self.hostName = hostName
        self.hostIp = hostIp
        self.dUser = {}

    def setUser(self, user, passwd, prompt):
        self.dUser[user] = (passwd, prompt)


class ReCmd(object):
    def __init__(self, user, aCmds):
        self.user = user
        self.aCmds = aCmds


# class RemoteSh(multiprocessing.Process):
#     def __init__(self, reCmd, reHost, logPre):
#         multiprocessing.Process.__init__(self)
#         self.reCmd = reCmd
#         self.host = reHost
#         self.logPre = logPre
#
#     def run(self):
#         logging.info('remote shell of host %s running in pid:%d %s', self.host.hostName, os.getpid(), self.name)
#         clt = pexpect.pxssh.pxssh()
#         flog = open('%s_%s.log' % (self.logPre, self.host.hostName), 'a')
#         flog.write('%s %s starting%s' % (time.strftime("%Y%m%d%H%M%S", time.localtime()), self.host.hostName, os.linesep))
#         flog.flush()
#         clt.logfile = flog
#         # clt.logfile = sys.stdout
#         logging.info('connect to host: %s %s %s', self.host.hostName, self.host.hostIp, self.reCmd.user)
#         # print 'connect to host: %s %s %s' % (self.host.hostName, self.host.hostIp, self.reCmd.user)
#
#         # plain_pw = base64.decodestring(user_pw)
#         # con = clt.login(float_ip,user_name,plain_pw)
#         con = clt.login(self.host.hostIp, self.reCmd.user, self.host.dUser[self.reCmd.user][0])
#         logging.info('connect: %s', con)
#         cmdcontinue = 0
#         for cmd in self.reCmd.aCmds:
#             logging.info('exec: %s', cmd)
#             # print 'exec: %s' % (cmd)
#             cmd = cmd.replace('$USER', self.reCmd.user)
#             if cmd[:5]=='su - ':
#                 suUser = cmd.split(' ')[2]
#                 suPwd = self.host.dUser[suUser][0]
#                 su = self.doSu(clt, cmd, suPwd)
#                 if su:
#                     continue
#                 else:
#                     logging.fatal('cmd su error,exit')
#                     break
#
#             if cmd[:5] == 'su ex':
#                 self.suExit(clt)
#                 continue
#             clt.sendline(cmd)
#             if cmd[:2] == 'if':
#                 cmdcontinue = 1
#             if cmd[0:2] == 'fi':
#                 cmdcontinue = 0
#             if cmdcontinue == 1:
#                 continue
#             clt.prompt()
#             logging.info('exec: %s', clt.before)
#         clt.logout()
#         flog.write('%s %s end%s' % (time.strftime("%Y%m%d%H%M%S", time.localtime()), self.host.hostName, os.linesep))
#         flog.close()
#
#     def doSu(self, clt, suCmd, pwd, auto_prompt_reset=True):
#         clt.sendline(suCmd)
#         i = clt.expect([u'密码：', 'Password:',pexpect.TIMEOUT,pexpect.EOF])
#         if i==0 or i==1:
#             clt.sendline(pwd)
#             i = clt.expect(["su: 鉴定故障", r"[#$]", pexpect.TIMEOUT])
#         else:
#             clt.close()
#             # raise pexpect.ExceptionPxssh('unexpected su response ')
#             return False
#         if i==1:
#             pass
#         else:
#             clt.close()
#             raise pexpect.ExceptionPxssh('unexpected login response')
#         if auto_prompt_reset:
#             if not clt.set_unique_prompt():
#                 clt.close()
#                 raise pexpect.ExceptionPxssh('could not set shell prompt '
#                                      '(received: %r, expected: %r).' % (
#                                          clt.before, clt.PROMPT,))
#         return True
#
#     def suExit(self, clt):
#         clt.sendline('exit')
#         clt.prompt()

# class ReShFac(object):
#     def __init__(self, main, cmdfile):
#         self.main = main
#         self.cmdFile = cmdfile
#         self.group = main.group
#         self.hosts = main.hosts
#         # self.dest = dest
#
#     def loadCmd(self):
#         logging.info('create cmd from %s', self.cmdFile)
#         fCmd = self.main.openFile(self.cmdFile,'r')
#         if not fCmd: return None
#         i = 0
#         user = None
#         aCmds = []
#         for line in fCmd:
#             line = line.strip()
#             if len(line) == 0:
#                 continue
#             if line[0] == '#':
#                 continue
#             i += 1
#             if i == 1:
#                 aUser = line.split()
#                 if len(aUser) < 2:
#                     logging.error('comd no user,exit!')
#                     exit(1)
#                 if aUser[0] == 'user':
#                     user = aUser[1]
#                 else:
#                     logging.error('no user of 1st line in %s', self.cmdFile)
#                     exit(1)
#                 continue
#             aCmds.append(line)
#         fCmd.close()
#         cmd = ReCmd(user, aCmds)
#         return cmd
#
#     def makeReSh(self, host, cmd):
#         logging.info('create remote shell of %s', host.hostName)
#         reSh = RemoteSh(cmd, host, self.main.logPre)
#         return reSh
#
#     def loadHosts(self):
#         conn = sqlite3.connect('kthosts.db')
#         cursor = conn.cursor()
#         if len(self.group) > 0:
#             groupName = "','".join(self.group)
#             groupName = "'%s'" % groupName
#             sql = 'select hostname from grouphosts where groupname in (%s)' % groupName
#             cursor.execute(sql)
#             hostrows = cursor.fetchall()
#             for row in hostrows:
#                 self.hosts.append(row[0])
#             logging.info('group hosts: %s', self.hosts)
#
#         sql = ''
#         hostName = None
#         if len(self.hosts) > 0:
#             hostName = "','".join(self.hosts)
#             hostName = "'%s'" % hostName
#             sql = 'SELECT hostname,hostip FROM kthosts where state = 1 and hostname in (%s)' % hostName
#         else:
#             sql = 'SELECT hostname,hostip FROM kthosts where state = 1'
#         logging.info('load host sql: %s', sql)
#         cursor.execute(sql)
#         rows = cursor.fetchall()
#         dHosts = {}
#         for row in rows:
#             host = ReHost(*row)
#             dHosts[row[0]] = host
#         # cursor.close()
#         logging.info('host: %s', dHosts.keys())
#         if hostName:
#             userSql = 'select hostname,user,passwd,prompt from hostuser where hostname in (%s)' % hostName
#         else:
#             userSql = 'select hostname,user,passwd,prompt from hostuser'
#         cursor.execute(userSql)
#         rows = cursor.fetchall()
#         for row in rows:
#             hostName = row[0]
#             user = row[1]
#             passwd = row[2]
#             prompt = row[3]
#             # logging.debug(row)
#             if hostName in dHosts:
#                 dHosts[hostName].setUser(user, passwd, prompt)
#             else:
#                 logging.warning('no host of %s', hostName)
#
#         cursor.close()
#         conn.close()
#         return dHosts
#
#     def startAll(self):
#         logging.info('all host to connect: %s' , self.aHosts)
#         # aHosts = self.aHosts
#         # pool = multiprocessing.Pool(processes=10)
#         for h in self.aHosts:
#             # h.append(self.localIp)
#             if h[1] == self.localIp:
#                 continue
#             logging.info('run client %s@%s(%s)' , h[2], h[0], h[1])
#             self.runClient(*h)
#             # pool.apply_async(self.runClient,h)
#         # pool.close()
#         # pool.join()
#
#     def getLocalIp(self):
#         self.hostname = socket.gethostname()
#         logging.info('local host: %s' ,self.hostname)
#         self.localIp = socket.gethostbyname(self.hostname)
#         return self.localIp
#     def getHostIp(self):
#         self.hostName = socket.gethostname()
#         try:
#             s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#             s.connect(('8.8.8.8', 80))
#             ip = s.getsockname()[0]
#             self.hostIp = ip
#         finally:
#             s.close()
#         return ip

class CsfTool(object):
    def __init__(self, main, cmd=None):
        self.main = main
        self.outTotal = main.outTotal
        self.outDetail = main.outDetail
        self.fTotal = main.openFile(self.outTotal, 'w')
        self.fDetail = main.openFile(self.outDetail, 'w')
        self.csfLog = main.csfLogFile
        self.fCsfLog = main.openFile(self.csfLog, 'a')
        self.workPath = '/app/aitask/jinhr/tranbill/tools'
        self.oldWorkPath = None
        self.aExcluId = []
        self.cmd = 'java -Dcsf.client.name=web-ac-yyt -Djava.ext.dirs=./csfTest_lib csfTest.MainClient'
        if cmd:
            self.cmd = cmd
        self.propertyFile = 'csf_client.properties'
        self.dProperty = {'INPUT_TYPE':'java.lang.String',
                          'INPUT_STRING':'{"billId":"%s","acctId":"","validDate":"%s","expireDate":""}',
                          'CSF_CODE':'ams_IBJFreeResCSV_queryShareTerminalFreeResOther',
                          'OUTPUT_TYPE':'java.lang.String'}
        self.dPatt = {'10start':r'[main] () (MainClient.java:26 xxxx canceled ',
                      '20callend':r'[main] () (ClientStub.java:110)',
                      '30outstart':r'[main] () (MainClient.java:85)',
                      '40outend':r'[main] () (MainClient.java:90)'}

    def setWorkEnv(self):
        self.oldWorkPath = os.getcwd()
        os.chdir(self.workPath)

    def setNum(self, aNum):
        self.aNum = aNum

    def makeProperty(self):
        fPrp = self.main.openFile(self.propertyFile, 'w')
        logging.debug(self.aNum)
        for key in self.dProperty:
            strProp = self.dProperty[key]
            if key == 'INPUT_STRING':
                strProp = strProp % self.aNum
                # strProp = strProp % tuple(self.aNum)
            fPrp.write('%s=%s%s' % (key, strProp, os.linesep))
        fPrp.close

    def query(self):
        logging.debug(self.cmd)
        # f = subprocess.Popen((self.cmd), stdout=subprocess.PIPE).stdout
        try:
            f = os.popen(self.cmd)
        except Exception, e:
            logging.info('%s error: %s', self.cmd, e)
        finded = 0
        # logging.info(self.dPatt)
        for line in f:
            # line = unicode(line)
            self.fCsfLog.write(line)
            if finded == 1:
                if line.find(self.dPatt['40outend']) > -1:
                    finded = 0
                    continue
                self.parseCsf(line)
            for key in sorted(self.dPatt.keys()):
                patt = self.dPatt[key]
                if line.find(patt) > -1:
                    logging.debug(line)
                    if key == '30outstart':
                        finded = 1
                    elif key == '40outend':
                        finded = 0
                    break
        exitValue = f.close()
        if exitValue:
            logging.error('%s error: %s',self.aNum[0], exitValue)

    def parseCsf(self, line):
        line = unicode(line, 'utf-8')
        line = line.strip()
        infoLen = len(line)
        line = line[1:infoLen - 1]
        line = line.replace(u'\\', u'')
        logging.debug(line)
        aInfo = json.loads(line)
        logging.debug(json.dumps(aInfo, encoding="UTF-8", ensure_ascii=False))
        resBalance = 0
        total = 0
        logging.debug('aInfo %s %d', type(aInfo), len(aInfo))
        for dInfo in aInfo:
            # logging.debug(dInfo)
            if dInfo['resUnit'] == 'KB':
                if dInfo['resFreeType'] in self.aExcluId:
                    logging.info('excluded: %d', dInfo['resFreeType'])
                    continue
                balance = int(dInfo['totalResFree']) - int(dInfo['totalResUsed'])
                resBalance += balance
                total += dInfo['totalResFree']
                # billid,prodId,validDate,expireDate,totalResFree,totalResUsed,balance,prodName,resFreeName,resFreeType,
                logging.debug(json.dumps(dInfo, encoding="utf-8", ensure_ascii=False))
                outDetail = '%s,%d,%s%s' % (self.aNum[0], balance, json.dumps(dInfo, encoding="UTF-8", ensure_ascii=False), os.linesep)
                self.fDetail.write(outDetail)
                # self.fDetail.write(u'%s,%d,%s,%s,%d,%d,%d,%s,%s,%d%s' % (self.aNum[0], dInfo['prodId'], dInfo['validDate'], dInfo['expireDate'], dInfo['totalResFree'], dInfo['totalResUsed'], balance, dInfo['prodName'], dInfo['resFreeName'], dInfo['resFreeType'], os.linesep))

        # sOut = json.dumps(aInfo, encoding="UTF-8", ensure_ascii=False)
        # bill_id,total,totalbalance
        self.fTotal.write(u'%s,%d,total=%d%s' % (self.aNum[0], total, resBalance, os.linesep))

    # def parseCsf(self, line):
    #     line = line.strip()
    #     # line = unicode(line,'utf-8')
    #     # line = line.decode('utf-8')
    #     line = line.replace(u'\\', u'')
    #     infoLen = len(line)
    #     # sInfo = "'%s'" % line[1:infoLen-1]
    #     sInfo = line[1:infoLen - 1]
    #     cmd = u'aInfo = %s' % sInfo
    #     aInfo = eval(cmd)
    #     # line = line.replace('},{', '|')
    #     # aInfo = line.split('|')
    #     logging.debug(aInfo)
    #     resBalance = 0
    #     for info in aInfo:
    #         logging.debug(info)
    #         dInfo = eval(info)
    #         # dInfo = info
    #         if dInfo['resUnit'] == 'KB':
    #             balance = int(dInfo['totalResFree']) - int(dInfo['totalResUsed'])
    #             resBalance += balance
    #     self.fOut.write(u'%s %s %d %s%s' % (self.aNum[0], self.aNum[1], resBalance, aInfo, os.linesep))

    # def parseCsf(self, line):
    #     line = line.strip()
    #     line = unicode(line,'utf-8')
    #     # line = line.decode('utf-8')
    #     line = line.replace(r'\"', '')
    #     # infoLen = len(line)
    #     # # sInfo = "'%s'" % line[1:infoLen-1]
    #     # sInfo = line[1:infoLen - 1]
    #     # cmd = 'aInfo = %s' % sInfo
    #     # aInfo = eval(cmd)
    #     line = line.replace('},{', '|')
    #     aInfo = line.split('|')
    #     logging.debug(aInfo)
    #     resBalance = 0
    #     for info in aInfo:
    #         logging.debug(info)
    #         # # dInfo = eval(info)
    #         # dInfo = info
    #         # if dInfo['resUnit'] == 'KB':
    #         #     balance = int(dInfo['totalResFree']) - int(dInfo['totalResUsed'])
    #         #     resBalance += balance
    #         aRow = info.split(',')
    #         isRes = 0
    #         total = 0
    #         used = 0
    #         balance = 0
    #         for pa in aRow:
    #             aPa = pa.split(':')
    #             if aPa[0] == 'resUnit' and aPa[1] == 'KB':
    #                 isRes = 1
    #             if aPa[0] == 'totalResFree':
    #                 total = int(aPa[1])
    #             if aPa[0] == 'totalResUsed':
    #                 used = int(aPa[1])
    #         if isRes == 1:
    #             balance = total - used
    #             resBalance += balance
    #             # print('%d - %d = %d  total: %d' % (total, used, balance, resBalance))
    #     sOutInfo = u'},{'.join(aInfo)
    #     # print(sOutInfo)
    #     self.fOut.write(u'%s %s %d %s%s' % (self.aNum[0], self.aNum[1], resBalance, sOutInfo, os.linesep))
    #     # self.fOut.write('%s' % aInfo)

    def exit(self):
        self.fTotal.close()
        self.fDetail.close()
        self.fCsfLog.close()
        os.chdir(self.oldWorkPath)


class Director(object):
    def __init__(self, main, csfClient):
        self.main = main
        self.csfClient = csfClient
        self.inFile = main.inFile
        self.fIn = main.openFile(self.inFile, 'r')
        self.aExcluId = []

    def saveOrderRsp(self, order):
        self.fRsp.write('%s %s\r\n' % (order.dParam['BILL_ID'], order.getStatus()))

    def loadExcludeId(self):
        fExl = self.main.openFile(self.main.excludeFile, 'r')
        aExclu = []
        for line in fExl:
            line = line.strip()
            aId = line.split()
            aExclu.append(int(aId[0]))
        fExl.close()
        aSorted = sorted(aExclu)
        self.aExcluId = aSorted
        self.csfClient.aExcluId = aSorted
        logging.debug(aSorted)

    def start(self):
        self.loadExcludeId()
        logging.info('csf tool starting...')
        self.csfClient.setWorkEnv()

        for line in self.fIn:
            line = line.strip()
            if len(line) == 0:
                continue
            aNum = line.split()
            timeStr = time.strftime("%Y%m%d%H%M%S", time.localtime())
            tPara = (aNum[0], timeStr)
            logging.debug('query %s', tPara)
            self.csfClient.setNum(tPara)
            self.csfClient.makeProperty()
            self.csfClient.query()
            # time.sleep(1)
        self.csfClient.exit()
        logging.info('csf tool complete.')


class Main(object):
    def __init__(self):
        self.Name = sys.argv[0]
        self.baseName = os.path.basename(self.Name)
        self.argc = len(sys.argv)
        self.inFile = None
        self.excludeFile = 'excludeid.cfg'
        self.csfDir = None
        self.cfgFile = None

    def parseWorkEnv(self):
        dirBin, appName = os.path.split(self.Name)
        self.dirBin = dirBin
        # print('0 bin: %s   appName: %s    name: %s' % (dirBin, appName, self.Name))
        appNameBody, appNameExt = os.path.splitext(appName)
        self.appNameBody = appNameBody
        self.appNameExt = appNameExt

        if dirBin=='' or dirBin=='.':
            dirBin = '.'
            dirApp = '..'
            self.dirBin = dirBin
            self.dirApp = dirApp
        else:
            dirApp, dirBinName = os.path.split(dirBin)
            if dirApp=='':
                dirApp = '.'
                self.dirBin = dirBin
                self.dirApp = dirApp
            else:
                self.dirApp = dirApp

        # self.dirLog = os.path.join(self.dirApp, 'log')
        self.dirCfg = os.getcwd()
        # self.dirTpl = os.path.join(self.dirApp, 'template')
        # self.dirLib = os.path.join(self.dirApp, 'lib')
        self.dirLog = os.getcwd()
        self.dirOut = os.getcwd()

        self.today = time.strftime("%Y%m%d", time.localtime())
        inBaseFile = os.path.basename(self.inFile)
        if self.cfgFile:
            cfgName = self.cfgFile
        else:
            cfgName = '%s.cfg' % self.appNameBody
        logName = '%s_%s.log' % (self.inFile, self.today)
        csfLogName = '%s_%s.csflog' % (inBaseFile, self.today)
        outTotalName = '%s.total' % inBaseFile
        outDetailName = '%s.detail' % inBaseFile
        logPre = '%s_%s' % (self.appNameBody, self.today)
        self.cfgFile = os.path.join(self.dirCfg, cfgName)
        self.logFile = os.path.join(self.dirLog, logName)
        self.csfLogFile = os.path.join(self.dirLog, csfLogName)
        self.outTotal = os.path.join(self.dirOut, outTotalName)
        self.outDetail = os.path.join(self.dirOut, outDetailName)

    def checkArgv(self):
        if self.argc < 2:
            self.usage()
        # self.checkopt()
        argvs = sys.argv

        # self.group = []
        # self.hosts = []
        # try:
        #     opts, arvs = getopt.getopt(argvs, "g:h:")
        # except getopt.GetoptError, e:
        #     print 'get opt error:%s. %s' % (argvs, e)
        #     # self.usage()
        # for opt, arg in opts:
        #      if opt == '-g':
        #         self.group = arg.split(',')
        #      elif opt == '-h':
        #          self.hosts = arg.split(',')
        if self.argc == 3:
            self.cfgFile = argvs[1]
            self.inFile = argvs[2]
        elif self.argc == 2:
            self.inFile = argvs[1]

    def usage(self):
        print "Usage: %s [cfgfile] infile" % self.baseName
        print "example:   %s %s %s" % (self.baseName, 'csfqry.cfg1', 'datafile')
        exit(1)

    def openFile(self, fileName, mode):
        try:
            f = open(fileName, mode)
        except IOError, e:
            logging.fatal('open file %s error: %s', fileName, e)
            return None
        return f

    def start(self):
        self.checkArgv()
        self.parseWorkEnv()

        self.cfg = Conf(self.cfgFile)
        self.logLevel = self.cfg.loadLogLevel()
        # self.logLevel = logging.DEBUG

        logging.basicConfig(filename=self.logFile, level=self.logLevel, format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y%m%d%I%M%S')
        logging.info('%s starting...' % self.baseName)

        self.csfDir = self.cfg.loadCsfDir()
        csf = CsfTool(self)
        if self.csfDir:
            csf.workPath = self.csfDir
        director = Director(self, csf)
        director.start()


# main here
if __name__ == '__main__':
    main = Main()
    main.start()
    logging.info('%s complete.', main.baseName)
