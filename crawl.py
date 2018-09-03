#! -*- coding: utf-8 -*-
import random
from tkinter import *
import threading
import urllib
import http.cookiejar
import re
import time
import webbrowser
from PIL import Image, ImageTk
from tkinter import ttk
import json

# 进度条变量
progress_var = None
# 进度数值
progress = 0
# 进度条
progress_bar = None
# 进度提示文字
progressLabel = None
# 预加载提示文字
preLoadLabel = None
# 课程清单切换tabs
tabs = None
# 随机一个模拟浏览器请求header
headerNum = random.randint(0, 3)

cookie = None
username = None
password = None
vercode = None
timestamp=None
vtoken=None
Logintoken=None
electiveBatchCode=None

listbox1=None
listbox2=None
listbox3=None
listbox4=None
listbox5=None



# 六大类课程数据
list_recommend = [] #系统推荐课程
list_humanity = [] #人文选修课
list_science = [] #自然科学选修课
list_economics=[] #经管选修课
list_sports = [] #体育选修课

# 正在选择的课程的清单
list_selecting = []
list_humanity_selecting = []
list_science_selecting = []
list_economics_selecting = []
list_sports_selecting= []

# 已选择课程的数量
selected_num = 0

# 三类通选是否正在选择的flag，1为否
flag_humanity = 1
flag_science = 1
flag_economics = 1

intensity = 0

#头部信息列表
fake_headers = [{'Host': 'newxk.urp.seu.edu.cn',
                 'Proxy-Connection': 'keep-alive',
                 'Origin': 'http://newxk.urp.seu.edu.cn',
                 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1'},
                {
                    'Host': 'newxk.urp.seu.edu.cn',
                    'Origin': 'http://newxk.urp.seu.edu.cn',
                    'Connection': 'keep-alive',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'},
                {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                 'Connection': 'keep-alive',
                 'Host': 'newxk.urp.seu.edu.cn',
                 'Origin': 'http://newxk.urp.seu.edu.cn',
                 'User-Agent': 'Mozilla/6.0 (Windows NT 6.2; rv:16.0) Gecko/20100101 Firefox/16.0'},
                {'Host': 'newxk.urp.seu.edu.cn',
                 'Connection': 'keep-alive',
                 'Accept': 'text/html, */*; q=0.01',
                 'User-Agent': 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.89 Safari/537.36',
                 'Origin': 'http://newxk.urp.seu.edu.cn'}]

# 预先准备Dialog类，暂时未进行任何修改
class PreloadDialog(Toplevel):
    def __init__(self, parent, title=None):
        global preLoadLabel #全局变量
        Toplevel.__init__(self, parent)
        self.transient(parent)
        if title:
            self.title(title)
        self.parent = parent
        self.system_state = 1
        preLoadLabel = Label(self, text="正在检查选课系统状态...")
        preLoadLabel.config(font=('times', 20, 'bold'))
        preLoadLabel.pack()

        self.grab_set()
        self.geometry('500x60+500+200')
        self.resizable(width=False, height=False)
        self.update()  # 不管是否准备好先显示窗口
        self.login_preload(1)
        print ('thread return')

    def login_preload(self, args):
        times = 0
        global preLoadLabel
        state = args
        while state:
            try:
                # print 'try'
                state = get_verifycode()
            except Exception as e:
                # print str(e)
                times += 1
                preLoadLabel.config(text='网络原因进入选课系统失败,重试(' + str(times) + ')...')
                self.update()
                # print 'Exception generated'
        # print 'to destroy'
        self.destroy()
        # print 'destroyed'

class LoginDialog(Toplevel):
    #初始化登录界面，暂时未进行任何修改,Tk暂时无法引入
    def __init__(self, parent, title=None):
        Toplevel.__init__(self, parent)

        self.transient(parent)
        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        Label(self, text="用户名").grid(sticky=E, padx=5, pady=10)
        Label(self, text="密码").grid(sticky=E)
        Label(self, text="验证码").grid(sticky=E, pady=10)
        self.edit_username = Entry(self)
        self.edit_password = Entry(self)
        self.edit_vercode = Entry(self)
        self.edit_username.grid(row=0, column=1, columnspan='2')
        self.edit_password.grid(row=1, column=1, columnspan='2')
        self.edit_vercode.grid(row=2, column=1, columnspan='2')
        # 读取验证码图片
        filename = 'verifycode.jpg'
        self.canvas = Canvas(self)
        image = Image.open(filename)
        image = image.resize((100, 50), Image.ANTIALIAS)
        img_bg = ImageTk.PhotoImage(image)
        self.label = Label(self, image=img_bg)
        self.label.image = img_bg
        self.label.grid(row=3, column=1, columnspan='2')

        # 点击提交则验证登录并销毁登录界面
        self.btn_submit = Button(self, text='   提交   ', command=lambda: self.destroy())
        self.btn_submit.grid(row=3, column=0, padx=10, pady=10)

        self.grab_set()

        self.geometry('230x180+500+200')
        self.resizable(width=False, height=False)
        self.wait_window(self)

    #销毁登录界面
    def destroy(self):
        self.submit_login()
        print("准备destroy Toplevel")
        Toplevel.destroy(self)

    #提交的用户名，密码，验证码
    def submit_login(self):
        global username
        global password
        global vercode
        username = self.edit_username.get()
        password = self.edit_password.get()
        vercode = self.edit_vercode.get()
        root.event_generate("<<EVENT_LOGIN>>")
        self.init_data()
        pass

    # 正在登录，依次请求网络数据
    def init_data(self):
        # 网络请求
        print ('init data~')
        for i in range(1,7):# 几个获取数据的阶段，为了测试暂时修改
            global progress
            global progress_bar
            # 登录过程的某一阶段处理
            try:
                self.doPost(i)
            except Exception as e:
                i -= 1
                continue
                # 重试
                # 登陆不成功
                tkMessageBox.showwarning("登录失败","请重新启动本程序\n")
                print('app destroy' + str(e))
                root.destroy()
            # 阶段处理完成
            progress += 20
            root.event_generate("<<EVENT_LOGIN_UPDATE>>")
        print('init data finished')

    #此处完成登录、拉取课表等操作
    def doPost(self, step):
        global mainLabel
        global cookie
        global headerNum
        global list_institute
        global list_humanity
        global list_science
        global list_economics
        global list_seminar
        global list_interinstitute
        if step == 1:
            print("正在进行第一步：登录")
            global cookie
            global username
            global password
            global vercode
            global headerNum
            global Logintoken
            global electiveBatchCode
            headerNum = random.randint(0, 3)
            # print 'header is ' + str(headerNum)
            header = fake_headers[headerNum]
            header.setdefault('Referer', 'http://newxk.urp.seu.edu.cn/')
            url = "http://newxk.urp.seu.edu.cn/xsxkapp/sys/xsxkapp/student/check/login.do?"+"timestrap="+str(int(time.time()))+"&loginName="+str(username)+"&loginPwd="+password+"&verifyCode="+vercode+"&vtoken="+vtoken
            print(url)
            req = urllib.request.Request(url, headers=header)
            #response = urllib.request.urlopen(req, timeout=12)
            cookie = http.cookiejar.CookieJar()
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie))
            urllib.request.install_opener(opener)
            response=opener.open(req)
            content = response.read().decode('utf-8')
            jsonObject = json.loads(content)
            Logintoken = jsonObject['data']['token']
            Msg= jsonObject['msg']
            print(Logintoken)
            print(Msg)
            if (Msg!="登录成功"):
                mainLabel.config(text="登录失败")

            #如果登录成功，获取选课批次代码
            url = "http://newxk.urp.seu.edu.cn/xsxkapp/sys/xsxkapp/elective/batch.do?timestrap="+str(int(time.time()));
            data=urllib.request.urlopen(url)
            content=data.read().decode("utf-8")
            electiveBatchCode = json.loads(content)['dataList'][0]['code']
            print(electiveBatchCode)
        if step == 2:
            print("正在进行第二步：拉取系统推荐课程")
            header2 = fake_headers[headerNum]
            header2.setdefault('Referer', 'http://newxk.urp.seu.edu.cn/xsxkapp/sys/xsxkapp/*default/grablessons.do?token='+str(Logintoken))
            header2.setdefault('token',Logintoken)
            url2 = 'http://newxk.urp.seu.edu.cn/xsxkapp/sys/xsxkapp/elective/recommendedCourse.do'
            jsonData = {
                "data": {
                    "studentCode": username,
                    "campus": "1",
                    "electiveBatchCode": electiveBatchCode,
                    "isMajor": "1",
                    "teachingClassType": "TJKC",
                    "checkConflict": "2",
                    "checkCapacity": "2",
                    "queryContent": ""
                },
                "pageSize": "100",
                "pageNumber": "0",
                "order": ""
            }

            postdata=urllib.parse.urlencode({
                "querySetting":json.dumps(jsonData)
            }).encode('utf-8')
            req2 = urllib.request.Request(url2,postdata,headers=header2)
            response2 = urllib.request.urlopen(req2, timeout=12)
            content2 = response2.read().decode('utf-8')
            print("专业课拉取完毕")
            JsonParse(list_recommend,content2)

            # print 'update ui humanitylist generated'
            root.event_generate("<<UPDATE_INSTITUTE_LIST>>")
        if step == 3:
            # print 'do post 3'
            print("正在进行第三步：拉取人文选修课程")
            header3 = fake_headers[headerNum]
            header3.setdefault('Referer',
                               'http://newxk.urp.seu.edu.cn/xsxkapp/sys/xsxkapp/*default/grablessons.do?token=' + str(
                                   Logintoken))
            header3.setdefault('token', Logintoken)
            url3 = 'http://newxk.urp.seu.edu.cn/xsxkapp/sys/xsxkapp/elective/publicCourse.do'
            jsonData = {
                "data": {
                    "studentCode": username,
                    "campus": "1",
                    "electiveBatchCode": electiveBatchCode,
                    "isMajor": "1",
                    "teachingClassType": "XGXK",
                    "checkConflict": "2",
                    "checkCapacity": "2",
                    "queryContent": "XGXKLBDM:01"
                },
                "pageSize": "100",
                "pageNumber": "0",
                "order": ""
            }

            postdata = urllib.parse.urlencode({
                "querySetting": json.dumps(jsonData)
            }).encode('utf-8')
            req3 = urllib.request.Request(url3, postdata, headers=header3)
            response3 = urllib.request.urlopen(req3, timeout=12)
            content3= response3.read().decode('utf-8')
            print("人文课拉取完毕")
            GJsonParse(list_humanity, content3)
            # print 'update ui list_science generated'
            root.event_generate("<<UPDATE_HUMANOTY_LIST>>")
        if step == 4:
            print("正在进行第三步：拉取自然科学课程")
            header4 = fake_headers[headerNum]
            header4.setdefault('Referer',
                               'http://newxk.urp.seu.edu.cn/xsxkapp/sys/xsxkapp/*default/grablessons.do?token=' + str(
                                   Logintoken))
            header4.setdefault('token', Logintoken)
            url4 = 'http://newxk.urp.seu.edu.cn/xsxkapp/sys/xsxkapp/elective/publicCourse.do'
            jsonData = {
                "data": {
                    "studentCode": username,
                    "campus": "1",
                    "electiveBatchCode": electiveBatchCode,
                    "isMajor": "1",
                    "teachingClassType": "XGXK",
                    "checkConflict": "2",
                    "checkCapacity": "2",
                    "queryContent": "XGXKLBDM:03"
                },
                "pageSize": "100",
                "pageNumber": "0",
                "order": ""
            }

            postdata = urllib.parse.urlencode({
                "querySetting": json.dumps(jsonData)
            }).encode('utf-8')
            req4 = urllib.request.Request(url4, postdata, headers=header4)
            response4 = urllib.request.urlopen(req4, timeout=12)
            content4 = response4.read().decode('utf-8')
            print("自然科学与技术课程拉取完毕")
            GJsonParse(list_science, content4)
            # print 'update ui list_science generated'
            root.event_generate("<<UPDATE_SCIENCE_LIST>>")
        if step == 5:
            print("正在进行第五步：拉取经管课程")

            header5 = fake_headers[headerNum]
            header5.setdefault('Referer',
                               'http://newxk.urp.seu.edu.cn/xsxkapp/sys/xsxkapp/*default/grablessons.do?token=' + str(
                                   Logintoken))
            header5.setdefault('token', Logintoken)
            url5 = 'http://newxk.urp.seu.edu.cn/xsxkapp/sys/xsxkapp/elective/publicCourse.do'
            jsonData = {
                "data": {
                    "studentCode": username,
                    "campus": "1",
                    "electiveBatchCode": electiveBatchCode,
                    "isMajor": "1",
                    "teachingClassType": "XGXK",
                    "checkConflict": "2",
                    "checkCapacity": "2",
                    "queryContent": "XGXKLBDM:02"
                },
                "pageSize": "100",
                "pageNumber": "0",
                "order": ""
            }

            postdata = urllib.parse.urlencode({
                "querySetting": json.dumps(jsonData)
            }).encode('utf-8')
            req5 = urllib.request.Request(url5, postdata, headers=header5)
            response5 = urllib.request.urlopen(req5, timeout=12)
            content5 = response5.read().decode('utf-8')
            print("经济管理类拉取完毕")
            GJsonParse(list_economics, content5)
            # print 'update ui list_science generated'
            root.event_generate("<<UPDATE_ECONOMICS_LIST>>")
        if step == 6:
            # print 'do post 6'
            print("正在进行第三步：拉取体育课程")
            header6 = fake_headers[headerNum]
            header6.setdefault('Referer',
                               'http://newxk.urp.seu.edu.cn/xsxkapp/sys/xsxkapp/*default/grablessons.do?token=' + str(
                                   Logintoken))
            header6.setdefault('token', Logintoken)
            url6 = 'http://newxk.urp.seu.edu.cn/xsxkapp/sys/xsxkapp/elective/programCourse.do'
            jsonData = {
                "data": {
                    "studentCode": username,
                    "campus": "1",
                    "electiveBatchCode": electiveBatchCode,
                    "isMajor": "1",
                    "teachingClassType": "TYKC",
                    "checkConflict": "2",
                    "checkCapacity": "2",
                    "queryContent": ""
                },
                "pageSize": "100",
                "pageNumber": "0",
                "order": ""
            }

            postdata = urllib.parse.urlencode({
                "querySetting": json.dumps(jsonData)
            }).encode('utf-8')
            req6 = urllib.request.Request(url6, postdata, headers=header6)
            response6 = urllib.request.urlopen(req6, timeout=12)
            content6 = response6.read().decode('utf-8')
            print("体育课拉取完毕")
            JsonParse(list_sports, content6)
            # print 'update ui list_science generated'
            root.event_generate("<<UPDATE_INTER_LIST>>")



# 获取验证码，图片暂时无法在本地打开，但是GUI测试正常可用
def get_verifycode():
    # 获取当前时间戳
    timestamp = time.time()
    url = 'http://newxk.urp.seu.edu.cn/xsxkapp/sys/xsxkapp/student/4/vcode.do?timestamp=' + str(int(timestamp));
    global vtoken
    # 创建cooliejar对象
    cookie = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie))
    urllib.request.install_opener(opener)
    req = urllib.request.Request(url)
    file = opener.open(req)
    vtoken = json.load(file)['data']['token']
    print(vtoken)
    img = urllib.request.urlopen(
        'http://newxk.urp.seu.edu.cn/xsxkapp/sys/xsxkapp/student/vcode/image.do?vtoken=' + vtoken, timeout=8)
    f = open('verifycode.jpg', 'wb')
    f.write(img.read())
    f.close()
    return 0

#解析Json
def JsonParse(datalist,StrJson):
    print("正在进行课表Json数据的解析")
    jsonObject = json.loads(StrJson)
    totalCount = jsonObject['totalCount']
    for i in range(0,int(totalCount)):
        str_select=str(jsonObject['dataList'][i]['selected'])
        if str_select=="False":
            classData=dict(courseName=jsonObject['dataList'][i]['courseName'])
            for j in range(0, int(jsonObject['dataList'][i]['number'])):
                classData['isFull']=str(jsonObject['dataList'][i]['tcList'][j]['isFull'])
                classData['isConflict'] = str(jsonObject['dataList'][i]['tcList'][j]['isConflict'])
                classData['teachingClassID']=str(jsonObject['dataList'][i]['tcList'][j]['teachingClassID'])
                classData['isChoose'] = str(jsonObject['dataList'][i]['tcList'][j]['isChoose'])
                classData['teacherName'] = str(jsonObject['dataList'][i]['tcList'][j]['teacherName'])
                classData['teachingPlace'] = str(jsonObject['dataList'][i]['tcList'][j]['teachingPlace'])
                datalist.append(classData)
    print(datalist)
    print("json解析完毕")

#解析json，通选课的json数据不同
def GJsonParse(datalist, StrJson):
    print("正在进行通选课Json数据的解析")
    jsonObject = json.loads(StrJson)
    totalCount = jsonObject['totalCount']
    for i in range(0, int(totalCount)):
        classData={}
        if((jsonObject['dataList'][i]['isChoose']) is None):
            classData['courseName'] = jsonObject['dataList'][i]['courseName']
            classData['isFull'] = jsonObject['dataList'][i]['isFull']
            classData['isConflict'] = jsonObject['dataList'][i]['isConflict']
            classData['teachingClassID'] = jsonObject['dataList'][i]['teachingClassID']
            classData['teacherName'] = jsonObject['dataList'][i]['teacherName']
            classData['teachingPlace'] = jsonObject['dataList'][i]['teachingPlace']
            datalist.append(classData)
    print(datalist)
    print("公选课json解析完毕")


#判断进度条
def login_update(self):
    global progress_bar
    global progress_var
    global progress
    global progressLabel
    if progress <= 100:
        progress_var.set(progress)
        root.update_idletasks()
    if progress < 19:
        progressLabel.config(text='正在拉取系统推荐课程...')
    if 20 <= progress <= 39:
        progressLabel.config(text='正在拉取人文选修课...')
    if 40 <= progress <= 59:
        progressLabel.config(text='正在拉取自然科学及经管选修课...')
    if 60 <= progress <= 79:
        progressLabel.config(text='正在拉取体育课...')
    if progress > 90:
        root.event_generate("<<EVENT_ON_CREATE>>")

# 弹出加载对话框
def login_start(self):
    global progress_var
    global progress_bar
    global progressLabel
    progress_var = DoubleVar()
    labelfont = ('times', 40, 'bold')
    progressLabel = Label(root, text="如果本页面长时未刷新\n请重启程序并确认账号密码验证码正确性\n反正不关我们事\n对了，目前只支持湖区选课", pady=110)
    progressLabel.config(font=labelfont)
    progressLabel.pack()
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
    progress_bar.pack(fill=BOTH, padx=20, pady=100)
    pass

#销毁进度条
def on_create(self):
    global progress_bar
    global progressLabel
    global tabs
    progressLabel.destroy()
    progress_bar.destroy()

#更新课程列表
def update_institute(args):
    global list_recommend
    global listbox1
    print('推荐课')
    listbox1.insert(END, "【以下是你目前未选择的“服从推荐”课程】点击选中课程后点右上【开始所选】按钮即可开始刷该门课程，请用鼠标滚轮来滑动列表，祝好运。")
    for i in range(0, list_recommend.__len__()):

        # print 'institute '+str(i)+str(list_institute[i][0])
        data=str(list_recommend[i]['courseName'])+" "+str(list_recommend[i]['teacherName'])+" "+str(list_recommend[i]['teachingPlace'])
        listbox1.insert(END, data)

def update_humanity(args):
    global list_humanity
    global listbox2
    print ("人文课")
    listbox2.insert(END, "点击选中课程后点右上【开始所选】按钮即可开始刷该门课程，请用鼠标滚轮来滑动列表，祝好运。")
    for i in range(0, list_humanity.__len__()):
        # print 'institute '+str(i)+str(list_humanity[i][0])
        data=str(list_humanity[i]['courseName'])+" "+str(list_humanity[i]['teacherName'])+" "+str(list_humanity[i]['teachingPlace'])
        listbox2.insert(END, data)


def update_science(args):
    global list_science
    global listbox3
    print ("社会科学")
    listbox3.insert(END, "点击选中课程后点右上【开始所选】按钮即可开始刷该门课程，请用鼠标滚轮来滑动列表，祝好运。")
    for i in range(0, list_science.__len__()):
        data=str(list_science[i]['courseName'])+" "+str(list_science[i]['teacherName'])+" "+str(list_science[i]['teachingPlace'])
        listbox3.insert(END,data)


def update_economy(args):
    global list_economics
    global listbox4
    print ("经济")
    listbox4.insert(END, "点击选中课程后点右上【开始所选】按钮即可开始刷该门课程，请用鼠标滚轮来滑动列表，祝好运。")
    for i in range(0, list_economics.__len__()):
        data=str(list_economics[i]['courseName'])+" "+str(list_economics[i]['teacherName'])+" "+str(list_economics[i]['teachingPlace'])
        listbox4.insert(END, data)


def update_seminar(args):
    global list_sports
    global listbox5
    print ("体育课")
    listbox5.insert(END, "点击选中课程后点右上【开始所选】按钮即可开始刷该门课程，请用鼠标滚轮来滑动列表，祝好运。")
    for i in range(0, list_sports.__len__()):
        data=str(list_sports[i]['courseName'])+" "+str(list_sports[i]['teacherName'])+" "+str(list_sports[i]['teachingPlace'])
        listbox5.insert(END,data)


def update_inter(args):
    global list_interinstitute
    global listbox6
    # print 'update ui list_interinstitute recieved'
    listbox6.insert(END, "点击选中课程后点右上【开始所选】按钮即可开始刷该门课程，请用鼠标滚轮来滑动列表，祝好运。")
    for i in range(0, list_interinstitute.__len__()):
        # print 'list_interinstitute '+str(i)+str(list_interinstitute[i][0])
        listbox6.insert(END, str(list_interinstitute[i][0]) + '    ' + str(list_interinstitute[i][1]) + '    ' + str(
            list_interinstitute[i][2]))

def on_select_success(args):
    global selected_num
    global mainLabel
    selected_num += 1
    count = int(selected_num)
    if flag_humanity != 1 or flag_economics != 1 or flag_science != 1:
        mainLabel.config(text="一键模式抢课成功，请查看课表")
    else:
        mainLabel.config(text="已经用本工具选到" + str(count) + "门课")
    pass

def about():
    dialog = Toplevel(root)
    dialog.geometry('280x190+360+300')
    dialog.title('关于本软件')
    Label(dialog, text="东南大学选课助手\n1.0测试版\n\n严禁一切商业用途\n关注本工具的最新动态，请移步本项目的github\n2016-9-27").pack()
    Button(dialog, text=' 移步过去资瓷一下 ', command=lambda: click_about("https://github.com/LeonidasCl/seu-jwc-catcher")).pack(
        pady=5)
    Button(dialog, text='   已 阅   ', command=lambda: dialog.destroy()).pack(pady=5)

def click_about(text):
    print("You clicked '%s'" % text)
    webbrowser.open_new(text)

def item_selected(args):
    # 获取选中项在box的下标和当前box在容器中的编号
    w = args.widget
    index = int(w.curselection()[0])
    index_tab = tabs.index(tabs.select())
    # 获取对应课程条目的选课id
    id_selected = 'false'
    if index_tab == 0:
        id_selected = list_institute[index - 1][2]
    if index_tab == 1:
        id_selected = list_humanity[index - 1][3]
    if index_tab == 2:
        id_selected = list_science[index - 1][3]
    if index_tab == 3:
        id_selected = list_economics[index - 1][3]
    if index_tab == 4:
        id_selected = list_seminar[index - 1][3]
    if index_tab == 5:
        id_selected = list_interinstitute[index - 1][3]
    # print 'You selected  tab:%d  item:"%d"  id:"%s"  ' % (index_tab, index,id_selected)
    # 检查该门课是否在刷课池以确定按钮展示方式
    if id_selected in list_selecting:
        btn_stop_specific.config(state='normal')
        btn_catch_specific.config(state='disabled')
    else:
        btn_catch_specific.config(state='normal')
        btn_stop_specific.config(state='disabled')

def catch_specific():
    global flag_economics
    global flag_humanity
    global flag_science
    index_tab = tabs.index(tabs.select())
    # print 'selected page is '+str(index_tab)
    # print 'selected item is ' + str(selected)
    # 获取对应课程条目的选课id
    id_selected = 'false'
    selected = -1
    if index_tab == 0:
        selected = int(listbox1.curselection()[0])
        id_selected = list_institute[selected - 1][2]
    if index_tab == 1:
        flag_humanity = 0
        selected = int(listbox2.curselection()[0])
        id_selected = list_humanity[selected - 1][3]
        # print '---------------append humanity'+str(id_selected)
        list_humanity_selecting.append(id_selected)
        # print str(list_economics_selecting)
    if index_tab == 2:
        flag_science = 0
        selected = int(listbox3.curselection()[0])
        id_selected = list_science[selected - 1][3]
        list_science_selecting.append(id_selected)
    if index_tab == 3:
        flag_economics = 0
        selected = int(listbox4.curselection()[0])
        id_selected = list_economics[selected - 1][3]
        list_economics_selecting.append(id_selected)
    if index_tab == 4:
        selected = int(listbox5.curselection()[0])
        id_selected = list_seminar[selected - 1][3]
    if index_tab == 5:
        selected = int(listbox6.curselection()[0])
        id_selected = list_interinstitute[selected - 1][3]
    # 将按钮状态更新
    btn_stop_specific.config(state='normal')
    btn_catch_specific.config(state='disabled')
    # 添加选课id到正在选课的列表
    list_selecting.append(id_selected)
    # 开始选课
    # print str(list_selecting)
    #thread.start_new_thread(select_worker, (index_tab, id_selected, selected - 1))

def stop_specific():
    index_tab = tabs.index(tabs.select())
    # print 'selected page is '+str(index_tab)
    # print 'selected item is ' + str(selected)
    # 获取对应条目的选课id
    id_selected = 'false'
    if index_tab == 0:
        selected = int(listbox1.curselection()[0])
        id_selected = list_institute[selected - 1][2]
    if index_tab == 1:
        selected = int(listbox2.curselection()[0])
        id_selected = list_humanity[selected - 1][3]
        list_humanity_selecting.remove(id_selected)
    if index_tab == 2:
        selected = int(listbox3.curselection()[0])
        id_selected = list_science[selected - 1][3]
        list_science_selecting.remove(id_selected)
    if index_tab == 3:
        selected = int(listbox4.curselection()[0])
        id_selected = list_economics[selected - 1][3]
        list_economics_selecting.remove(id_selected)
    if index_tab == 4:
        selected = int(listbox5.curselection()[0])
        id_selected = list_seminar[selected - 1][3]
    if index_tab == 5:
        selected = int(listbox6.curselection()[0])
        id_selected = list_interinstitute[selected - 1][3]
    # 将按钮状态更新
    btn_catch_specific.config(state='normal')
    btn_stop_specific.config(state='disabled')
    # 从正在选课的列表移除选课id
    # 该门课的值守线程发现选课id被移除就会结束
    list_selecting.remove(id_selected)


def stop_all():
    global list_selecting
    global list_economics_selecting
    global list_science_selecting
    global list_humanity_selecting
    # print 'stopping all '+str(list_selecting)
    list_selecting = []
    list_economics_selecting = []
    list_science_selecting = []
    list_humanity_selecting = []
    # print 'stopped all'+str(list_selecting)

def check_table():
    global username
    dialog = Toplevel(root)
    dialog.geometry('240x100+360+300')
    dialog.title('请输入学期')
    Label(dialog, text="例如，在下面的输入框中输入：16-17-2").pack()
    v = StringVar()
    Entry(dialog,textvariable=v).pack(pady=5)
    Button(dialog, text=' 查看课表 ', command=lambda: webbrowser.open_new(r"http://xk.urp.seu.edu.cn/jw_s"
                                                                      r"ervice/service/stuCurriculum.action?queryStudentId=" + str(
        username) + "&queryAcademicYear=" + v.get())).pack(pady=5)


if __name__ == "__main__":
    # preload.destroy()

    # global listbox1
    # global listbox2
    # global listbox3
    # global listbox4
    # global listbox5

    root = Tk()
    root.title("东南大学选课助手")
    root.resizable(width=False, height=False)
    root.geometry('960x500+100+100')
    root.bind("<<EVENT_LOGIN>>", login_start)
    root.bind("<<EVENT_LOGIN_UPDATE>>", login_update)
    root.bind("<<EVENT_ON_CREATE>>", on_create)

    frame0 = Frame(root)

    frame = Frame(root)

    frame2 = Frame(root)

    frame3 = Frame(root)

    tabs = ttk.Notebook(frame2)

    page_institute = ttk.Frame(tabs)
    listbox1 = Listbox(page_institute)


    page_humanities = ttk.Frame(tabs)
    listbox2 = Listbox(page_humanities)


    page_science = ttk.Frame(tabs)
    listbox3 = Listbox(page_science)


    page_economics = ttk.Frame(tabs)
    listbox4 = Listbox(page_economics)


    page_seminar = ttk.Frame(tabs)
    listbox5 = Listbox(page_seminar)



    #读完课程，更新拉取到的所有课程
    root.bind("<<UPDATE_INSTITUTE_LIST>>", update_institute)
    root.bind("<<UPDATE_HUMANOTY_LIST>>", update_humanity)
    root.bind("<<UPDATE_SCIENCE_LIST>>", update_science)
    root.bind("<<UPDATE_ECONOMICS_LIST>>", update_economy)
    root.bind("<<UPDATE_SEMINAR_LIST>>", update_seminar)
    #root.bind("<<UPDATE_INTER_LIST>>", update_inter)
    root.bind("<<SELECT_SUCCESS>>", on_select_success)


    preload = PreloadDialog(root)

    dlg = LoginDialog(root, '登录选课系统')



    listbox1.bind('<<ListboxSelect>>', item_selected)
    listbox1.pack(fill=BOTH)

    listbox2.bind('<<ListboxSelect>>', item_selected)
    listbox2.pack(fill=BOTH)

    listbox3.bind('<<ListboxSelect>>', item_selected)
    listbox3.pack(fill=BOTH)

    listbox4.bind('<<ListboxSelect>>', item_selected)
    listbox4.pack(fill=BOTH)

    listbox5.bind('<<ListboxSelect>>', item_selected)
    listbox5.pack(fill=BOTH)

    mainLabel = Label(frame0, text="已经用本工具选到0门课")
    mainLabel.config(font=('times', 20, 'bold'))
    mainLabel.pack(side=LEFT, padx=5)

    btn_catch_specific = Button(frame, text='开始所选', command=catch_specific)
    btn_stop_specific = Button(frame, text='停止所选', command=stop_specific)
    btn_stop_all = Button(frame, text='停止所有', command=stop_all)
    btn_table = Button(frame, text='查看课表', command=check_table)
    btn_about = Button(frame, text='关于', command=about)

    btn_catch_specific.pack(side=LEFT, padx=5)
    btn_catch_specific.config(state='disabled')
    btn_stop_specific.pack(side=LEFT, padx=5)
    btn_stop_specific.config(state='disabled')
    btn_stop_all.pack(side=LEFT, padx=5)
    btn_about.pack(side=RIGHT, padx=5)
    btn_table.pack(side=RIGHT, padx=5)





    # page_inter_institute = ttk.Frame(tabs)
    # listbox6 = Listbox(page_inter_institute)
    # listbox6.bind('<<ListboxSelect>>', item_selected)
    # listbox6.pack(fill=BOTH)

    tabs.add(page_institute, text='院系内可【服从推荐】课程')
    tabs.add(page_humanities, text='人文社科通选课程')
    tabs.add(page_science, text='自然科学通选课程')
    tabs.add(page_economics, text='经济管理通选课程')
    tabs.add(page_seminar, text='体育课程')
    # tabs.add(page_inter_institute, text='跨院系课程')
    tabs.pack(side=BOTTOM, expand=1, fill=BOTH, padx=10, pady=10)

    group1 = LabelFrame(frame3, text="院系内课程池", padx=5, pady=5)
    group1.pack(side=LEFT, padx=10, pady=10)
    pool1 = Listbox(group1, bg='black', fg='green')
    pool1.pack()

    group2 = LabelFrame(frame3, text="人文社科池", padx=5, pady=5)
    group2.pack(side=LEFT, padx=10, pady=10)
    pool2 = Listbox(group2, bg='black', fg='green')
    pool2.pack()

    group3 = LabelFrame(frame3, text="自然科学池", padx=5, pady=5)
    group3.pack(side=LEFT, padx=10, pady=10)
    pool3 = Listbox(group3, bg='black', fg='green')
    pool3.pack()

    group4 = LabelFrame(frame3, text="经济管理池", padx=5, pady=5)
    group4.pack(side=LEFT, padx=10, pady=10)
    pool4 = Listbox(group4, bg='black', fg='green')
    pool4.pack()

    group5 = LabelFrame(frame3, text="其它课程池", padx=5, pady=5)
    group5.pack(side=LEFT, padx=10, pady=10)
    pool5 = Listbox(group5, bg='black', fg='green')
    pool5.pack()

    frame0.pack(padx=5, pady=5)
    frame.pack(fill=X, padx=5, pady=5)
    frame2.pack(fill=X)
    frame3.pack(fill=BOTH)

    root.mainloop()