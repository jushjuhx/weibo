# http://www.cnblogs.com/xuchaosheng/p/3749693.html
# import 这边需要注意的是只有一个rsa这个模块是需要install的，其他的都是内置
import re , urllib.parse , urllib.request , http.cookiejar , base64 , binascii , rsa
import configparser , time , json
import http_connection , db_mysql
from bs4 import BeautifulSoup

# 以下4行代码说简单点就是让你接下来的所有get和post请求都带上已经获取的cookie，因为稍大些的网站的登陆验证全靠cookie
cj = http.cookiejar.LWPCookieJar()
cookie_support = urllib.request.HTTPCookieProcessor(cj)
opener = urllib.request.build_opener(cookie_support , urllib.request.HTTPHandler)
urllib.request.install_opener(opener)


#ptnattra是提取每个热门微博链接的a标签 ptnaurl是根据ptnattra提取的a标签提取链接
ptnattra = re.compile(r'<a target=\\\"_blank\\\" href=\\\"http:\\\/\\\/weibo.com\\\/.*?title.*?date.*?name.*?class=\\\"S_txt2\\\" node-type=\\\"feed_list_item_date\\\" suda-data=\\\"key=tblog_home_new&value=feed_time.*?<\\\/a>')
ptnaurl = re.compile(r'http:\\\/\\\/weibo.com\\\/.*?\"')
ISOTIMEFORMAT='%Y-%m-%d %X'

def insert_hotweibourl(text):
    attraall = re.findall(ptnattra,text)
    #插入hotweibourl的sql语句
    inserthwu = "INSERT INTO `hotweibourl` (`url`, `time`) VALUES (%s, %s)"
    for attra in attraall:
        hoturlall = re.findall(ptnaurl,attra)
        hoturl = hoturlall[0].replace("\"","").replace("\\","")
        get_comment(hoturl)
        paras = (hoturl, time.strftime( ISOTIMEFORMAT, time.localtime() ))
        db_mysql.dbMysql().executeInsert(inserthwu , paras)

def get_comment(url):
    text = http_connection.getData(url)
    pattern = re.compile(r'mid=\d+')
    id = re.findall(pattern,text)[0][4:]
    #第一页评论，主要为了获取max_id
    cmturlfirst = 'http://weibo.com/aj/v6/comment/big?ajwvr=6&mid=' + id + '&id=' + id + '&filter=hot&__rnd=' + str(int(time.time()*1000))
    text = http_connection.getData(cmturlfirst)
    pattern = re.compile(r'max_id=\d+')
    max_id = re.findall(pattern,text)[0][7:]
    #页码
    pagenum = 0
    while 1:
        #到最后一页了
        has_more = False
        #从第一页开始
        pagenum += 1
        cmturl = 'http://weibo.com/aj/v6/comment/big?ajwvr=6&id=' + id + '&max_id=' + max_id + '&filter=hot&page=' + str(pagenum) + '&__rnd=' + str(int(time.time()*1000))
        #获取第一页的评论json
        text = http_connection.getData(cmturl)
        #处理评论的json文件
        decodejson = json.loads(text)
        #提取json的评论html
        soup = BeautifulSoup(decodejson['data']['html'], 'html.parser')
        #提取每条评论的关键部分
        for divWB_text in soup.find_all("div", class_="WB_text"):
            has_more = True
            ptcmtuser = re.compile(r'id=\d+',re.S)
            #评论人id
            cmtuserid = re.findall(ptcmtuser,str(divWB_text))[0][3:]
            #删除html标签
            htmltag = re.compile(r'<[^>]+>',re.S)
            deletetag = htmltag.sub('',str(divWB_text))
            #查找有@人的评论
            commentat = re.compile(r'@.+? ',re.S)
            #被@的人
            nickatall =  re.findall(commentat,deletetag)
            if(nickatall.__len__() != 0):
                cmtcore = deletetag.split('：',1)
                #评论人昵称
                cmtusernick = cmtcore[0]
                #评论内容
                cmtcont = cmtcore[1]
                for eachnickat in nickatall:
                    inserthwu = "INSERT INTO `commentat` (`cmtuserid`, `cmtusernick`, `cmtatnick` , `cmtcontent` , `url` , `time` ) VALUES (%s, %s, %s, %s, %s, %s)"
                    paras = (cmtuserid, cmtusernick.replace('\n',''),eachnickat.replace('@','').replace(' ',''),cmtcont, url, time.strftime( ISOTIMEFORMAT, time.localtime() ))
                    db_mysql.dbMysql().executeInsert(inserthwu , paras)

        if(has_more == False):
            break

def login_weibo(nick , pwd) :
    #==========================获取servertime , pcid , pubkey , rsakv===========================
    # 预登陆请求，获取到若干参数
    prelogin_url = 'http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su=%s&rsakt=mod&checkpin=1&client=ssologin.js(v1.4.15)&_=1400822309846' % nick
    preLogin = http_connection.getData(prelogin_url)
    # 下面获取的四个值都是接下来要使用的
    servertime = re.findall('"servertime":(.*?),' , preLogin)[0]
    pubkey = re.findall('"pubkey":"(.*?)",' , preLogin)[0]
    rsakv = re.findall('"rsakv":"(.*?)",' , preLogin)[0]
    nonce = re.findall('"nonce":"(.*?)",' , preLogin)[0]
    #===============对用户名和密码加密================
    # 好，你已经来到登陆新浪微博最难的一部分了，如果这部分没有大神出来指点一下，那就真是太难了，我也不想多说什么，反正就是各种加密，最后形成了加密后的su和sp
    su = base64.b64encode(bytes(urllib.request.quote(nick) , encoding = 'utf-8'))
    rsaPublickey = int(pubkey , 16)
    key = rsa.PublicKey(rsaPublickey , 65537)
    # 稍微说一下的是在我网上搜到的文章中，有些文章里并没有对拼接起来的字符串进行bytes，这是python3的新方法好像是。rsa.encrypt需要一个字节参数，这一点和之前不一样。其实上面的base64.b64encode也一样
    message = bytes(str(servertime) + '\t' + str(nonce) + '\n' + str(pwd) , encoding = 'utf-8')
    sp = binascii.b2a_hex(rsa.encrypt(message , key))
    #=======================登录=======================
    
    #param就是激动人心的登陆post参数，这个参数用到了若干个上面第一步获取到的数据，可说的不多
    param = {'entry' : 'weibo' , 'gateway' : 1 , 'from' : '' , 'savestate' : 7 , 'useticket' : 1 , 'pagerefer' : 'http://login.sina.com.cn/sso/logout.php?entry=miniblog&r=http%3A%2F%2Fweibo.com%2Flogout.php%3Fbackurl%3D' , 'vsnf' : 1 , 'su' : su , 'service' : 'miniblog' , 'servertime' : servertime , 'nonce' : nonce , 'pwencode' : 'rsa2' , 'rsakv' : rsakv , 'sp' : sp , 'sr' : '1680*1050' ,
             'encoding' : 'UTF-8' , 'prelt' : 961 , 'url' : 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack'}
    # 这里就是使用postData的唯一一处，也很简单
    s = http_connection.postData('http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.15)' , param)
    # 好了，当你的代码执行到这里时，已经完成了大部分了，可是有很多爬虫童鞋跟我一样还就栽在了这里，假如你跳过这里直接去执行获取粉丝的这几行代码你就会发现你获取的到还是让你登陆的页面，真郁闷啊，我就栽在这里长达一天啊
    # 好了，我们还是继续。这个urll是登陆之后新浪返回的一段脚本中定义的一个进一步登陆的url，之前还都是获取参数和验证之类的，这一步才是真正的登陆，所以你还需要再一次把这个urll获取到并用get登陆即可

    #如果这里报错，那么原因有可能是需要输入验证码
    urll = re.findall("location.replace\(\'(.*?)\'\);" , s)[0]

    http_connection.getData(urll)
    #这里相当于login已经结束，下面的代码不属于login的部分了
    #======================获取粉丝====================
    # 如果你没有跳过刚才那个urll来到这里的话，那么恭喜你！你成功了，接下来就是你在新浪微博里畅爬的时候了，获取到任何你想获取到的数据了！
    # 可以尝试着获取你自己的微博主页看看，你就会发现那是一个多大几百kb的文件了

    #插入hotweibopage的sql语句
    inserthwp = "INSERT INTO `hotweibopage` (`pagenum`, `content`, `time`) VALUES (%s, %s, %s)"
    for i in range(5):
        if(i == 0):
            #第一页的内容和其他内容不一样
            #每一页分成三部分
            #part1
            text = http_connection.getData('http://d.weibo.com/102803?topnav=1&mod=logo&wvr=6')
            #获取最后一个mid,在后面请求链接中能用到
            pattern = re.compile(r'mid=\d+')
            midall = re.findall(pattern,text)
            lastmid = midall[midall.__len__()-1][4:]
            #将每一个获取的text插入到数据库中
            paras = ('1-1', text, time.strftime( ISOTIMEFORMAT, time.localtime() ))
            db_mysql.dbMysql().executeInsert(inserthwp , paras)
            #将每一个热门微博链接提取出来，插入数据库中
            insert_hotweibourl(text)
            #part2
            text = http_connection.getData('http://d.weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain=102803&topnav=1&mod=logo&wvr=6&pre_page=1&page=1&max_id=&end_id=' + lastmid  + '&pagebar=0&filtered_min_id=&pl_name=Pl_Core_MixedFeed__5&id=102803&script_uri=/102803&feed_type=1&tab=home&current_page=1&domain_op=102803&__rnd=' + str(int(time.time()*1000)))
            paras = ('1-2', text, time.strftime( ISOTIMEFORMAT, time.localtime() ))
            db_mysql.dbMysql().executeInsert(inserthwp , paras)
            insert_hotweibourl(text)
            #part3
            text = http_connection.getData('http://d.weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain=102803&topnav=1&mod=logo&wvr=6&pre_page=1&page=1&max_id=&end_id=' + lastmid  + '&pagebar=1&filtered_min_id=&pl_name=Pl_Core_MixedFeed__5&id=102803&script_uri=/102803&feed_type=1&tab=home&current_page=1&domain_op=102803&__rnd=' + str(int(time.time()*1000)))
            paras = ('1-3', text, time.strftime( ISOTIMEFORMAT, time.localtime() ))
            db_mysql.dbMysql().executeInsert(inserthwp , paras)
            insert_hotweibourl(text)
        else:
            #每一页分成三部分
            #part1
            text = http_connection.getData('http://d.weibo.com/102803?pids=Pl_Core_MixedFeed__5&current_page=' + str(i * 3)    + '&since_id=&page=' + str(i + 1)    + '&ajaxpagelet=1&__ref=/102803&_t=FM_' + str(int(time.time()*1000)))
            #获取最后一个mid,在后面请求链接中能用到
            pattern = re.compile(r'mid=\d+')
            midall = re.findall(pattern,text)
            lastmid = midall[midall.__len__()-1][4:]
            paras = (str(i+1) + '-1', text, time.strftime( ISOTIMEFORMAT, time.localtime() ))
            db_mysql.dbMysql().executeInsert(inserthwp , paras)
            insert_hotweibourl(text)
            #part2
            text = http_connection.getData('http://d.weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain=102803&current_page=' + str(i * 3 + 1)    + '&since_id=&page=' + str(i + 1)    + '&pre_page=' + str(i + 1)    + '&max_id=&end_id=' + lastmid  + '&pagebar=0&filtered_min_id=&pl_name=Pl_Core_MixedFeed__5&id=102803&script_uri=/102803&feed_type=1&tab=home&domain_op=102803&__rnd=' + str(int(time.time()*1000)))
            paras = (str(i+1) + '-2', text, time.strftime( ISOTIMEFORMAT, time.localtime() ))
            db_mysql.dbMysql().executeInsert(inserthwp , paras)
            insert_hotweibourl(text)
            #part3
            text = http_connection.getData('http://d.weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain=102803&current_page=' + str(i * 3 + 2)    + '&since_id=&page=' + str(i + 1)    + '&pre_page=' + str(i + 1)    + '&max_id=&end_id=' + lastmid  + '&pagebar=1&filtered_min_id=&pl_name=Pl_Core_MixedFeed__5&id=102803&script_uri=/102803&feed_type=1&tab=home&domain_op=102803&__rnd=' + str(int(time.time()*1000)))
            paras = (str(i+1) + '-3', text, time.strftime( ISOTIMEFORMAT, time.localtime() ))
            db_mysql.dbMysql().executeInsert(inserthwp , paras)
            insert_hotweibourl(text)
    print("end...")


login_weibo('user' , 'pass')
#==================================================后记============================================================

