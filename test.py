import json , re , db_mysql , time
from bs4 import BeautifulSoup

ISOTIMEFORMAT='%Y-%m-%d %X'

f = open('yeah.html' , 'r' , encoding='utf-8')
#处理评论的json文件
decodejson = json.loads(f.read())
#提取json的评论html
soup = BeautifulSoup(decodejson['data']['html'], 'html.parser')

#提取每条评论的关键部分
for divWB_text in soup.find_all("div", class_="WB_text"):
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
        cmtnick = cmtcore[0]
        #评论内容
        cmtcont = cmtcore[1]
        for eachnickat in nickatall:
            print(cmtuserid)
            print(cmtnick.replace('\n',''))
            print(eachnickat.replace('@','').replace(' ',''))
            print(cmtcont)
            print('-----------------------------------------------------------------5')



