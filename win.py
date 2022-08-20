from flask import Flask, render_template, request,url_for,redirect,session, abort, redirect,send_file,jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_session import Session
from flask_pymongo import PyMongo
import bcrypt
from instascrape import Reel
import os
from dotenv import load_dotenv
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant, ChatGrant
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import time
import sys
import json
from flask_fontawesome import FontAwesome
import zipfile
from werkzeug.utils import secure_filename
from hurry.filesize import size
from datetime import datetime
import filetype
from flask_qrcode import QRcode
from urllib.parse import unquote
import socket 


win = Flask(__name__, template_folder = "templates", static_folder = "static")


hostname = socket.gethostname()    
IPAddr = socket.gethostbyname(hostname)    
print("Your Computer Name is: " + hostname)    
print("Your Computer IP Address is: " + IPAddr)   
maxNameLength = 15


fa = FontAwesome(win)

qrcode = QRcode(win)



win.secret_key = 'my_secret_key'

with open('config.json') as json_data_file:
    data = json.load(json_data_file)
hiddenList = data["Hidden"]
favList = data["Favorites"]
password = data["Password"]



currentDirectory=data["rootDir"]

osWindows = False 

default_view = 0

tp_dict = {'image':'photo-icon.png','audio':'audio-icon.png','video':'video-icon.png'}

if 'win32' in sys.platform or 'win64' in sys.platform:
    
    osWindows = True
   


if(len(favList)>3):
    favList=favList[0:3]
    
def make_zipfile(output_filename, source_dir):
    relroot = os.path.abspath(os.path.join(source_dir, os.pardir))
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zip:
        for root, dirs, files in os.walk(source_dir):
            zip.write(root, os.path.relpath(root, relroot))
            for file in files:
                filename = os.path.join(root, file)
                if os.path.isfile(filename):
                    arcname = os.path.join(os.path.relpath(root, relroot), file)
                    zip.write(filename, arcname)

load_dotenv()
account_sid = os.environ.get('AC3a8cd809aa06f20d85e37feb815035ee')
api_key_sid = os.environ.get('SKf1301874ab8a57f7f8d3a1cd3844fe68')
api_key_secret = os.environ.get('LVJgEonrAsBEnFeAzXhg9YxCZRya7JFe')
client = Client('SKf1301874ab8a57f7f8d3a1cd3844fe68','LVJgEonrAsBEnFeAzXhg9YxCZRya7JFe','AC3a8cd809aa06f20d85e37feb815035ee')


def get_chatroom(name):
    for conversation in client.conversations.conversations.stream():
        if conversation.friendly_name == name:
            return conversation


    return client.conversations.conversations.create(
        friendly_name=name)

win = Flask(__name__, template_folder = "templates", static_folder = "static")
win.debug = True
win.config['SECRET_KEY'] = 'secret_key'
win.config['SESSION_TYPE'] = 'filesystem'
win.config['MONGO_DBNAME'] = 'users'
win.config['MONGO_URI'] = 'mongodb+srv://new-user-31:RsVcWaFohW2a7ero@application1.erodfdx.mongodb.net/users'

mongo = PyMongo(win)

Session(win)

socketio = SocketIO(win, manage_session=False)


@win.route('/')
def main():
    return render_template("index.html")

@win.route('/signup', methods = ['POST','GET'])
def signup():
   if request.method == "POST":
        documents = mongo.db.documents
        existing_user = documents.find_one({'name' : request.form['email']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            hashpass = bcrypt.hashpw(request.form['phonenumber'].encode('utf-8'), bcrypt.gensalt())
            documents.insert_one({'name':request.form['email'], 'password': hashpass,'fname':request.form['firstName'],'lname':request.form['lastName'],'phno': hashpass})
            session['email'] =  request.form['email']
            session['firstName'] = request.form['firstName']
            session['phonenumber'] = request.form['phonenumber']
            return redirect(url_for('home'))
        else: 
            return 'User Already Exists'
   else:
        return render_template('signup.html')
@win.route('/login_user', methods = ['GET', 'POST'])
def login_user():
     if request.form == "GET":
        return render_template("signup.html")
     if request.form == "POST":
         documents = mongo.db.documents
         login_user = documents.find_one({'name': request.form.get['email']})
    
         if login_user:
             if bcrypt.hashpw(request.form.get['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
                session.get['email'] = request.form.get['email']
                return redirect(url_for('home'))
         else:
            return 'Invalid username or password'
     else:
         return render_template("loginpage.html")

@win.route('/welcome')
def welcome():
    return render_template("welcome.html")

@win.route('/indexes', methods=['GET', 'POST'])
def index():
    return render_template('indexes.html')

@win.route('/chat',methods = ['POST', 'GET'])
def chat():
    if request.method == 'POST':
        username = request.form['username']
        room = request.form['room']
        session['username'] = username
        session['room'] = room
        return render_template('chat.html', session=session)
    else:
        if session.get('username') is not None:
            return render_template('chat.html', session=session)
        else:
            return redirect(url_for('index'))
@socketio.on('join', namespace='/chat')
def join():
    room = session.get('room')
    join_room(room)


@socketio.on('text', namespace='/chat')
def text(message):
    room = session.get('room')
    emit('message', {'msg':  session.get('username') + ' : ' + message['msg']}, room=room)


@socketio.on('left', namespace='/chat')
def left(message):
    room = session.get('room')
    username = session.get('username')
    leave_room(room)
    session.clear()
    emit('status', {'msg': username + ' has left the room.'}, room=room)

@win.route('/home')
def home():
    return render_template("homepage.html")

@win.route('/telegram')
def telegram():
    return render_template("telegram.html")

@win.route('/addaccount', methods = ['POST', 'GET'])
def addaccount():
     if request.method == "POST":
        adduser = mongo.db.adduser
        add_user = adduser.find_one({'addame' : request.form['email-1']})

        if add_user is None:
            hashpass = bcrypt.hashpw(request.form['pass-2'].encode('utf-8'), bcrypt.gensalt())
            adduser.insert_one({'addname':request.form['email-1'], 'password': hashpass})
            session['email-1'] =  request.form['email-1']
            return redirect(url_for('home'))
        else: 
            return 'User Already Exists'
     else:
       return render_template("addaccount.html")

@win.route('/cprofile')
def cprofile():
    return render_template("cprofile.html")

@win.route('/files')
def files():
    return render_template("files.html")

@win.route('/telegram_user')
def telegram_user():
    return render_template("telegrampage.html")

@win.route('/forget')
def forget():
    return render_template("forget.html")

@win.route('/hfeedback', methods=['POST', "GET"])
def hfeedback():
    if request.form == "POST":
        feed = mongo.db.adduser
        feed_back = feed.find_one({'feedname' : request.form['feedemail-2']})

        if feed_back is None:
            hashpass = bcrypt.hashpw(request.form['feedphonenumber-2'].encode('utf-8'), bcrypt.gensalt())
            feed.insert_one({'feedname':request.form['feedemail-2'], 'feedphonenumber': hashpass, 'feeddes':request.form['feeddescription-2']})
            session['feedemail-2'] =  request.form['feedemail-2']
            return redirect(url_for('home'))
    else:
     return render_template("hfeedback.html")

@win.route('/hlang')
def hlang():

    return render_template("hlang.html")
@win.route('/homeabout')
def homeabout():
    return render_template("homeabout.html")

@win.route('/homealter', methods = ['POST', 'GET'])
def homealter():
    if request.method == "POST":
        adduser = mongo.db.adduser
        add_user = adduser.find_one({'addnumber' : request.form['alternumber']})

        if add_user is None:
            adduser.insert_one({'addnumber':request.form['alternumber']})
            session['alternumber'] =  request.form['alternumber']
            return redirect(url_for('home'))
        else: 
            return 'User Already Exists'
    else:
        return render_template("homealternatepage.html")
@win.route('/homemail', methods = ['POST', 'GET'])
def homemail():
    if request.method == "POST":
        adduser = mongo.db.adduser
        add_user = adduser.find_one({'addemail' : request.form['homeemail-1']})

        if add_user is None:
            adduser.insert_one({'addemail':request.form['homeemail-1']})
            session['homeemail-1'] =  request.form['homeemail-1']
            return redirect(url_for('home'))
        else: 
            return 'User Email Already Exists'
    else:
      return render_template("homeemailpage.html")
@win.route('/homefont')
def homefont():
    return render_template("homefont.html")

@win.route('/homelegal')
def homelegal():
    return render_template("homelegal.html")
@win.route('/homereg', methods = ['POST', 'GET'])
def homereg():
    if request.method == "POST":
        adduser = mongo.db.adduser
        add_user = adduser.find_one({'newnumber' : request.form['registernumber']})

        if add_user is None:
            adduser.insert_one({'newnumber':request.form['registernumber']})
            session['registernumber'] =  request.form['registernumber']
            return redirect(url_for('home'))
        else: 
            return 'User addnew Number'
    else:
      return render_template("homeregisterpage.html")
@win.route('/hprofile')
def hprofile():
    return render_template("hprofile.html")
@win.route('/hsettings')
def homeset():
    return render_template("hsettings.html")

@win.route('/hthemepage')
def hometheme():
    return render_template("hthemepage.html")
@win.route('/rdownload')
def downloadreel():
    return render_template("rdownload.html")
@win.route('/rguide')
def rguide():
    return render_template("rguide.html")

@win.route('/chatnumber', methods =['POST', 'GET'])
def chatnumber():
     if request.method == "POST":
        adduser = mongo.db.adduser
        add_user = adduser.find_one({'old_number' : request.form['number-1']})

        if add_user is None:
            adduser.insert_one({'old_number':request.form['number-1'], 'new_number': request.form['number-2']})
            session['number-1'] =  request.form['number-1']
            session['number-2'] =  request.form['number-2']
            return redirect(url_for('home'))
        else: 
            return 'already number exists'
     else:
      return render_template("chatchangenumber.html")

@win.route('/rhistory')
def reelhis():
    return render_template("rhistory.html")
@win.route('/rsave')
def reelsave():
    return render_template("rsave.html")
@win.route('/status')
def status():
    return render_template("status.html")

@win.route('/stsdownloads')
def statusdown():
    return render_template("stsdownloads.html")
@win.route('/stsguide')
def statusgui():
    return render_template("stsgu.html")

@win.route('/stslan')
def stslan():
    return render_template("stslan.html")

@win.route('/stsvideos')
def stsvideos():
    return render_template("stsvideos.html")


@win.route('/reel',methods=['GET'])
def reel():
    if request.form == "GET":
        link = request.form.get["Reel"]
        SESSIONID = "{5640599364%3ACORrAuUCLR9YFw%3A13%3AAYe6aICJvHpt0zAj8aqNCDuZIrIHy3Gghk8F_cF7Bw}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.74 Safari/537.36 Edg/79.0.309.43",
            "cookie":f'sessionid={SESSIONID};'
        }   
        reel=Reel(link)
        reel.scrape(headers=headers)
        reel.download(fp=f".\\reel{int(time.time())}.mp4")
    return render_template("reel.html") 
            

@win.route('/chatsettings')
def chatsettings():
    return render_template("chatsettings.html")

@win.route('/chatprivacy')
def chatprivacy():
    return render_template("chatprivacy.html")

@win.route('/chatprofile')
def chatprofile():
    return render_template("chatprofile.html")

@win.route('/chatwall')
def chatwall():
    return render_template("chatwall.html")
@win.route('/stsimage')
def stsimage():
    return render_template("stsimage.html")
@win.route('/callvideo')
def video():
    return render_template("video.html")

@win.route('/logins', methods=['POST'])
def logins():
    username = request.get_json(force=True).get('username')
    if not username:
        abort(401)

    conversation = get_chatroom('My Room')
    try:
        conversation.participants.create(identity=username)
    except TwilioRestException as exc:
        
        if exc.status != 409:
            raise

    token = AccessToken(account_sid,api_key_sid,api_key_secret, identity=username)
    token.add_grant(VideoGrant(room='My Room'))
    token.add_grant(ChatGrant(service_sid = conversation.chat_service_sid))

    return {'token': token.to_jwt().decode(),
            'conversation_sid': conversation.sid}

@win.route('/chatdelete')
def chatdel():
    return render_template("chatdelete.html")

@win.route('/filesdesktop')
def filesdsk():
    return render_template("filesdesktop.html")
@win.route('/filesdoc')
def filesdoc():
    return render_template("filesdoc.html")

@win.route('/filesdownloads')
def filesdownloads():
    return render_template("filesdownloads.html")

@win.route('/filespc')
def filespc():
    return render_template("filesPC.html")

@win.route('/filespic')
def filespic():
    return render_template("filespic.html")

@win.route('/newcon')
def newcon():
    return render_template("newcon.html")
@win.route('/login/')
@win.route('/login/<path:var>')
def loginMethod(var=""):
    global password

   

    if(password==''):
        session['login'] = True


    if('login' in session):
        return redirect('/'+var)
    else:
        return render_template('login.html')


@win.route('/login/', methods=['POST'])
@win.route('/login/<path:var>', methods=['POST'])
def loginPost(var = ""):
    global password



    text = request.form['text']
    if(text==password):
        session['login'] = True

        return redirect('/'+var)
    else:
        return redirect('/login/'+var)

@win.route('/logout/')
def logoutMethod():
    if('login' in session):
        session.pop('login',None)
    return redirect('/login/')
    

def hidden(path):

    for i in hiddenList:
        if i != '' and i in path:
            return True
    
    return False



def changeDirectory(path):
    global currentDirectory, osWindows


    pathC = path.split('/')
 

    if(osWindows):
        myPath = '//'.join(pathC)+'//'
    else:
        myPath = '/'+'/'.join(pathC)

  
    myPath = unquote(myPath)
  

    print(currentDirectory)
    
    try:
        os.chdir(myPath)
        ans=True
        if (osWindows):
            if(currentDirectory.replace('/','\\') not in os.getcwd()):
                ans = False
        else: 
            if(currentDirectory not in os.getcwd()):
                ans = False
    except:
        ans=False
    
    

    return ans


@win.route('/changeView')
def changeView():
    global default_view

 

    v = int(request.args.get('view', 0))

    if v in [0,1]:
        default_view = v
    else:
        default_view = 0


    return jsonify({
 
        "txt":default_view,
     
    })



def getDirList():
    

    global maxNameLength,tp_dict,hostname

    dList = list(os.listdir('.'))
    dList= list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
    dir_list_dict = {}
    fList = list(filter(lambda x: not os.path.isdir(x), os.listdir('.')))
    file_list_dict = {}
    curDir=os.getcwd()
  



    for i in dList:
        if(hidden(curDir+'/'+i)==False):
            image = 'folder5.png'

            if len(i)>maxNameLength:
                dots = "..."
            else:
                dots = ""

            dir_stats = os.stat(i)
            dir_list_dict[i]={}
            dir_list_dict[i]['f'] = i[0:maxNameLength]+dots
            dir_list_dict[i]['f_url'] = i
            dir_list_dict[i]['currentDir'] = curDir
            dir_list_dict[i]['f_complete'] = i
            dir_list_dict[i]['image'] = image
            dir_list_dict[i]['dtc'] = datetime.utcfromtimestamp(dir_stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            dir_list_dict[i]['dtm'] = datetime.utcfromtimestamp(dir_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            dir_list_dict[i]['size'] = "---"


    for i in fList:
        if(hidden(curDir+'/'+i)==False):
            image = None
            try:
                kind = filetype.guess(i)

                if kind:
                    tp = kind.mime.split('/')[0]

                    if tp in tp_dict:
                        image = tp_dict[tp]
            except:
                pass

            if not image:
                image = 'file-test2.png'

            if len(i)>maxNameLength:
                dots = "..."
            else:
                dots = ""
        
            

            file_list_dict[i]={}
            file_list_dict[i]['f'] = i[0:maxNameLength]+dots
            file_list_dict[i]['f_url'] = i
            file_list_dict[i]['currentDir'] = curDir
            file_list_dict[i]['f_complete'] = i
            file_list_dict[i]['image'] = image

            try:
                dir_stats = os.stat(i)
                file_list_dict[i]['dtc'] = datetime.utcfromtimestamp(dir_stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                file_list_dict[i]['dtm'] = datetime.utcfromtimestamp(dir_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                file_list_dict[i]['size'] = size(dir_stats.st_size)
            except:
                file_list_dict[i]['dtc'] = "---"
                file_list_dict[i]['dtm'] = "---"
                file_list_dict[i]['size'] = "---"


    return dir_list_dict,file_list_dict


def getFileList():

    dList = list(filter(lambda x: os.path.isfile(x), os.listdir('.')))

    finalList = []
    curDir=os.getcwd()

    for i in dList:
        if(hidden(curDir+'/'+i)==False):
            finalList.append(i)

    return(finalList)





@win.route('/files/', methods=['GET'])
@win.route('/files/<path:var>', methods=['GET'])
def filePage(var = ""):
    global default_view


    if('login' not in session):
        return redirect('/login/files/'+var)

    
    if(changeDirectory(var)==False):
      
        print("Directory Doesn't Exist")
        return render_template('404.html',errorCode=300,errorText='Invalid Directory Path',favList=favList)
     
    print(default_view)

    try:
        dir_dict,file_dict = getDirList()
        print(default_view)
        if default_view == 0:
            var1,var2 = "DISABLED",""
            default_view_css_1,default_view_css_2 = '','style=display:none'
        else:
            var1,var2 = "","DISABLED"
            default_view_css_1,default_view_css_2 = 'style=display:none',''


    except:
        return render_template('404.html',errorCode=200,errorText='Permission Denied',favList=favList)
    


    if osWindows:
        cList = var.split('/')
        var_path = '<a style = "color:black;"href = "/files/'+cList[0]+'">'+unquote(cList[0])+'</a>'
        for c in range(1,len(cList)):
            var_path += ' / <a style = "color:black;"href = "/files/'+'/'.join(cList[0:c+1])+'">'+unquote(cList[c])+'</a>'
        
    else:
        cList = var.split('/')
        var_path = '<a href = "/files/"><img src = "/static/root.png" style = "height:25px;width: 25px;">&nbsp;</a>'
        for c in range(0,len(cList)):
            var_path += ' / <a style = "color:black;"href = "/files/'+'/'.join(cList[0:c+1])+'">'+unquote(cList[c])+'</a>'


    return render_template('home.html',currentDir=var,favList=favList,default_view_css_1=default_view_css_1,default_view_css_2=default_view_css_2,view0_button=var1,view1_button = var2,currentDir_path=var_path,dir_dict=dir_dict,file_dict=file_dict)



@win.route('/', methods=['GET'])
def homePage():

    global currentDirectory, osWindows

    if('login' not in session):
        return redirect('/login/')
    
    print(currentDirectory)
    if osWindows:
        if(currentDirectory == ""):
            return redirect('/files/C:')
        else:
            

            cura='>'.join(currentDirectory.split('\\'))
            return redirect('/files/'+cura)
    else:
        return redirect('/files/'+currentDirectory)
        
        


@win.route('/download/<path:var>')
def downloadFile(var):

    if('login' not in session):
        return redirect('/login/download/'+var)
    
    

    
    pathC = unquote(var).split('/')
    if(pathC[0]==''):
        pathC.remove(pathC[0])
    
   

    if osWindows:
        fPath = '//'.join(pathC)
    else:
        fPath = '/'+'//'.join(pathC)

    

    f_path_hidden = '//'.join(fPath.split("//")[0:-1])



    
    if(hidden(f_path_hidden) == True or changeDirectory(f_path_hidden)== False):
       
        return render_template('404.html',errorCode=100,errorText='File Hidden',favList=favList)


    fName=pathC[len(pathC)-1]
   
    return send_file(fPath, download_name=fName)
    try:
        return send_file(fPath, download_name=fName)
    except:
        return render_template('404.html',errorCode=200,errorText='Permission Denied',favList=favList)



@win.route('/downloadFolder/<path:var>')
def downloadFolder(var):

    if('login' not in session):
        return redirect('/login/downloadFolder/'+var)
    

    pathC = var.split('/')
    if(pathC[0]==''):
        pathC.remove(pathC[0])
    
    if osWindows:
        fPath = '//'.join(pathC)
    else:
        fPath = '/'+'//'.join(pathC)
    
    
    
    f_path_hidden = '//'.join(fPath.split("//")[0:-1])
    
    if(hidden(f_path_hidden) == True or changeDirectory(f_path_hidden)== False):
        #FILE HIDDEN
        return render_template('404.html',errorCode=100,errorText='File Hidden',favList=favList)


    fName=pathC[len(pathC)-1]+'.zip'
    
    try:
        make_zipfile('C:\\Users\\reall\\Downloads\\temp\\abc.zip',os.getcwd())
        return send_file('C:\\Users\\reall\\Downloads\\temp\\abc.zip', attachment_filename=fName)
    except:
        return render_template('404.html',errorCode=200,errorText='Permission Denied',favList=favList)


@win.errorhandler(404)
def page_not_found(e):
    if('login' not in session):
        return redirect('/login/')
    
    
    return render_template('404.html',errorCode=404,errorText='Page Not Found',favList=favList), 404


@win.route('/upload/', methods = ['GET', 'POST'])
@win.route('/upload/<path:var>', methods = ['GET', 'POST'])
def uploadFile(var=""):

    if('login' not in session):
    
        return render_template('login.html')

    text = ""
    if request.method == 'POST':
        pathC = var.split('/')

        if(pathC[0]==''):
            pathC.remove(pathC[0])
        
    

        if osWindows:
            fPath = +'//'.join(pathC)
        else:
            fPath = '/'+'//'.join(pathC)
    
        f_path_hidden = fPath

      

        if(hidden(f_path_hidden) == True or changeDirectory(f_path_hidden)== False):
           
            return render_template('404.html',errorCode=100,errorText='File Hidden',favList=favList)


        files = request.files.getlist('files[]') 
        fileNo=0
        for file in files:
            fupload = os.path.join(fPath,file.filename)

            if secure_filename(file.filename) and not os.path.exists(fupload):
                try:
                    file.save(fupload)    
                    print(file.filename + ' Uploaded')
                    text = text + file.filename + ' Uploaded<br>'
 
                    fileNo = fileNo +1
                except Exception as e:
                    print(file.filename + ' Failed with Exception '+str(e))
                    text = text + file.filename + ' Failed with Exception '+str(e) + '<br>'

                    continue
            else:
                print(file.filename + ' Failed because File Already Exists or File Type Issue')
                text = text + file.filename + ' Failed because File Already Exists or File Type not secure <br>'

            
          
    fileNo2 = len(files)-fileNo
    return render_template('uploadsuccess.html',text=text,fileNo=fileNo,fileNo2=fileNo2,favList=favList)



    
        

@win.route('/qr/<path:var>')
def qrFile(var):
    global hostname

    if('login' not in session):
        return redirect('/login/qr/'+var)
    
    
    
    
    pathC = unquote(var).split('/')
    if(pathC[0]==''):
        pathC.remove(pathC[0])
    

    if osWindows:
        fPath = '//'.join(pathC)
    else:
        fPath = '/'+'//'.join(pathC)

    
    f_path_hidden = '//'.join(fPath.split("//")[0:-1])
    
    if(hidden(f_path_hidden) == True or changeDirectory(f_path_hidden)== False):
        
        return render_template('404.html',errorCode=100,errorText='File Hidden',favList=favList)
    

    fName=pathC[len(pathC)-1]
   
    qr_text = 'http://'+hostname+"//download//"+fPath

   
    return send_file(qrcode(qr_text, mode="raw"), mimetype="image/png")
    return send_file(fPath, attachment_filename=fName)

if __name__ == "__main__":
    win.run(debug=True)
    win.run(host='0.0.0.0')
    socketio.run(win)
    win.run(host= '0.0.0.0',debug=True,port=5000)