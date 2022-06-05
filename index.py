###
### Краткое описание того что нужно для работы
### https://github.com/l3lackShark/gosumemory и запущенная игра осу
### Программа находит файлы карты с помощью goosumemory и отправляет на бесплатный фтп сервер архив с расширением
### .osz(файлы карт в игре(по факту этот тот же архив .zip,только со своим названием расширения)) и названием <md5>.osz
### и после этого отправляет на node.js сервер инфу о том что карта загружена,
### сервер ведёт трекинг всех игроков с запущенным клиентом по md5 хешу выбранной карты,и группирует их по этому хешу
### когда клиент выкладывает карту на сервер посылается запрос "Done:<username>:<md5>" 
### и по сокету на другие клиент приходит md5 хеш,после этого они подключаются к тому же фтп серверу
### и скачивают ту же самую карту
### 
### Иногда можно встретить комментарии на английском,мне так проще думать пока работаешь
###
### Пока что не реализовано: 
### Открытие карты(игра сама распоковывает карту и кидает файлы в папку .../osu!/Songs) после скачивания
### 
### Что можно добавить/изменить:
### НЕ использовать фтп сервер,слишком медленно
### Добавить везде catch и try,сейчас код просто крашится
### 
### 
### 
### 

from time import sleep
import socket
import json
import os
import zipfile
import urllib.request
import ftplib
import glob
import shutil
import threading


hostname = '192.168.0.106' #server host ip
# hostname = 'localhost'
port = 5051

class PlayerClient:
    def __init__(self,username = None,oldmd5 = None,md5 = None):
        self.username = username
        self.oldmd5 = oldmd5
        self.md5 = md5
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.osupath = ""
        self.connected = False

    def connectandupdate(self,addr,port):
        # print(self.username)
        # print("plr",plr)
        # print("self",self)
        userdata = "{\n\t\"username\": \"" + self.username + "\",\n\t\"oldmd5\": \"" + self.oldmd5 + "\",\n\t\"md5\": \"" + self.md5 + "\"\n}"
        if self.connected == False:
            self.socket.connect((hostname,port))
        self.socket.send(bytes(userdata,'utf-8'))
        # print(userdata)
        if self.connected == False:
            th = threading.Thread(target=self.listen_to_server,args=(self.socket,))
            th.start()
        self.connected = True

    def newmd5(self,newmd5):
        self.oldmd5 = self.md5
        self.md5 = newmd5
        
    def sendmap(self,s):
        print("start sending map")
        file = open(os.path.dirname(os.path.abspath(__file__))+'\\'+plr.md5+'.osz','rb')
        session = ftplib.FTP('hostname','ftpuser','ftppassword')
        print("FTP response: ",session.storbinary('STOR '+ plr.md5 +'.osz', file))
        session.close()
        file.close()
        s.send(b'done:' + bytes(self.username + ":" + self.md5,"utf-8"))
        print("End sending map")

    def listen_to_server(self,s):
        print('listener start')
        while 1:
            sleep(0.2)
            data = s.recv(1024)
            print(data)
            if data != b"":
                if data == b"sendmap":
                    PackAndSendMap(1,1,self)
                elif data[0] == 109: #m #input info is "m<md5 hash с длинной 32 символа>"
                    data = data[1:] #delete indeficator if we accepting map
                    data = str(data)
                    data = data[2:-1] #delete b'/.../' form converting bytes to str
                    data = data
                    print("recived newmd5,type r to recive")
                    # if len(data) == 32: для дальнейшей проверки что качаем то что надо
                    with open(os.path.dirname(os.path.abspath(__file__)) + "\\"+ data +".osz", "wb") as file:
                        # Команда для получения файла с фтп сервера "RETR filename"
                        session = ftplib.FTP('hostname','ftpuser','ftppassword')
                        Dfile = session.retrbinary("RETR " + data + ".osz",file.write)
                        session.close()
                        file.close()
                        print("downloaded: ",data)
                elif data[0] == 78: #L
                    data = str(data)
                    data = data[2:-1]
                    data = data.split(':')
                    self.newmd5(data[1])

global plr

plr = PlayerClient() #define blank player as a global var

def getjsondata():
    response = urllib.request.urlopen("http://127.0.0.1:24050/json") # load info from goosumemory local server
    return json.load(response)

def globallistener(plr):
    print("globallistener start")
    data = getjsondata()
    olddata = data
    while 1:
        sleep(1)
        data = getjsondata()
        if data['menu']['bm']['md5'] != olddata['menu']['bm']['md5']:
            plr.newmd5(data['menu']['bm']['md5'])
            plr.connectandupdate(hostname,port)
        olddata = data

#functions init
def SendMap(plr):
    print("funccalled")
    s = socket.socket()
    try:
        s.connect(("127.0.0.1",24050))
        print("Go osumemory running")
        print("pre Thread",plr)
        listenerth = threading.Thread(target=globallistener,args=[plr])
        listenerth.start()
        s.close()
    except socket.error as e:
        #TODO launch osumemory
        print("goosumemory didn't running")
        print(e)
        s.close()
        return

def PackAndSendMap(WithVideo,OneDiff,plr):
    Pagejson = getjsondata()
    osufolder = Pagejson['settings']['folders']['songs']
    diffFile = Pagejson['menu']['bm']['path']['file']
    mapfolder = Pagejson['menu']['bm']['path']['folder']
    diffpath = osufolder + "\\" + mapfolder
    # удалённая функция поиска файла фонового видео в файле карты
    # difffileP = open(str(diffpath+"\\"+Pagejson['menu']['bm']['path']['file']).replace("\\","/"),'r')
    # VideoName = ""
    # if WithVideo != 0 or OneDiff !=0:
    #     for line in difffileP:
    #         # print(line)
    #         if line == "[Events]\n":
    #             findvideoB = True
    #         if line.rfind("Video") != -1 and line[:2] != "//" and findvideoB == True: #?????
    #             VideoName = line.split(",")[2].replace('"', '') #reutrns video.mp4\n
    #             VideoName = VideoName[:-1] #delete '\n'
    #             print(VideoName)
    #         if line == "[TimingPoints]\n":
    #             break

    #copy files from map because just packing didnt work
    for filename in glob.glob(os.path.join(diffpath, '*.*')): 
        shutil.copy(filename, os.path.dirname(os.path.abspath(__file__)) + "\\copydir")
    print("copying files")
    #creating archive
    zf = zipfile.ZipFile(os.path.dirname(os.path.abspath(__file__)) + "\\" + plr.md5 + ".osz", "w")
    print("creating file...")
    for dirname, subdirs, files in os.walk(os.path.dirname(os.path.abspath(__file__)) + "\\copydir"):
        for filename in files:
            zf.write(os.path.join(dirname, filename),filename)
            print("packed: ",filename)
    zf.close()
    #delete files from temp dir
    for filename in os.listdir(os.path.dirname(os.path.abspath(__file__)) + "\\copydir"):
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)) + "\\copydir", filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    print("done")
    plr.sendmap(plr.socket)


#####
##### Main Func
#####
jsondata = getjsondata()
#get the username because for some reason i have no username from goosumemory
username = ""
files = []
osufolder = str(jsondata['settings']['folders']['game'])
os.chdir(osufolder)
for file in glob.glob("osu!.[a-zA-Z0-9]*.cfg"): #gets osu!.[smthhere].cfg,it's a usercfg
    files.append(file)
file = open(str(jsondata['settings']['folders']['game']) + "\\" + files[0],'r',encoding='utf-8')
for line in file:
    if line.__contains__('Username'):
        line = line.split("=")
        print(line)
        username = line[1] #Username =( arsenii0) 
        username = username[1:-1] #delete space and \n
        break
plr = PlayerClient(username,oldmd5="",md5=jsondata['menu']['bm']['md5'])
plr.connectandupdate(hostname,port)
SendMap(plr)

while 1: #все основные функции работают в отдельных потоках,по этому бесконечный цикл ни на что не влияет
    act = input("action: ")
    if act == "s": #send
        PackAndSendMap(0,0,plr)
    elif act == "q": #quit
        quit()