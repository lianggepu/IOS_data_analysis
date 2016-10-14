#coding: utf-8
import sqlite3
import paramiko
import time
import os
import commands,hashlib
from biplist import *

#从手机自动提取所需文件或目录
def scp2(ip,password):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip,22,"root", password)
        ssh.exec_command("mkdir /dump")
        ssh.exec_command('cp -r /var/mobile/Library/AddressBook /dump')
        time.sleep(3)
        ssh.exec_command('cp -r /var/root/Library/Caches/locationd /dump')
        time.sleep(5)
        ssh.exec_command('cp -r /var/mobile/Containers/Data/Application/CAE787A4-4D72-4F6F-A102-21A549EB417E/Documents/a78eb769a558110f547ba4faea76f76a /dump')
        time.sleep(5)
        ssh.exec_command('cp /private/var/mobile/Library/SMS/sms.db /dump')
        time.sleep(5)
        ssh.exec_command('cp -r /private/var/mobile/Library/CallHistoryDB /dump')
        time.sleep(5)
        ssh.exec_command('cp /var/preferences/SystemConfiguration/com.apple.wifi.plist /dump')
        time.sleep(5)
        ssh.exec_command(' tar -zcvf /dump.tar.gz /dump')
        time.sleep(10)
    except:
        print 'error'
    try:
        t=paramiko.Transport((ip,22))
        t.connect(username='root',password=password)
        sftp=paramiko.SFTPClient.from_transport(t)
        sftp.get('/dump.tar.gz','./dump.tar.gz')
        time.sleep(10)
        ssh.exec_command('rm -rf /dump')
        ssh.exec_command('rm /dump.tar.gz')
    except:
        print 'error'
    t.close()
    ssh.close()
    os.system('tar -zxf ./dump.tar.gz')
    print 'all dumped'

#获取联系人的住址信息
def getaddress(cu,uid):
    country=''
    province=''
    city=''
    street=''
    zipcode=''
    cu.execute('select key,value from ABMultiValueEntry where parent_id='+str(uid))
    r=cu.fetchall()
    if len(r)>0:
        for i in range(len(r)):
            if r[i][0]==1:
                country=r[i][1].encode('utf-8')
            elif r[i][0]==2:
                street=r[i][1].encode('utf-8')
            elif r[i][0]==3:
                zipcode==r[i][1].encode('utf-8')
            elif r[i][0]==4:
                city=r[i][1].encode('utf-8')
            elif r[i][0]==5:
                province=r[i][1].encode('utf-8')
    address=country+province+city+street+'  '+zipcode
    return address.replace('\n',' ')

#解析通讯录数据
def dealaddressbook(addrfile):
    alluser={}
    conn=sqlite3.connect(addrfile)
    cu=conn.cursor()
    cu.execute('select * from ABPerson')
    r=cu.fetchall()
    if len(r)>0:
        for i in range(len(r)):
            #print r[i]
            userid=r[i][0]
            userinfo={}
            firstname=lastname=organization=note=''
            if r[i][1]!=None:
                firstname=r[i][1].encode('utf-8')
            if r[i][2]!=None:
                lastname=r[i][2].encode('utf-8')
            userinfo['name']=lastname+firstname
            if r[i][7]!=None:
                organization=r[i][7].encode('utf-8')
            userinfo['organization']=organization
            if r[i][9]!=None:
                note=r[i][9].encode('utf-8')
            userinfo['note']=note
            alluser[userid]=userinfo
    allid=alluser.keys()
    #print allid
    for i in allid:
        phone=[]
        email=[]
        cu.execute('select value from ABMultiValue where record_id='+str(i)+' and property=3')
        r=cu.fetchall()
        if len(r)>0:
            for j in range(len(r)):
                phone.append(r[j][0].encode('utf-8'))
        alluser[i]['phone']=phone
        cu.execute('select value from ABMultiValue where record_id='+str(i)+' and property=4')
        r=cu.fetchall()
        if len(r)>0:
            for m in range(len(r)):
                email.append(r[m][0].encode('utf-8'))
        alluser[i]['email']=email
    address={}
    cu.execute('select uid,record_id from ABMultiValue where property=5')
    r=cu.fetchall()
    if len(r)>0:
        for n in range(len(r)):
            alluser[r[n][1]]['address']=getaddress(cu,r[n][0])
    #print alluser
    fileout=open('address.csv','a')
    fileout.write('name'+','+'organization'+','+'phone'+','+'email'+','+'address'+','+'note'+'\n')
    for i in alluser.keys():
        name=organization=note=email=phone=address=''
        if alluser[i].has_key('name'):
            name=alluser[i]['name']
        if alluser[i].has_key('organization'):
            organization=alluser[i]['organization']
        if alluser[i].has_key('note'):
            note=alluser[i]['note'].strip()
        if alluser[i].has_key('email'):
            for x in range(len(alluser[i]['email'])):
                email+=alluser[i]['email'][x]+'\t'
            email=email.strip().replace('\t',';')
        if alluser[i].has_key('address'):
            address=alluser[i]['address']
        if alluser[i].has_key('phone'):
            for y in range(len(alluser[i]['phone'])):
                phone+=alluser[i]['phone'][y]+'\t'
            phone=phone.strip().replace('\t',';')
        fileout.write(name+','+organization+','+phone+','+email+','+address+','+note+'\n')
    fileout.close()

#解析手机卡定位信息
def ltelocation(infile):
    ltelocation=open('ltelocation.txt','a')
    conn=sqlite3.connect(infile)
    cu=conn.cursor()
    cu.execute('select timestamp,latitude,longitude,HorizontalAccuracy from LteCellLocation')
    r=cu.fetchall()
    if len(r)>0:
        for i in range(len(r)):
            result=list(r[i])
            x=time.localtime(result[0]+978307200)
            result[0]=time.strftime('%Y-%m-%d %H:%M:%S',x)
            for i in range(len(result)):
                result[i]=str(result[i])
            #print result
            sep=','
            ltelocation.write(sep.join(result)+'\n')
    ltelocation.close()
'''
def applocation(infile):
    location=open('location.txt','a')
    conn=sqlite3.connect(infile)
    cu=conn.cursor()
    cu.execute('select timestamp,latitude,longitude,HorizontalAccuracy from appHarvest where BundleId=\'com.tencent.xin\'')
    r=cu.fetchall()
    if len(r)>0:
        location.write('weixin location:\n')
        for i in range(len(r)):
            result=list(r[i])
            x=time.localtime(result[0]+978307200)
            result[0]=time.strftime('%Y-%m-%d %H:%M:%S',x)
            for i in range(len(result)):
                result[i]=str(result[i])
            sep=','
            location.write(sep.join(result)+'\n')
    location.close()
'''

#解析微信登录帐号信息
def getself(infile,outfile):
    #(status, output)=commands.getstatusoutput('strings /root/iphone/wechat/Documents/a78eb769a558110f547ba4faea76f76a/mmsetting.archive|grep wxid')
    out=open(outfile,'a')
    try:  
        plist = readPlist(infile)
    except (InvalidPlistException, NotBinaryPlistException), e:  
        print "Not a plist:", e 
    obj=plist[ "$objects"]
    selfinfo={}
    selfinfo['username']=obj[2]
    selfinfo['nickname']=obj[3]
    selfinfo['phone']=obj[5]
    #print selfinfo
    out.write('selfinfo:'+'\n'+'username:'+obj[2]+'\n'+'nickname:'+obj[3]+'\n'+'phone:'+obj[5]+'\n')
    out.close()
    return selfinfo

#获取微信好友信息
def getfriend(cu,outfile):
    out=open(outfile,'w')
    cu.execute('select usrname,nickname from Friend where type!=1 and type!=2')
    r=cu.fetchall()
    friendinfo={}
    if len(r)>0:
        for i in range(len(r)):
            #print r[i][0].encode('utf-8')+':'+r[i][1].encode('utf-8')
            friendinfo[r[i][0].encode('utf-8')]=r[i][1].encode('utf-8')
            out.write(r[i][0].encode('utf-8')+':'+r[i][1].encode('utf-8')+'\n')
    return friendinfo

#获取一个好友的微信聊天记录
def getchat(username,cu,outfile):
    out=open(outfile,'w')
    m=hashlib.md5()
    m.update(username)
    table='Chat_'+m.hexdigest()
    cu.execute('select * from sqlite_master where type=\'table\' and name=\''+table+'\'')
    r=cu.fetchall()
    if len(r)==1:
        cu.execute('select createtime,message,des from '+table+' order by CreateTime asc')
        r=cu.fetchall()
        if len(r)>0:
            for i in range(len(r)):
                if r[i][2]==0:
                    x=time.localtime(r[i][0])
                    str=time.strftime('%Y-%m-%d %H:%M:%S',x)+ '  to '+username+':'+r[i][1].encode('utf-8')
                    #print str
                    out.write(str+'\n')
                elif r[i][2]==1:
                    x=time.localtime(r[i][0])
                    str= time.strftime('%Y-%m-%d %H:%M:%S',x)+ '  from '+username+':'+r[i][1].encode('utf-8')
                    #print str
                    out.write(str+'\n')
    out.close()

#解析微信聊天记录
def weichat(infile):
    conn=sqlite3.connect(infile)
    cu=conn.cursor()
    friend=getfriend(cu,'./weichat/weichatfriend.txt')
    for id in friend.keys():
        if id[:3]!='gh_':
            #outfile.write(r['username']+'<--------------------->'+id+'\n')
            getchat(id,cu,'./weichat/'+id+'.txt')

#解析WIFI信息
def wifiinfo(plist,outfile):
    try:  
        plist = readPlist(plist)
        #print plist
    except (InvalidPlistException, NotBinaryPlistException), e:  
        print "Not a plist:", e 
    out=open(outfile,'a')
    #print 'mac,name,lastjoined'
    out.write('mac,name,lastjoined\n')
    for i in range(len(plist["List of known networks"])):
        name=plist["List of known networks"][i]['SSID_STR'].encode('utf-8')
        if plist["List of known networks"][i].has_key('networkKnownBSSListKey'):
            other=plist["List of known networks"][i]['networkKnownBSSListKey']
            otherinfo={}
            for j in other:
                t=str(j['lastRoamed']).split('.')[0]
                x = time.localtime(time.mktime(time.strptime(t,'%Y-%m-%d %H:%M:%S'))+28800)
                time.strftime('%Y-%m-%d %H:%M:%S',x)
                otherinfo[j['BSSID']]=time.strftime('%Y-%m-%d %H:%M:%S',x)
            for m in otherinfo.keys():
                #print m+','+name+','+str(otherinfo[m])
                out.write(m+','+name+','+str(otherinfo[m])+'\n')
        else:
            mac=plist["List of known networks"][i]['BSSID'].encode('utf-8')
            t=str(plist["List of known networks"][i]['lastJoined']).split('.')[0]
            x = time.localtime(time.mktime(time.strptime(t,'%Y-%m-%d %H:%M:%S'))+28800)
            time.strftime('%Y-%m-%d %H:%M:%S',x)
            jointime=time.strftime('%Y-%m-%d %H:%M:%S',x)
            #print mac+','+name+','+str(jointime)
            out.write(mac+','+name+','+str(jointime)+'\n')
    out.close()

#解析短信
def getsms(infile,outfile):
    out=open(outfile,'a')
    smsinfo={}
    conn=sqlite3.connect(infile)
    cu=conn.cursor()
    cu.execute('select id,chat_id from chat_handle_join left join handle on handle_id=rowid')
    r=cu.fetchall()
    if len(r)>0:
        for i in range(len(r)):
            message_id=[]
            phone=r[i][0].encode('utf-8')
            chat_id=r[i][1]
            cu.execute('select message_id from chat_message_join where chat_id='+str(chat_id))
            r2=cu.fetchall()
            if len(r2)>0:
                for j in range(len(r2)):
                    message_id.append(r2[j][0])
            smsinfo[phone]=message_id
        #print smsinfo
    for k in smsinfo.keys():
        for mid in smsinfo[k]:
            cu.execute('select text,date,account,is_from_me from message where rowid='+str(mid)+' order by date asc')
            r=cu.fetchall()
            if len(r)>0:
                for i in range(len(r)):
                    text=r[i][0].encode('utf-8')
                    date=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(r[i][1]+978307200))
                    account=r[i][2].encode('utf-8').split(':')[1]
                    is_from_me=r[i][3]
                    if is_from_me:
                        #print date+'\t'+account+' to '+k+':'+text
                        out.write(date+'\t'+account+' to '+k+':'+text+'\n')
                    else:
                        #print date+'\t'+k+' to '+account+':'+text
                        out.write(date+'\t'+k+' to '+account+':'+text+'\n')
    out.close()

#解析通话记录
def callhistory(infile,outfile):
    out=open(outfile,'a')
    conn=sqlite3.connect(infile)
    cu=conn.cursor()
    cu.execute('select zoriginated,zdate,zaddress from zcallrecord order by zdate asc')
    r=cu.fetchall()
    if len(r):
        for i in range(len(r)):
            zoriginated=r[i][0]
            #print type(zoriginated)
            zdate=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(r[i][1]+978307200))
            #print zdate
            zaddress=r[i][2]
            #print type(zaddress)
            if zoriginated:
                #print str(zdate)+'\thuchu\tto:'+str(zaddress)
                out.write(str(zdate)+'\thuchu\tto:'+str(zaddress)+'\n')
            else:
                #print str(zdate)+'\thuru\tfrom:'+str(zaddress)
                out.write(str(zdate)+'\thuru\tfrom:'+str(zaddress)+'\n')

#解析WIFI定位信息
def wifilocation(infile,outfile):
    out=open(outfile,'a')
    conn=sqlite3.connect(infile)
    cu=conn.cursor()
    cu.execute('select mac,timestamp,latitude,longitude,horizontalaccuracy from wtwlocationharvest order by timestamp asc')
    r=cu.fetchall()
    if len(r):
        out.write('mac,time,latitude,longitude,horizontalaccuracy')
        for i in range(len(r)):
            mac=r[i][0].encode('utf-8')
            jointime=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(r[i][1]+978307200))
            latitude=str(r[i][2])
            longitude=str(r[i][3])
            horizontalaccuracy=str(r[i][4])
            out.write(mac+','+jointime+','+latitude+','+longitude+','+horizontalaccuracy+'\n')
            #print mac+','+jointime+','+latitude+','+longitude+','+horizontalaccuracy
    out.close()


if __name__ == '__main__':
    if os.path.exists('weichat')!=True or os.path.isdir('weichat')!=True:
        os.mkdir('weichat')
    #try:
        #scp2('192.168.1.102','alpine')
    #except Exception,e:
        #print 1
        #print e
    try:
        dealaddressbook('./dump/AddressBook.sqlitedb')
    except Exception,e:
        print 2
        print e
    try:
        ltelocation('./dump/locationd/cache_encryptedA.db')
    except Exception,e:
        print 3
        print e
    try:
        callhistory('./dump/CallHistoryDB/CallHistory.storedata','./callhistory.txt')
    except Exception,e:
        print 4
        print e
    try:
        getsms('./dump/sms.db','./sms.txt')
    except Exception,e:
        print 5
        print e
    try:
        weichat('./dump/a78eb769a558110f547ba4faea76f76a/DB/MM.sqlite')
    except Exception,e:
        print 6
        print e
    try:
        getself('./dump/a78eb769a558110f547ba4faea76f76a/mmsetting.archive','./weichat/self.txt')
    except Exception,e:
        print 7
        print e
    try:
        wifiinfo('./dump/com.apple.wifi.plist','wifiinfo.txt')
    except Exception,e:
        print 8
        print e
    try:
        wifilocation('./dump/locationd/cache_encryptedA.db','wifiloction.txt')
    except Exception,e:
        print 9
        print e

