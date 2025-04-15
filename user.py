from flask import *
from database import *
import uuid
import nltk
import face_recognition
nltk.download('punkt')
nltk.download('stopwords')
# render_template
user = Blueprint ("user",__name__)


@user.route('/user_home')
def user_home():
    
    login_id=session['login_id']
    data={} 
    q1="select * from user inner join login on user.login_id = login.login_id where user.login_id='%s'"%(login_id)
    data=select(q1)
    
    return render_template("user/user_home.html" , data=data)


@user.route("/user_change_password" , methods=['post' , 'get'])
def user_change_password():
    login_id=session['login_id']
    if "submit" in request.form:
        password=request.form['password']
        q1="UPDATE `login` SET password='%s' WHERE login_id='%s'"%(password,login_id)
        update(q1)
        return "<script>alert('password changed');window.location='/user_change_password';</script>"
    return render_template('user/user_change_password.html')

@user.route("/view_profile")
def view_profile():
    login_id=session['login_id']
    data={} 
    q1="select * from user inner join login on user.login_id = login.login_id where user.login_id='%s'"%(login_id)
    data=select(q1)
    return render_template('user/view_profile.html' , data=data)


@user.route("/user_add_post",methods=['get','post'])
def add_post():
    user_id=session['user_id']
    print(user_id,"useridddddddddddd")
    print(user_id,"++++++++++++++++++++++++++++++++++++++")
    if 'submit' in request.form:
        photo=request.files['photo']
        description=request.form['description']
        path="static/posts/"+str(uuid.uuid4())+photo.filename
        photo.save(path)
        description_list=description.split(" ")
        if len(description_list)<4:
            if description in mylist:
                d="normal"
                q1="insert into post values(NULL,'%s',now(),'%s','%s','posted','Normal')"%(user_id,description,path)
                id=insert(q1)
        else:
            d=predict_bully(description)
            if d == "normal":
                q1="insert into post values(NULL,'%s',now(),'%s','%s','posted','Normal')"%(user_id,description,path)
                id=insert(q1)
            else:
                q1="insert into post values(NULL,'%s',now(),'%s','%s','posted','Bully')"%(user_id,description,path)
                id=insert(q1)
                q2="update `user` set `bullying_count`=`bullying_count`+1 where `user_id`='%s'"%(user_id)
                update(q2)
        knownimage = []
        knownids = []
        qry = "SELECT * FROM `user` WHERE `user_id` !='"+str(user_id)+"'"
        l = select(qry)  
        mom=0

        for i in l:
            s = "C:\\Users\\User\\Desktop\\cybercrime\\"
            m = s + i["photo"]
            print(m)

            picture_of_me = face_recognition.load_image_file(m)
            my_face_encoding = face_recognition.face_encodings(picture_of_me)[0]

            print(my_face_encoding)
            knownimage.append(my_face_encoding)
            knownids.append(i["user_id"])


        picture_of_post = face_recognition.load_image_file(path)
        others_face_encoding = face_recognition.face_encodings(picture_of_post)

        totface = len(others_face_encoding)
        print(totface)


        for detected_face in others_face_encoding:
            res = face_recognition.compare_faces(knownimage, detected_face, tolerance=0.5)

            for idx, match in enumerate(res):
                if match:
                    print("Match found for user ID:", knownids[idx])
                    print("Inserting notification...")
                    qrry1 = "INSERT INTO `notification` (`post_id`, `date`, `status`, `user_id`) VALUES ('"+str(id)+"', CURDATE(), 'pending','"+str(knownids[idx])+"')"
                    insert(qrry1)  
                    mom+=1
        if mom>0:
            q2="update `user` set `bullying_count`=`bullying_count`+1 where `user_id`='%s'"%(user_id)
            update(q2)
            q2="update `post` set `status`='pending' where `post_id`='%s'"%(id)
            update(q2)
        return "<script>alert('post added');window.location='/user_home';</script>"
    return render_template("user/add_post.html")

@user.route("/view_my_post")
def view_my_post():
    data={}
    user_id=session['user_id']
    q1 = """
            SELECT post.*, user.user_id, user.username, user.photo AS profile_pic 
            FROM post 
            INNER JOIN user ON post.user_id = user.user_id 
            WHERE user.user_id = %s
            """ % (user_id)
    data=select(q1)
    return render_template("user/view_my_post.html",data=data)

@user.route("/view_notifications")
def view_notifications():
    data={}
    user_id=session['user_id']
    q1 = """
            SELECT post.*, user.user_id, user.username, user.photo AS profile_pic ,notification.status as nstatus,
            notification_id
            FROM post 
            INNER JOIN user ON post.user_id = user.user_id 
            inner join notification on notification.post_id=post.post_id 
            WHERE notification.user_id = %s
            """ % (user_id)
    data=select(q1)
    return render_template("user/view_notifications.html",data=data)

@user.route("/approve_post/<nid>/<pid>")
def approve_post(nid,pid):
    qry="update notification set status='approved' where notification_id='"+nid+"'"
    update(qry)
    qry2="select * from notification where status='pending' and post_id='"+pid+"'"
    res=select(qry2)
    if len(res)>0:
        pass
    else:
        qry="update post set status='posted' where post_id='"+pid+"'"
        update(qry)
    return '''<script>alert('Post Approved');window.location='/view_notifications'</script>'''

@user.route("/reject_post/<nid>/<pid>")
def reject_post(nid,pid):
    qry="update notification set status='rejected' where notification_id='"+nid+"'"
    update(qry)
    
    return '''<script>alert('Post Rejected');window.location='/view_notifications'</script>'''

@user.route("/view_post_of_friends")
def view_post_of_friend_list():
    user_id = session['user_id']
    friend_id=request.args.get('id')
    session['frnd_post_id']=friend_id
    data={}
    q1="""
    SELECT post.*, user.photo as userphoto, user.f_name as name 
    FROM post
    INNER JOIN user ON post.user_id = user.user_id
    INNER JOIN request ON 
        ((request.from_id = post.user_id AND request.to_id = %s) 
        OR (request.to_id = post.user_id AND request.from_id = %s))
    WHERE post.status='posted' and request.r_status = 'friends'
    """ % (user_id, user_id)
    data=select(q1)
    print(q1)
    return render_template("user/view_post_of_friends.html",data=data)

@user.route("/view_specific_friend_post")
def view_single_friend_post():
    friend_id = request.args.get('id')  
    # if not friend_id:
    #     return "Friend ID is required", 400

    data = {}


    q1 = """
    SELECT post.*, user.photo as userphoto, user.username as name 
    FROM post
    INNER JOIN user ON post.user_id = user.user_id
    WHERE post.status='posted' and post.user_id = %s
    """ % (friend_id)

    data = select(q1)
    return render_template("user/view_specific_friend_post.html", data=data)

@user.route("/update_profile",methods=['get','post'])
def update_profile():
    login_id=session['login_id']
    data={}
    user_id=session['user_id']
    q1="select * from user inner join login on login.login_id=user.login_id where user_id='%s'"%(user_id)
    data=select(q1)
    if "submit" in request.form:
        fname=request.form['fname']
        lname=request.form['lname']
        dob=request.form['dob']
        gender=request.form['gender']
        place=request.form['place']
        phone=request.form['phone']
        email=request.form['email']
        username=request.form['username']
        photo=request.files['photos']
        path="static/image/"+str(uuid.uuid4())+photo.filename
        photo.save(path)
        q1="UPDATE `user` SET f_name='%s',l_name='%s' ,username='%s',dob='%s',gender='%s',place='%s' , photo='%s' , phone='%s',email='%s' WHERE user_id='%s'"%(fname, lname  , username , dob ,gender,place, path , phone , email , user_id)
        update(q1)
        q3="UPDATE `login` SET username='%s' WHERE login_id='%s'"%(username , login_id)
        update(q3)
        return "<script>alert('Profile updated');window.location='/view_profile';</script>"
        
    if "subm" in request.form:
        password=request.form['password']
        q5="UPDATE `login` SET password='%s' WHERE login_id='%s'"%(password,login_id)
        update(q5)
        
        return "<script>alert('password updated');window.location='/view_profile';</script>"
    return render_template("user/update_profile.html",data=data)


# @user.route("/user_view_users")
# def view_users():
#     data={}
#     q2="select * from user where user_id !='%s'"%(str(session['user_id']))
#     data=select(q2)
#     return render_template("user/view_user.html",data=data)


@user.route("/user_view_users")
def view_users():
    user_id = session['user_id']
    
    # Fetch users that are not already friends with the logged-in user
    q = """
    SELECT *
    FROM user
    WHERE user.user_id != %s AND user.user_id NOT IN (
        SELECT
            CASE
                WHEN from_id = %s THEN to_id
                ELSE from_id
            END AS friend_id
        FROM request
        WHERE (from_id = %s OR to_id = %s) AND r_status = 'friends'
    )
    """ % (user_id, user_id, user_id, user_id)

    data = select(q)
    return render_template("user/view_user.html", data=data)



@user.route("/user_add_friend_request")
def add_friend_request():
    user_id=session['user_id']
    friend_id=request.args.get('id')
    session["fid"]=friend_id
    q2="select * from request where (from_id='%s' and to_id='%s')"%(user_id,friend_id)
    data=select(q2)
    if data:
         return "<script>alert('request already sent');window.location='/user_view_users';</script>"
    else:
        q1="insert into request values(NULL,'%s','%s', now() ,'%s')"%(user_id,friend_id,"pending")
        insert(q1)
        return "<script>alert('request sent');window.location='/user_view_users';</script>"
    
@user.route("/view_friend_requested_by_me")
def view_friend_requested_by_me():
    user_id=session['user_id']
    data={}
    q1="select * from request inner join user on request.to_id=user.user_id where request.from_id='%s'"%(user_id)
    # q1="SELECT request.*,user.* FROM `request` INNER JOIN `user` ON `request`.`to_id`=`user`.`user_id` WHERE request.from_id !='%s'"%(user_id)
    data=select(q1)
    return render_template("user/view_friend_requested_by_me.html",data=data)


@user.route("/cancel_request")
def cancel_request():
    rid=request.args.get("id")
    q1="delete from `request` WHERE request_id='%s'"%(rid)
    delete(q1)
    return "<script>alert(' request cancelled');window.location='/view_friend_requested_by_me';</script>"
   
   
@user.route("/view_friend_request")
def view_friend_request():
    user_id=session['user_id']
    dataa={}
    q2="select * from request inner join user on request.from_id=user.user_id where request.to_id='%s'"%(user_id)
    dataa=select(q2)
    return render_template("user/view_friend_request.html" , dataa=dataa)

@user.route("/accept_request")
def accept_request():
    request_id=request.args.get("id")
    q1="UPDATE `request` SET r_status='friends' WHERE request_id='%s'"%(request_id)
    update(q1)
    return "<script>alert('request accepted successfully');window.location='/view_friend_request';</script>"

@user.route("/reject_request")
def reject_request():
    rid=request.args.get("id")
    q1="UPDATE `request` SET r_status='reject' WHERE request_id='%s'"%(rid)
    update(q1)
    return "<script>alert('friend request rejected');window.location='/view_friend_request';</script>"


a');window.location='/view_post_of_friends';</script>"
    
    return render_template("user/sent_comment_for_the_post.html" , data=data)


# @user.route("/view_comments_and_sent_reply",methods=['get','post'])
# def view_comments_and_sent_reply():
#     post_id=request.args['post_id']
#     session['postt_id']=post_id
#     p_id=session['postt_id']
#     user_id=session['user_id']
#     data={}
#     q="select * from comment where post_id='%s'"%(post_id)
#     data['comments']=select(q)
#     if 'submit' in request.form:
#         reply=request.form['reply']
#         q2 =" update comment set reply='%s' , reply_date=curdate() where post_id='%s'"%(reply , post_id)
#         update(q2)
#         return f"<script>alert('Reply sent');window.location='/view_comments_and_sent_reply?post_id={post_id}';</script>"

        
#     return render_template("user/view_comments_and_sent_reply.html",data=data)


@user.route("/view_comments_and_sent_reply", methods=['get', 'post'])
def view_comments_and_sent_reply():
    post_id = request.args['post_id']
    session['postt_id'] = post_id
    user_id = session['user_id']
    data = {}
    
    
    q = "SELECT * FROM comment WHERE post_id='%s'" % (post_id)
    data['comments'] = select(q)
    
    if 'submit' in request.form:
        reply = request.form['reply']
        comment_id = request.form['comment_id']  
        
        
        q2 = "UPDATE comment SET reply='%s', reply_date=CURDATE() WHERE comment_id='%s'" % (reply, comment_id)
        update(q2)
        
        return f"<script>alert('Reply sent');window.location='/view_comments_and_sent_reply?post_id={post_id}';</script>"
    
    return render_template("user/view_comments_and_sent_reply.html", data=data)


@user.route("/message",methods=['get','post'])
def message():
    user_id=session['user_id']
    q1="""SELECT * 
    FROM request 
    INNER JOIN user 
    ON (request.from_id = user.user_id OR request.to_id = user.user_id) 
    AND request.r_status = 'friends' 
    WHERE (request.from_id = %s OR request.to_id = %s) 
    AND user.user_id != %s
    """ % (user_id, user_id, user_id)
    data=select(q1)
    return render_template("user/messages.html" , data=data)

@user.route('/user_chat',methods=['get','post'])
def user_chat():
    to_id = request.args['id']
    print("/////////////////////////////", to_id)
    uid = session['user_id']
    print('eewerwerwe', uid)

    s = "SELECT * FROM user WHERE user_id='%s'" % (to_id)
    data = select(s)
    s1 = "SELECT * FROM chat WHERE (from_id='%s' AND to_id='%s') OR (from_id='%s' AND to_id='%s') ORDER BY chat_id ASC" % (uid, to_id, to_id, uid)
    data1 = select(s1)
    
    if 'submit' in request.form:
        message = request.form['message']
        if message:
            print(f"Message: {message}")  # Print to debug if the message is captured
        else:
            print("No message entered")  # If message is empty

        
        # Split the message into words and check length
        
        
        if message not in bullys:  # Assume `mylist` is a predefined list of predefined messages
            q1 = "INSERT INTO chat VALUES(null, '%s', '%s', '%s', CURDATE(), 'Normal')" % (uid, to_id, message)
            insert(q1)
        else:
            # Predict whether the message is bullying
            d = predict_bully(message)
            if d == "normal":
                # Insert normal message
                q = "INSERT INTO chat VALUES(null, '%s', '%s', '%s', CURDATE(), 'Normal')" % (uid, to_id, message)
                insert(q)
            else:
                # Insert bullying message and update the user's bullying count
                q = "INSERT INTO chat VALUES(null, '%s', '%s', '%s', CURDATE(), 'Bully')" % (uid, to_id, message)
                insert(q)
                
                q2 = "UPDATE `user` SET `bullying_count` = `bullying_count` + 1 WHERE `user_id` = '%s'" % (uid)
                update(q2)
                
                # Return an alert that the message is bullying
                return f"<script>alert('You have sent a bullying message. Please be respectful!'); window.location='/user_chat?id={to_id}';</script>"
        
        # If the message is not bullying, proceed as usual
        return f"<script>alert('Message sent'); window.location='/user_chat?id={to_id}';</script>"
    
    return render_template("user/user_chat.html", data=data, data1=data1)




@user.route("/complaint",methods=['get','post'])
def complaint():
    user_id= session['user_id']
    data={}
    q1="select * from complaint where user_id='%s'"%(user_id)
    data=select(q1)
    print(data)
    
    if 'submit' in request.form:
        complaints=request.form['complaint']
        q1="insert into complaint values(NULL,'%s',curdate(),'%s','pending', 'pending')"%(user_id,complaints )
        insert(q1)
        return "<script>alert('complaint sent');window.location='/complaint';</script>"

    return render_template("user/complaint.html",data=data)

@user.route('/deactivate', methods=['GET','POST'])
def deactivate():

    id=request.args['id']
    q="delete from user where login_id='%s'"%(id)
    delete(q)
    q1="delete from login where login_id='%s'"%(id)
    delete(q1)
    return """<script>alert('Account Deactivated succcesfully');window.location='/login'</script>"""




#template styling portion-------------------------------------------------------------------------->


@user.route('/user_header')
def user_header():
    
    login_id=session['login_id']
    datas={} 
    q1="select * from user inner join login on user.login_id = login.login_id where user.login_id='%s'"%(login_id)
    datas=select(q1)
    
    return render_template("user/user_header.html" , datas=datas)


def predict_bully(id):
    msg=id
    from sklearn.model_selection import train_test_split

    path1 = "C:\\Users\\User\\Desktop\\cybercrime\\static\\cyberbullying-bdlstm.h5"
    path2 = "C:\\Users\\User\\Desktop\\cybercrime\\static\\tokenizer.json"

    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import json

    import tensorflow as tf
    from tensorflow.keras.preprocessing.text import Tokenizer
    from tensorflow.keras.preprocessing.sequence import pad_sequences
    from tensorflow.keras.callbacks import EarlyStopping
    from tensorflow.keras.layers import Activation
    def swish(x):
        return x * tf.sigmoid(x)
    # Define Swish activation function layer
    activation = Activation(swish)

    # Use Swish activation function in your model


    model = tf.keras.Sequential([
        tf.keras.layers.Embedding(2000, 64),  # embedding layer
        tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(64, dropout=0.2, recurrent_dropout=0.2)),  # LSTM layer
        tf.keras.layers.Dropout(rate=0.2),  # dropout layer
        tf.keras.layers.Dense(64, activation=activation),  # fully connected layer
        tf.keras.layers.Dense(1, activation='sigmoid')  # final layer
    ])

    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy', 'AUC'])
    model.load_weights(path1)

    import functools, re
    import random

    df = pd.read_csv("C:\\Users\\User\\Desktop\\cybercrime\\static\\toxi.csv")
    df.cyberbullying_type.value_counts().plot.barh(xlim=(7800, 8000))

    stopwords = [i.lower() for i in nltk.corpus.stopwords.words('english') + [chr(i) for i in range(97, 123)]]
    x = df.tweet_text.apply(lambda text: re.sub("\s+", " ", ' '.join([i for i in re.sub("[^9A-Za-z ]", "",
                                                                                        re.sub("\\n", "",
                                                                                               re.sub("\s+", " ",
                                                                                                      re.sub(
                                                                                                          r'http\S+',
                                                                                                          '',
                                                                                                          text.lower())))).split(
        " ") if i not in stopwords]))).values.astype(str)

    y = df.cyberbullying_type != "not_cyberbullying"

    x_train, x_val, y_train, y_val = train_test_split(x, y, test_size=0.4)
    x_val, x_test, y_val, y_test = train_test_split(x_val, y_val, test_size=0.25)

    tokenizer = tf.keras.preprocessing.text.Tokenizer(num_words=2000, oov_token="<OOV>")
    tokenizer.fit_on_texts(x)
    word_index = tokenizer.word_index

    x_test = [msg]

    x_test = pad_sequences(tokenizer.texts_to_sequences(x_test), maxlen=100, padding='post', truncating='post')

    y_pred = model.predict(x_test).round().T[0]

    print(y_pred)

    if y_pred[0] == 0.0:
        b = "normal"
    else:
        b = "toxic"
    return b

bullys=["thendi" ]

mylist = ["a" , "ok", "ohkey"  , "vokey" , "aa","hi","hai","new one","me","feel it","independent","classy","chill vibes","mood","good","a","aa","hi","hai","new one","me","feel it","independent","classy","chill vibes","mood","good","vibe check","just breathe","be yourself","living life","stay positive","let it go","good energy","peaceful mind","enjoy the moment","self-love","embrace change","stay true","make it happen","dream big","find your path","limitless","carpe diem","unapologetic","create your reality","live your truth","go with the flow","inner peace","shine bright","be the change","focus on the good","everyday magic","take a chance","follow your heart","let love in","seize the day","gr8","g2g","bff","lol","omg","ttyl","btw","idk",
          "lmk","fyi","tbh","nvm","imho","sry","omw","hmu","night","nyts","n8","xoxo","smh","wbu",
          "l8r","b4","gr8t","thx","cu","asap","k","v","u","rn","bday","4ever","plz","w8",
          "cya","diy","fomo","lmao","brb","tmi","wyd","gtg","np","yolo","ppl","bbl","tgif",
          "hbd","bbl","fam","lit","vibe","squad","bae","shade","snatched","dope","extra",
          "cringe","on point","thirsty","slay","cheers","sips tea","basic","fire","troll",
          "smol","yasss","meme","bet","lit AF","salty","receipts","shipping","flex","real talk"
          ,"spill the beans","not today","hype","bruh","ghosting","stan","low-key","high-key","clout","shade","adulting","feels","roast","hustle","squad goals",
          "cray","thicc","bussin'","catch flights","glow up","peep","snag","spill","finesse","savage",
          "woke","vibes","yikes","litty","kicks","doe","bay","skrt","sippin'","dank","cheugy","buss",
          "noted","yolo","hangry","slay","vibe check","facepalm","k","lmfao","naw","nah","lolz","gimme",
          "sus","vroom","phew","meh","woot","aesthetic","squad","woes","sexy","ttys","tty","woah","troll",
          "FML","oh em gee","damn","sick","mad","vital","fo'sho","swole","jet lag","finesse","slow clap",
          "swole","jet lag","finesse","slow clap","af","banger","clutch","plug","sike","suss","fam","sauce",
          "lit fam","fr","finesse","dope","poppin'","throw shade","tea","waifu","lmao","smh","bop","babe",
          "lil","shook","dime","curve","ratchet","slay","straight fire","snack","lit","cray","goat","adulting","iconic","extra","bomb","bussin","clout","fit","shade","zaddy","ship","bootylicious","rager","spilling the tea","kween","thirst trap","wig snatched","getting lit","tea spill","on fleek","fetch","slaps","tbh","dead","shade","canceled","fomo","no cap","vibe out","sus","blocked","doll","score","turnt","bet","no worries","skrrt","get lit","hella","fam","lowkey","highkey","ab","bad","big mood","bomb","buss","clap back","dope","fire","for real","gassed","ghost","jank","lit","no filter","salty","savage","shook","spill","tea","vibe","woke","yeet"]

mylist += [
    "eda" , "njan", "sughano" , 
    "yeah", "hoii", "oii", "gud", "vohoo", "voo", "set", "gonna", "k", "brb",
    "lol", "tbh", "fyi", "nvm", "idk", "hmm", "meh", "yup", "nah", "omg",
    "sry", "thx", "lmk", "bff", "btw", "cya", "gtg", "hbd", "xoxo", "cool",
    "rad", "lit", "slay", "sick", "dope", "fire", "vibe", "chill", "vibes",
    "bday", "squad", "bae", "swole", "cray", "fomo", "yass", "bussin", "woah", "oops",
    "whoops", "phew", "xoxo", "lmao", "omw", "wbu", "asap", "holla", "holla", "okey",
    "finesse", "litty", "groovy", "snazzy", "wow", "hype", "yo", "holla", "dude", "bro",
    "pals", "hey", "wassup", "homie", "kool", "hugs", "sweet", "yay", "woo", "coolio",
    "buddy", "pal", "sup", "cuz", "fam", "v", "bruh", "squad", "on fleek", "yolo",
    "lit fam", "dope", "neat", "sick", "tight", "fly", "clutch", "slaps", "rad", "buzz",
    "whatevs", "goat", "salty", "extra", "lit", "savage", "k", "lil", "flex", "biggie",
    "spicy", "fresh", "cute", "gn", "smh", "facts", "vroom", "sips", "kicks", "goals",
    "swag", "shook", "bop", "gel", "slay", "banger", "woke", "turnt", "jazzed", "dreamy",
    "sunkissed", "vroom", "lazy", "feelz", "chillax", "nifty", "aesthetic", "doozy", "neato",
    "gamer", "hyped", "treat", "pumped", "thumbs up", "sweet", "lit", "kicks", "scoop",
    "spunk", "wowza", "dandy", "spark", "fizz", "giggles", "lovely", "poppin", "zesty",
    "peep", "hitch", "feels", "bubbly", "smooth", "spicy", "treat", "ace", "zap", "skip",
    "proud", "cheers", "puff", "clap", "flash", "snap", "tilt", "bump", "hint", "pout",
    "sneak", "fizz", "hug", "slouch", "skip", "crunch", "swirl", "nudge", "splash", "drip",
    "swoosh", "whiff", "twist", "wink", "nudge", "swank", "cheer", "jive", "kick", "loop",
    "sway", "yap", "fray", "gig", "sprint", "zap", "vibe", "flare", "glow", "flinch",
    "flare", "jolt", "wink", "flick", "sway", "peek", "plunge", "sizzle", "squint", "dunk",
    "hike", "hush", "pounce", "zop", "zest", "zip", "buzz", "fry", "splat", "crackle",
    "fuzz", "scoop", "skate", "flap", "fling", "bounce", "tweak", "dash", "splat", "sway",
    "skip", "boop", "dash", "snag", "swipe", "twirl", "shake", "fob", "swing", "crisp",
    "huff", "slink", "drift", "gush", "tweak", "sway", "fizz", "slip", "drum", "snipe",
    "hustle", "nuzzle", "poke", "whiff", "fluff", "gush", "stomp", "tug", "zoom", "bounce",
    "trip", "shimmer", "tune", "bounce", "skip", "flick", "wink", "sway", "glance", "flip",
    "tap", "nudge", "gleam", "grin", "swig", "swirl", "flutter", "dance", "bounce", "zip",
    "clink", "float", "pop", "swipe", "glide", "sway", "chime", "twist", "jolt", "cheer",
    "sizzle", "swig", "tumble", "twirl", "jog", "shimmer", "peek", "nudge", "slap", "boing",
    "snap", "drift", "whoosh", "shake", "fizz", "bounce", "zest", "grasp", "fizz", "twist",
    "dash", "swoosh", "glimmer", "fizz", "twitch", "bounce", "drift", "swoop", "tug", "sway",
    "skip", "twirl", "peep", "gawk", "scoot", "jive", "wiggle", "trot", "skedaddle", "vroom",
    "dash", "slink", "zoom", "zippy", "snicker", "breeze", "bop", "bark", "snap", "flash",
    "fluff", "glint", "dive", "flick", "smirk", "nod", "twist", "flip", "tweak", "nudge"
]

mylist += [
    "hey", "hi", "yo", "sup", "na", "woo", "aha", "holla", "coolio", "dude",
    "buddy", "mate", "chill", "hype", "babe", "heyyo", "bro", "sis", "gang",
    "squad", "vibe", "ohh", "huh", "whoa", "word", "sippin", "yep", "sure",
    "easy", "chill", "okay", "cool", "fine", "right", "totes", "totally", "truly",
    "honestly", "gorgeous", "awesome", "perfect", "super", "great", "rad", "neat",
    "fun", "peace", "let's go", "cheerio", "top-notch", "legit", "nope", "yohoo",
    "kewl", "bruh", "sweat", "fam", "pals", "homey", "friend", "crew", "team",
    "vay", "zest", "zippy", "fluffy", "light", "fuzzy", "heyo", "whoopsie", "snap",
    "bingo", "yow", "yippie", "glad", "whew", "freshy", "splendid", "zappy", "saucy",
    "lit", "gnarly", "splashy", "awesome", "wicked", "boss", "stoked", "yeah buddy",
    "mellow", "zing", "whoosh", "jive", "wiggle", "tap", "bounce", "sway", "hitch",
    "cackle", "sneak", "skip", "dash", "zoom", "swish", "plunge", "flip", "kick",
    "hop", "roll", "flop", "trickle", "peek", "whirl", "swoosh", "bounce", "sprinkle",
    "shimmer", "glisten", "twinkle", "wink", "pop", "clap", "crash", "bang", "smash",
    "snag", "zap", "crush", "peep", "splash", "fizz", "twitch", "giggle", "nudge",
    "plop", "huddle", "snuggle", "bounce", "swoop", "jolt", "spin", "wave", "dart",
    "prance", "bop", "whip", "flip", "twist", "squish", "glide", "float", "zip",
    "tumble", "twitch", "stir", "drift", "zoo", "crinkle", "gush", "flare", "greet",
    "frolic", "sniff", "jiggle", "rattle", "skitter", "shuffle", "shimmer", "froth",
    "guzzle", "sip", "popcorn", "munch", "slurp", "yum", "nibble", "chomp", "chow",
    "crunch", "swig", "dip", "dunk", "quench", "slosh", "mingle", "savor", "treat",
    "dash", "swing", "fiddle", "twitch", "scoot", "bounce", "buzz", "vroom", "swoosh",
    "gawp", "yippee", "jolt", "bounce", "whack", "doodle", "giggle", "snoop", "hustle",
    "vow", "crazy", "harmony", "giddy", "bubble", "quiver", "chatter", "grin", "guffaw",
    "pounce", "snoop", "groan", "greet", "roam", "soar", "drizzle", "sneeze", "bounce",
    "whisk", "bustle", "skim", "flicker", "tumble", "hug", "swaddle", "glimmer", "whiff"
]

mylist += [
    "yep", "nah", "sure", "cool", "gotcha", "nice", "yo", "wanna", "chill",
    "vibe", "hey", "dude", "bro", "sis", "babe", "buddy", "pal", "homie",
    "tight", "lit", "fire", "sweet", "sick", "dope", "rad", "neat", "fresh",
    "whassup", "bingo", "cheers", "goodies", "kudos", "score", "bravo", "props",
    "woohoo", "huzzah", "yeah", "nope", "whoa", "yow", "eek", "oops", "yay",
    "bump", "bang", "zing", "bop", "snap", "nifty", "dazzle", "groovy", "vroom",
    "swag", "flex", "chillax", "okey", "gnarly", "holla", "let's", "roll", "squad",
    "fluffy", "slay", "smash", "crush", "pop", "dance", "bounce", "chill", "skate",
    "scoop", "swirl", "swoop", "bask", "prance", "bop", "jam", "nudge", "wink",
    "spark", "buzz", "whirl", "soar", "doodle", "dazzle", "giddy", "flutter", 
    "sparkle", "sizzle", "twee", "chit-chat", "splash", "whisk", "fling", "whip",
    "fizz", "swoosh", "zoom", "swish", "popcorn", "drizzle", "flutter", "tickle",
    "sneak", "snoop", "buzz", "hustle", "sizzle", "swoosh", "bounce", "drift",
    "zoom", "scoop", "twist", "whiff", "crackle", "snag", "gush", "plunge",
    "gawk", "grin", "cackle", "scoop", "swoon", "gasp", "hum", "chirp", "chirp",
    "snooze", "dare", "swing", "dash", "breeze", "float", "zoom", "glide",
    "wiggle", "jive", "shake", "swirl", "bliss", "serene", "gleam", "spark",
    "slap", "tap", "buzz", "slip", "wiggle", "smirk", "grin", "mingle", "flair",
    "delight", "bubbly", "spark", "chime", "glee", "joy", "zest", "zeal",
    "cheer", "chuckle", "exhale", "breathe", "flow", "sway", "whisper", "gleeful",
    "sketch", "paddle", "flick", "smile", "shine", "glow", "frolic", "exult",
    "glimmer", "echo", "jubilant", "zany", "fizz", "bop", "mellow", "nifty",
    "goofy", "zippy", "chipper", "kooky", "bouncy", "perky", "sprightly", "uplift",
    "revive", "nuzzle", "snuggle", "hug", "sway", "flip", "tumble", "chime"
]


mylist += [
    "hello", "goodbye", "please", "thank you", "sorry", "excuse me", "yes", "no",
    "maybe", "sure", "of course", "absolutely", "definitely", "really", "kind of",
    "a little", "totally", "awesome", "cool", "fine", "okay", "alright", "no worries",
    "take care", "what's up", "how are you", "what's going on", "catch you later",
    "talk to you soon", "see you", "have a nice day", "you got this", "hang in there",
    "keep it up", "stay strong", "good luck", "go for it", "just do it", "cheers",
    "best wishes", "hugs", "kisses", "love you", "miss you", "I appreciate you",
    "you're amazing", "you're the best", "so proud of you", "way to go", "you rock",
    "you're right", "my bad", "no biggie", "it's all good", "you know what I mean",
    "know what I'm saying", "fair enough", "let's go", "let's do this", "bring it on",
    "count me in", "I'm in", "let's roll", "let's get started", "let's make it happen",
    "what do you think", "your call", "whatever you say", "if you say so", "that's cool",
    "that sounds good", "sounds like a plan", "I see what you mean", "gotcha", "understood",
    "makes sense", "that's fair", "that's true", "I agree", "I hear you", "I'm with you",
    "that works for me", "totally agree", "sure thing", "I get it", "you've got a point",
    "good to know", "noted", "point taken", "I'll take that into account", "I respect that",
    "let's agree to disagree", "it's okay to disagree", "I understand your perspective",
    "appreciate your input", "thanks for sharing", "you've made your point", "I'll keep that in mind",
    "that's interesting", "tell me more", "I'd like to hear more about that", "I'm curious",
    "I'm interested", "that's a good question", "what's your take", "how do you feel about that",
    "what's your opinion", "let's discuss", "we should talk about this", "can we chat",
    "let's catch up", "I want to hear your thoughts", "what do you want to do", "where do you want to go",
    "let's figure it out", "we can work it out", "let's find a solution", "let's brainstorm",
    "I'm open to suggestions", "let's collaborate", "let's team up", "let's partner", "let's unite",
    "let's join forces", "let's work together", "let's combine our efforts", "let's share ideas",
    "I value your opinion", "your feedback is important", "your thoughts matter", "I appreciate your thoughts",
    "I value your perspective", "I like your style", "you're so creative", "you think outside the box",
    "you have great ideas", "you're innovative", "you're inspiring", "you have a way with words",
    "you express yourself well", "you're articulate", "you have a talent for communication",
    "I admire your confidence", "you're a great listener", "you're very thoughtful", "you're empathetic",
    "you're compassionate", "you're understanding", "you have a good heart", "you care about others",
    "you make a difference", "you bring out the best in people", "you uplift those around you",
    "you inspire positivity", "you're a ray of sunshine", "you're a breath of fresh air", "you brighten my day",
    "you bring joy to my life", "you have a positive impact", "you make the world a better place",
    "you're a blessing", "you're a gift", "you're unique", "you're one of a kind", "you're special",
    "you stand out", "you're different in a good way", "you're exceptional", "you're remarkable",
    "you're phenomenal", "you're fantastic", "you're terrific", "you're outstanding", "you're impressive",
    "you're admirable", "you're excellent", "you're top-notch", "you're extraordinary", "you're fabulous",
    "you're lovely", "you're delightful", "you're charming", "you're sweet", "you're kind",
    "you're generous", "you're helpful", "you're supportive", "you're encouraging", "you're motivating",
    "you're inspiring", "you're uplifting", "you're reassuring", "you're calming", "you're soothing",
    "you're peaceful", "you're tranquil", "you're grounded", "you're centered", "you're balanced",
    "you're stable", "you're reliable", "you're dependable", "you're trustworthy", "you're honest",
    "you're straightforward", "you're genuine", "you're authentic", "you're sincere", "you're true to yourself",
    "you're real", "you're down to earth", "you're humble", "you're modest", "you're grounded",
    "you're relatable", "you're approachable", "you're friendly", "you're sociable", "you're fun to be around",
    "you're entertaining", "you're engaging", "you're charismatic", "you're magnetic", "you're captivating",
    "you're charming", "you're witty", "you're funny", "you're humorous", "you're light-hearted",
    "you're playful", "you're spontaneous", "you're adventurous", "you're curious", "you're open-minded",
    "you're flexible", "you're adaptable", "you're resilient", "you're courageous", "you're brave",
    "you're bold", "you're daring", "you're confident", "you're assertive", "you're ambitious",
    "you're driven", "you're determined", "you're focused", "you're goal-oriented", "you're disciplined",
    "you're committed", "you're dedicated", "you're passionate", "you're enthusiastic", "you're excited",
    "you're optimistic", "you're hopeful", "you're positive", "you're cheerful", "you're upbeat",
    "you're lively", "you're vibrant", "you're dynamic", "you're energetic", "you're full of life",
    "you're full of energy", "you're spirited", "you're fun-loving", "you're happy", "you're joyful",
    "you're content", "you're fulfilled", "you're satisfied", "you're at peace", "you're serene",
    "you're relaxed", "you're calm", "you're composed", "you're centered", "you're grounded",
    "you're balanced", "you're stable", "you're secure", "you're confident", "you're self-assured",
    "you're self-reliant", "you're self-sufficient", "you're independent", "you're capable", "you're skilled",
    "you're talented", "you're gifted", "you're smart", "you're intelligent", "you're knowledgeable",
    "you're wise", "you're insightful", "you're perceptive", "you're observant", "you're aware",
    "you're conscious", "you're mindful", "you're thoughtful", "you're considerate", "you're respectful",
    "you're polite", "you're courteous", "you're gracious", "you're civil", "you're kind-hearted",
    "you're gentle", "you're tender", "you're nurturing", "you're caring", "you're affectionate",
    "you're loving", "you're warm-hearted", "you're compassionate", "you're empathetic", "you're understanding",
    "you're sympathetic", "you're supportive", "you're encouraging", "you're helpful", "you're resourceful",
    "you're innovative", "you're inventive", "you're creative", "you're artistic", "you're imaginative",
    "you're original", "you're unique", "you're one of a kind", "you're special", "you're exceptional",
    "you're remarkable", "you're fantastic", "you're terrific", "you're fabulous", "you're wonderful",
    "you're great", "you're awesome", "you're amazing", "you're incredible", "you're unbelievable",
    "you're extraordinary", "you're phenomenal", "you're outstanding", "you're super", "you're marvelous",
    "you're glorious", "you're splendid", "you're brilliant", "you're shining", "you're luminous",
    "you're radiant", "you're bright", "you're sparkling", "you're dazzling", "you're vibrant",
    "you're colorful", "you're lively", "you're dynamic", "you're energetic", "you're full of life",
    "you're full of spirit", "you're spirited", "you're zealous", "you're enthusiastic", "you're passionate",
    "you're excited", "you're eager", "you're keen", "you're ambitious", "you're driven",
    "you're goal-oriented", "you're determined", "you're persistent", "you're patient", "you're resilient",
    "you're tough", "you're strong", "you're powerful", "you're confident", "you're brave",
    "you're fearless", "you're bold", "you're daring", "you're adventurous", "you're courageous",
    "you're audacious", "you're enterprising", "you're innovative", "you're creative", "you're resourceful",
    "you're clever", "you're quick-witted", "you're sharp", "you're bright", "you're intelligent",
    "you're smart", "you're wise", "you're knowledgeable", "you're informed", "you're insightful",
    "you're discerning", "you're perceptive", "you're observant", "you're aware", "you're mindful",
    "you're thoughtful", "you're considerate", "you're respectful", "you're polite", "you're gracious",
    "you're civil", "you're kind", "you're friendly", "you're sociable", "you're engaging", "you're charismatic",
    "you're charming", "you're appealing", "you're captivating", "you're magnetic", "you're alluring",
    "you're attractive", "you're beautiful", "you're stunning", "you're gorgeous", "you're lovely",
    "you're pretty", "you're handsome", "you're elegant", "you're classy", "you're stylish",
    "you're fashionable", "you're chic", "you're trendy", "you're in style", "you're modern",
    "you're sophisticated", "you're polished", "you're refined", "you're cultured", "you're worldly",
    "you're educated", "you're well-read", "you're cultured", "you're experienced", "you're seasoned",
    "you're accomplished", "you're successful", "you're thriving", "you're flourishing", "you're growing",
    "you're evolving", "you're progressing", "you're advancing", "you're improving", "you're developing",
    "you're learning", "you're mastering", "you're honing your skills", "you're sharpening your skills",
    "you're increasing your knowledge", "you're expanding your horizons", "you're broadening your perspective",
    "you're enhancing your skills", "you're cultivating your talents", "you're nurturing your abilities",
    "you're unleashing your potential", "you're maximizing your strengths", "you're utilizing your resources",
    "you're leveraging your skills", "you're capitalizing on your strengths", "you're building your brand",
    "you're establishing your presence", "you're making a mark", "you're leaving an impression",
    "you're standing out", "you're distinguishing yourself", "you're making waves", "you're shaking things up",
    "you're changing the game", "you're pushing boundaries", "you're breaking barriers", "you're defying expectations",
    "you're exceeding limits", "you're surpassing standards", "you're challenging norms", "you're rewriting the rules",
    "you're leading the way", "you're setting the standard", "you're paving the path", "you're trailblazing",
    "you're forging your own path", "you're carving your niche", "you're finding your voice", "you're speaking your truth",
    "you're expressing yourself", "you're sharing your story", "you're telling your narrative", "you're being heard",
    "you're making yourself known", "you're being recognized", "you're being acknowledged", "you're being appreciated",
    "you're being celebrated", "you're being honored", "you're being valued", "you're being cherished", "you're being loved",
    "you're being supported", "you're being uplifted", "you're being encouraged", "you're being motivated",
    "you're being inspired", "you're being empowered", "you're being transformed", "you're being changed",
    "you're being enriched", "you're being enhanced", "you're being elevated", "you're being lifted up",
    "you're being encouraged", "you're being fortified", "you're being strengthened", "you're being revitalized",
    "you're being rejuvenated", "you're being reinvigorated", "you're being renewed", "you're being refreshed",
    "you're being awakened", "you're being enlightened", "you're being illuminated", "you're being guided",
    "you're being directed", "you're being supported", "you're being backed", "you're being bolstered",
    "you're being held up", "you're being sustained", "you're being nurtured", "you're being fostered",
    "you're being developed", "you're being cultivated", "you're being grown", "you're being expanded",
    "you're being advanced", "you're being propelled", "you're being driven", "you're being thrust forward",
    "you're being launched", "you're being elevated", "you're being raised up", "you're being pushed up",
    "you're being elevated to new heights", "you're being taken to the next level", "you're being lifted to new standards",
    "you're being carried to new heights", "you're being supported to reach your potential", "you're being encouraged to shine",
    "you're being celebrated for your achievements", "you're being acknowledged for your contributions", "you're being valued for your input",
    "you're being recognized for your efforts", "you're being appreciated for your talents", "you're being honored for your hard work",
    "you're being respected for your integrity", "you're being admired for your strengths", "you're being cherished for your uniqueness",
    "you're being loved for who you are", "you're being valued for your worth", "you're being supported for your dreams",
    "you're being uplifted for your passions", "you're being encouraged to pursue your goals", "you're being inspired to chase your dreams",
    "you're being empowered to take action", "you're being transformed to become the best version of yourself",
    "you're being changed to live your truth", "you're being enriched to find your purpose", "you're being enhanced to make a difference",
    "you're being elevated to contribute positively", "you're being lifted up to be your authentic self", "you're being encouraged to thrive",
    "you're being supported to flourish", "you're being motivated to grow", "you're being inspired to evolve",
    "you're being empowered to create", "you're being transformed to lead", "you're being changed to inspire others",
    "you're being enriched to leave a legacy", "you're being enhanced to spread positivity", "you're being elevated to shine your light",
    "you're being lifted up to share your gifts", "you're being encouraged to give back", "you're being supported to help others",
    "you're being motivated to uplift those around you", "you're being inspired to lead by example", "you're being empowered to advocate for change",
    "you're being transformed to become a beacon of hope", "you're being changed to inspire greatness", "you're being enriched to empower others",
    "you're being enhanced to build a better world", "you're being elevated to be a change-maker", "you're being lifted up to create a brighter future",
    "you're being encouraged to chase your dreams", "you're being supported to make your mark", "you're being motivated to achieve your goals",
    "you're being inspired to live fully", "you're being empowered to take risks", "you're being transformed to embrace new opportunities",
    "you're being changed to explore new paths", "you're being enriched to discover new horizons", "you're being enhanced to overcome challenges",
    "you're being elevated to reach new heights", "you're being lifted up to see beyond limits", "you're being encouraged to take leaps of faith",
    "you're being supported to navigate through life", "you're being motivated to keep going", "you're being inspired to rise above",
    "you're being empowered to shine brightly", "you're being transformed to find your true self", "you're being changed to live authentically",
    "you're being enriched to cultivate your strengths", "you're being enhanced to nurture your passions", "you're being elevated to embrace your journey",
    "you're being lifted up to celebrate your progress", "you're being encouraged to honor your path", "you're being supported to reflect on your growth",
    "you're being motivated to appreciate the present", "you're being inspired to savor the journey", "you're being empowered to embrace change",
    "you're being transformed to be resilient", "you're being changed to take charge of your life", "you're being enriched to find joy in the little things",
    "you're being enhanced to practice gratitude", "you're being elevated to spread kindness", "you're being lifted up to create positive vibes",
    "you're being encouraged to foster connection", "you're being supported to build relationships", "you're being motivated to stay engaged",
    "you're being inspired to participate actively", "you're being empowered to advocate for yourself", "you're being transformed to express your truth",
    "you're being changed to seek understanding", "you're being enriched to cultivate compassion", "you're being enhanced to practice empathy",
    "you're being elevated to be a force for good", "you're being lifted up to empower your community", "you're being encouraged to connect with others",
    "you're being supported to share your story", "you're being motivated to stand up for what you believe", "you're being inspired to make your voice heard",
    "you're being empowered to champion causes that matter", "you're being transformed to create lasting change", "you're being changed to foster inclusivity",
    "you're being enriched to build bridges", "you're being enhanced to promote unity", "you're being elevated to embrace diversity",
    "you're being lifted up to celebrate differences", "you're being encouraged to spread love", "you're being supported to champion justice",
    "you're being motivated to create a welcoming space", "you're being inspired to uplift marginalized voices", "you're being empowered to advocate for equality",
    "you're being transformed to create a sense of belonging", "you're being changed to nurture acceptance", "you're being enriched to promote understanding",
    "you're being enhanced to celebrate humanity", "you're being elevated to appreciate every voice", "you're being lifted up to encourage collaboration",
    "you're being encouraged to work together for a common goal", "you're being supported to foster teamwork", "you're being motivated to embrace synergy",
    "you're being inspired to innovate collectively", "you're being empowered to solve problems as a team", "you're being transformed to share responsibilities",
    "you're being changed to distribute opportunities fairly", "you're being enriched to build a supportive environment", "you're being enhanced to cultivate trust",
    "you're being elevated to inspire confidence", "you're being lifted up to nurture creativity", "you're being encouraged to explore new ideas",
    "you're being supported to think outside the box", "you're being motivated to push boundaries", "you're being inspired to dream big together",
    "you're being empowered to create impact", "you're being transformed to envision a brighter future", "you're being changed to work towards shared goals",
    "you're being enriched to cultivate mutual respect", "you're being enhanced to foster collaboration", "you're being elevated to amplify voices",
    "you're being lifted up to build community", "you're being encouraged to connect meaningfully", "you're being supported to share experiences",
    "you're being motivated to uplift spirits", "you're being inspired to celebrate milestones", "you're being empowered to encourage growth",
    "you're being transformed to recognize achievements", "you're being changed to honor progress", "you're being enriched to appreciate every effort",
    "you're being enhanced to express gratitude", "you're being elevated to be a source of inspiration", "you're being lifted up to encourage celebration",
    "you're being encouraged to cherish relationships", "you're being supported to strengthen bonds", "you're being motivated to create lasting memories",
    "you're being inspired to cultivate joy", "you're being empowered to spread positivity", "you're being transformed to embrace hope",
    "you're being changed to foster resilience", "you're being enriched to celebrate every step", "you're being enhanced to encourage persistence",
    "you're being elevated to inspire perseverance", "you're being lifted up to promote self-love", "you're being encouraged to practice self-care",
    "you're being supported to prioritize well-being", "you're being motivated to nurture mental health", "you're being inspired to seek balance",
    "you're being empowered to create healthy habits", "you're being transformed to live mindfully", "you're being changed to cultivate awareness",
    "you're being enriched to appreciate stillness", "you're being enhanced to enjoy the moment", "you're being elevated to embrace serenity",
    "you're being lifted up to find peace within", "you're being encouraged to practice mindfulness", "you're being supported to foster well-being",
    "you're being motivated to live in the present", "you're being inspired to savor life", "you're being empowered to enjoy simplicity",
    "you're being transformed to cultivate joy in everyday moments", "you're being changed to find beauty in the ordinary", "you're being enriched to appreciate nature",
    "you're being enhanced to embrace the outdoors", "you're being elevated to connect with the world", "you're being lifted up to explore new places",
    "you're being encouraged to travel mindfully", "you're being supported to seek adventure", "you're being motivated to discover new cultures",
    "you're being inspired to learn from experiences", "you're being empowered to expand your horizons", "you're being transformed to embrace new perspectives",
    "you're being changed to foster curiosity", "you're being enriched to appreciate different viewpoints", "you're being enhanced to seek wisdom",
    "you're being elevated to engage in lifelong learning", "you're being lifted up to challenge assumptions", "you're being encouraged to explore possibilities",
    "you're being supported to embrace change", "you're being motivated to adapt", "you're being inspired to grow through experiences",
    "you're being empowered to overcome obstacles", "you're being transformed to rise above challenges", "you're being changed to cultivate a growth mindset",
    "you're being enriched to embrace opportunities for improvement", "you're being enhanced to celebrate learning journeys", "you're being elevated to make meaningful connections",
    "you're being lifted up to inspire others through your journey", "you're being encouraged to share lessons learned", "you're being supported to reflect on experiences",
    "you're being motivated to embrace change as a friend", "you're being inspired to celebrate personal growth", "you're being empowered to take pride in your journey",
    "you're being transformed to inspire others to embrace their paths", "you're being changed to cultivate a sense of belonging in every space",
    "you're being enriched to foster community spirit", "you're being enhanced to create welcoming environments", "you're being elevated to celebrate unity",
    "you're being lifted up to honor diversity", "you're being encouraged to promote inclusivity", "you're being supported to share your gifts",
    "you're being motivated to empower others to share theirs", "you're being inspired to build a legacy of kindness", "you're being empowered to lead with love",
    "you're being transformed to inspire future generations", "you're being changed to create ripples of positive change", "you're being enriched to spread hope",
    "you're being enhanced to celebrate each day", "you're being elevated to appreciate life's gifts", "you're being lifted up to make every moment count",
    "you're being encouraged to love yourself", "you're being supported to be your true self", "you're being motivated to shine your light brightly",
    "you're being inspired to illuminate the path for others", "you're being empowered to share your light", "you're being transformed to be a source of positivity",
    "you're being changed to inspire joy", "you're being enriched to uplift hearts", "you're being enhanced to create harmony",
    "you're being elevated to promote love", "you're being lifted up to be a catalyst for change", "you're being encouraged to embrace your uniqueness",
    "you're being supported to stand tall in your truth", "you're being motivated to be a beacon of hope", "you're being inspired to be a voice for the voiceless",
    "you're being empowered to champion those in need", "you're being transformed to inspire compassion", "you're being changed to be a light in the world",
    "you're being enriched to celebrate each day as a gift", "you're being enhanced to embrace the beauty around you", "you're being elevated to make a positive impact",
    "you're being lifted up to encourage kindness", "you're being encouraged to live your truth", "you're being supported to uplift those in need",
    "you're being motivated to create safe spaces", "you're being inspired to foster understanding", "you're being empowered to be a force for good",
    "you're being transformed to inspire change", "you're being changed to spread love and acceptance", "you're being enriched to uplift every soul",
    "you're being enhanced to be a beacon of hope", "you're being elevated to inspire greatness in others", "you're being lifted up to empower every voice",
    "you're being encouraged to celebrate every victory", "you're being supported to honor every step forward", "you're being motivated to cherish every moment",
    "you're being inspired to cultivate gratitude in your heart", "you're being empowered to spread positivity like confetti", "you're being transformed to light up the world",
    "you're being changed to inspire love and joy", "you're being enriched to be a source of inspiration for others", "you're being enhanced to share your unique gifts",
    "you're being elevated to appreciate the beauty of humanity", "you're being lifted up to embrace every challenge", "you're being encouraged to make a difference",
    "you're being supported to follow your dreams", "you're being motivated to leave a legacy of love", "you're being inspired to shine your light brightly",
    "you're being empowered to create ripples of kindness", "you're being transformed to inspire others to do the same", "you're being changed to embrace your true essence",
    "you're being enriched to find beauty in every experience", "you're being enhanced to cultivate a loving heart", "you're being elevated to celebrate life fully",
    "you're being lifted up to appreciate every sunrise", "you're being encouraged to spread joy wherever you go", "you're being supported to cultivate a mindset of gratitude",
    "you're being motivated to share your light", "you're being inspired to be a beacon of hope for those around you", "you're being empowered to embrace your journey with love",
    "you're being transformed to uplift the world with your spirit", "you're being changed to inspire others to shine their light", "you're being enriched to spread hope",
    "you're being enhanced to create a culture of love", "you're being elevated to nurture a community of kindness", "you're being lifted up to be a source of light",
    "you're being encouraged to inspire joy in others", "you're being supported to foster connection", "you're being motivated to make every moment matter",
    "you're being inspired to cherish relationships", "you're being empowered to celebrate every unique story", "you're being transformed to uplift each other",
    "you're being changed to appreciate the beauty in diversity", "you're being enriched to celebrate every moment of life", "you're being enhanced to spread joy",
    "you're being elevated to cultivate compassion", "you're being lifted up to inspire others with your journey", "you're being encouraged to shine your light brightly",
    "you're being supported to spread positivity in every corner of your life", "you're being motivated to make every day a celebration",
    "you're being inspired to lift each other up", "you're being empowered to lead with love", "you're being transformed to create a legacy of kindness",
    "you're being changed to be a voice for the voiceless", "you're being enriched to celebrate every person", "you're being enhanced to create a world filled with love",
    "you're being elevated to foster acceptance", "you're being lifted up to be a source of encouragement", "you're being encouraged to embrace your differences",
    "you're being supported to promote inclusivity", "you're being motivated to celebrate the beauty of humanity", "you're being inspired to uplift others",
    "you're being empowered to create ripples of change", "you're being transformed to inspire future generations", "you're being changed to cherish every relationship",
    "you're being enriched to celebrate your uniqueness", "you're being enhanced to promote understanding and compassion", "you're being elevated to uplift spirits",
    "you're being lifted up to create a better world", "you're being encouraged to share your gifts with the world", "you're being supported to cultivate connections",
    "you're being motivated to empower others", "you're being inspired to build a community of love", "you're being empowered to shine your light",
    "you're being transformed to uplift every heart", "you're being changed to inspire a culture of kindness", "you're being enriched to spread positivity",
    "you're being enhanced to embrace every moment of joy", "you're being elevated to celebrate the gift of life", "you're being lifted up to create a legacy of love",
    "you're being encouraged to share your journey with others", "you're being supported to celebrate every small victory", "you're being motivated to be a catalyst for change",
    "you're being inspired to uplift those around you", "you're being empowered to make every moment count", "you're being transformed to spread love",
    "you're being changed to celebrate every heartbeat", "you're being enriched to embrace your story", "you're being enhanced to inspire others",
    "you're being elevated to spread joy like wildfire", "you're being lifted up to create a world filled with laughter", "you're being encourag"]


mylist += [
    "dee",
    "daa",
    "okay",              # Okay
    "babe",              # Term of endearment
    "nah",               # No
    "yolo",              # You only live once
    "lmk",               # Let me know
    "fomo",              # Fear of missing out
    "bet",               # Agreement
    "tbh",               # To be honest
    "lol",               # Laugh out loud
    "brb",               # Be right back
    "gtg",               # Got to go
    "idk",               # I don't know
    "smh",               # Shaking my head
    "ttyl",              # Talk to you later
    "omg",               # Oh my god
    "wtf",               # What the f***
    "rofl",              # Rolling on the floor laughing
    "bff",               # Best friends forever
    "imo",               # In my opinion
    "jk",                # Just kidding
    "lmao",              # Laughing my ass off
    "bc",                # Because
    "gr8",               # Great
    "l8r",               # Later
    "plz",               # Please
    "cya",               # See you
    "xoxo",              # Hugs and kisses
    "xoxo",              # Hugs and kisses
    "thx",               # Thanks
    "fyi",               # For your information
    "ty",                # Thank you
    "np",                # No problem
    "fam",               # Family or close friends
    "gr8t",              # Great
    "ur",                # Your
    "u",                 # You
    "ppl",               # People
    "cuz",               # Because
    "wbu",               # What about you?
    "g2g",               # Got to go
    "mfw",               # My face when
    "dm",                # Direct message
    "bbl",               # Be back later
    "lmk",               # Let me know
    "btw",               # By the way
    "srsly",            # Seriously
    "whatevs",           # Whatever
    "omw",               # On my way
    "diy",               # Do it yourself
    "s/o",               # Shout out
    "hmu",               # Hit me up
    "tbh",               # To be honest
    "wyd",               # What are you doing?
    "wsup",              # What's up?
    "idc",               # I don't care
    "fomo",              # Fear of missing out
    "nvm",               # Never mind
    "gtg",               # Got to go
    "k",                 # Okay
    "bih",               # Babe or another term for someone attractive
    "kewl",              # Cool
    "yass",              # Yes, with excitement
    "hype",              # Excitement or buzz
    "savage",            # Bold or fierce
    "dope",              # Cool or awesome
    "lit",               # Exciting or fun
    "sick",              # Awesome or impressive
    "slay",              # To do something exceptionally well
    "banger",            # A great song
    "finesse",           # Skillfully handling a situation
    "vibe",              # Atmosphere or feeling
    "flex",              # To show off
    "sus",               # Suspicious
    "slaps",             # Really good (especially for music)
    "woke",              # Socially aware
    "ratchet",           # Wild or out of control
    "no cap",            # No lie
    "finna",             # Fixing to, planning to
    "shade",             # Subtle criticism
    "bussin",            # Delicious
    "litty",             # Really fun or exciting
    "on point",          # Exactly right
    "deadass",           # Seriously or truthfully
    "big yikes",         # An exaggerated reaction to an embarrassing situation
    "cringe",            # Awkward or embarrassing
    "big mood",          # A strong feeling
    "vibe check",        # Assessing the atmosphere
    "doe",               # Though or however
    "sus",               # Suspicious
    "drip",              # Stylish or fashionable
    "tea",               # Gossip
    "curve",             # To reject someone
    "buss",              # Very good
    "ratchet",           # Wild or crazy
    "salty",             # Upset or bitter
    "shade",             # Insult or criticism
    "shook",             # Shocked or surprised
    "yeet",              # To throw or express excitement
    "cray",              # Crazy
    "facts",             # Truth
    "good vibes",        # Positive feelings
    "slay queen",        # A powerful woman
    "lit fam",           # Fun family or friends
    "adulting",          # Taking on adult responsibilities
    "squad",             # Group of friends
    "wavy",              # Cool or stylish
    "clutch",            # A last-minute success
    "yolo",              # You only live once
    "whip",              # Car
    "suss",              # Suspicious
    "iconic",            # Widely recognized
    "turnt",             # Intoxicated or excited
    "cray cray",         # Really crazy
    "babe",              # Term of endearment
    "lowkey",            # Quietly or subtly
    "highkey",           # Very obvious
    "big brain",         # Smart or clever
    "slay",              # To succeed
    "rager",             # A wild party
    "sippin' tea",       # Enjoying gossip
    "mojo",              # Charm or appeal
    "dope",              # Awesome
    "lit",               # Exciting or fun
    "swole",             # Muscular
    "lowkey",            # Subtle
    "savage",            # Ruthless
    "dope",              # Excellent
    "fire",              # Really good
    "flex",              # Show off
    "big yikes",         # An exaggerated reaction to something embarrassing
    "spill the tea",     # Share gossip
    "bet",               # Agreement
    "trippin'",          # Overreacting
    "bro",               # Male friend
    "sis",               # Female friend
    "gassed",            # Excited
    "fire",              # Amazing
    "snatch",            # To take something quickly
    "swoop",             # To pick up or arrive
    "vibe out",          # To relax and enjoy
    "wildin'",           # Acting crazy
    "bestie",            # Best friend
    "neat",              # Good or okay
    "sus",               # Suspicious
    "buzzkill",          # Someone who dampens the mood
    "creeper",           # Someone who acts inappropriately
    "shade",             # Insult or slight
    "bumpin'",           # Good music
    "chill",             # Relaxed
    "keep it real",      # Be honest
    "fall back",         # To retreat or take a step back
    "on fleek",          # Perfectly done
    "caught feelings",    # Developed romantic feelings
    "salty",             # Bitter or upset
    "extra",             # Over the top
    "vibe",              # Mood or feeling
    "boomerang",         # A video that plays forward and then in reverse
    "throwback",         # A nostalgic post
    "hangry",            # Hungry and angry
    "jiggy",             # Having fun or dancing
    "kicks",             # Sneakers
    "meme",              # Humorous content shared online
    "ghost",             # To cut off communication suddenly
    "fry",               # To roast or tease
    "squad goals",       # Aspirational friendship
    "steez",             # Style with ease
    "sick",              # Cool or impressive
    "finesse",           # Skillful handling
    "get it",            # To understand or agree
    "lit",               # Exciting
    "lituation",         # A great situation or party
    "dope",              # Cool or awesome
    "vibin'",            # Enjoying the moment
    "goals",             # Aspirations
    "hangout",           # A casual gathering
    "squad",             # A close group of friends
    "adulting",          # Taking on adult responsibilities
    "simp",              # Someone who is overly attentive to someone else
    "tea",               # Gossip
    "get lit",           # To party
    "shade",             # Subtle insult
    "receipts",          # Proof or evidence, often used in gossip
    "chill",             # Relaxed
    "low-key",           # Not obvious
    "high-key",          # Very obvious
    "wave",              # A trend
    "stan",              # An obsessed fan
    "clout",             # Influence or fame
    "fomo",              # Fear of missing out
    "cancelled",         # To dismiss someone or something
    "sip tea",           # Enjoy gossip
    "smol",              # Small or cute
    "extra",             # Over the top
    "wig",               # Used when something is so good it makes you feel like your wig is blown off
    "whip",              # Car
    "feels",             # Feelings or emotions
    "doe",               # Though
    "drama",             # Gossip or conflict
    "squad",             # Group of friends
    "sus",               # Suspicious
    "cap",               # Lie
    "no cap",            # No lie
    "simp",              # Someone who is overly attentive to someone else
    "spicy",             # Interesting or exciting
    "tea",               # Gossip
    "fire",              # Really good
    "bless up",          # To show gratitude
    "hype",              # Excitement
    "vibe check",        # Assessing the mood
    "hit different",     # Feeling an emotional connection
    "got the juice",     # Having charm or charisma
    "lowkey",            # Subtly
    "highkey",           # Very noticeable
    "cringe",            # Awkward
    "canceled",          # Dismissed or rejected
    "vibe",              # Mood
    "savage",            # Bold and fierce
    "wholesome",         # Pure or good-hearted
    "finesse",           # Skillfully handling a situation
    "cancel culture",    # The practice of canceling individuals
    "jaded",             # Tired or worn out
    "reset",             # Starting over
    "woke",              # Socially aware
    "unbothered",        # Not affected by drama
    "shade",             # Insult or slight
    "dime",              # Attractive person
    "fire",              # Amazing
    "vibes",             # Atmosphere
    "on point",          # Exactly right
    "salty",             # Upset
    "dope",              # Cool
    "whip",              # Car
    "drip",              # Style
    "go off",            # To speak passionately
    "tea",               # Gossip
    "turnt",             # Intoxicated or excited
    "stoked",            # Excited
    "hyped",             # Excited
    "sus",               # Suspicious
    "spill the tea",     # Share gossip
    "bet",               # Agreement
    "jams",              # Good music
    "spicy",             # Interesting
    "lightwork",         # Easy task
    "clutch",            # A crucial moment
    "wavy",              # Cool
    "lit",               # Exciting
    "troll",             # Someone who makes inflammatory comments online
    "burn",              # A clever insult
    "drool",             # To desire something greatly
    "fry",               # To roast someone
    "clout chasing",     # Seeking fame or influence
    "vibe out",          # To relax and enjoy
    "sippin' tea",       # Enjoying gossip
    "cooking",           # Preparing or planning something
    "pulling up",        # Arriving at a location
    "running it",        # Continuing or proceeding with something
    "get the bag",       # To make money
    "beef",              # Conflict or disagreement
    "shook",             # Shocked or surprised
    "squad up",          # Gather your friends
    "ghosting",          # Suddenly cutting off communication
    "lit",               # Exciting or fun
    "snatch",            # To take something quickly
    "curve",             # To reject someone
    "yeet",              # To throw or express excitement
    "hypebeast",         # Someone who follows fashion trends
    "lowkey",            # Subtle
    "highkey",           # Very obvious
    "over it",           # Tired of something
    "send it",           # Go for it
    "cheugy",           # Out of date or trying too hard
    "on brand",          # Consistent with one's image
    "vibe check",        # Assessing the atmosphere
    "dope",              # Excellent
    "janky",             # Low quality or unreliable
    "cuffing season",    # Fall and winter when people seek relationships
    "slay",              # To succeed
    "finna",             # Fixing to, planning to
    "shady",             # Untrustworthy
    "lowkey",            # Not obvious
    "swole",             # Muscular
    "feels",             # Emotions
    "litty",             # Really fun or exciting
    "adulting",          # Taking on adult responsibilities
    "squad",             # A group of friends
    "ghost",             # To cut off communication suddenly
    "vibe",              # Atmosphere or feeling
    "ratchet",           # Wild or out of control
    "dope",              # Cool or awesome
    "lit",               # Exciting or fun
    "whip",              # Car
    "on fleek",          # Perfectly done
    "cringe",            # Awkward or embarrassing
    "hype",              # Excitement or buzz
    "ratchet",           # Wild or crazy
    "savage",            # Bold or fierce
    "drip",              # Stylish or fashionable
    "flex",              # To show off
    "sips tea",          # To enjoy gossip
    "vibe out",          # To relax and enjoy
    "big mood",          # A strong feeling
    "thirst trap",       # An alluring post to attract attention
    "lit fam",           # Fun family or friends
    "finesse",           # Skillfully handling a situation
    "salty",             # Upset or bitter
    "shade",             # Subtle criticism
    "snatched",          # Looking great
    "extra",             # Over the top
    "cray",              # Crazy
    "simp",              # Someone who is overly attentive to someone else
    "no cap",            # No lie
    "smol",              # Small or cute
    "swole",             # Muscular
    "lowkey",            # Not obvious
    "highkey",           # Very obvious
    "vibe check",        # Assessing the atmosphere
    "big yikes",         # An exaggerated reaction to an embarrassing situation
    "shade",             # Subtle insult
    "bless up",          # To show gratitude
    "sippin' tea",       # Enjoying gossip
    "lit",               # Exciting
    "flex",              # To show off
    "slay queen",        # A powerful woman
    "dope",              # Cool or awesome
    "savage",            # Bold and fierce
    "cancel culture",    # The practice of canceling individuals
    "adulting",          # Taking on adult responsibilities
    "catching vibes",     # Feeling the atmosphere
    "chillin'",          # Relaxing
    "throwing shade",    # Insulting someone subtly
    "on the grind",      # Working hard
    "real talk",         # Seriously speaking
    "thank u, next",     # Moving on
    "getting lit",       # Having a good time
    "having a meltdown",  # Overwhelmed
    "caught feelings",    # Developed romantic feelings
    "turn up",           # To party
    "major key",         # Important advice or information
    "hangry",            # Hungry and angry
    "cray cray",         # Really crazy
    "spill the tea",     # Share gossip
    "living rent-free",  # Thoughts that linger in your mind
    "tripping",          # Overreacting
    "slay",              # To do something exceptionally well
    "turnt",             # Intoxicated or excited
    "good vibes only",   # Positive energy only
    "mojo",              # Charm or appeal
    "savage",            # Bold or fierce
    "burn",              # A clever insult
    "hitting the sauce",  # Drinking alcohol
    "big brain",         # Smart or clever
    "finesse",           # Skillfully handling a situation
    "curved",            # Rejected someone
    "vibe check",        # Assessing the atmosphere
    "drama",             # Gossip or conflict
    "squad goals",       # Aspirational friendship
    "dime",              # Attractive person
    "wildin'",           # Acting crazy
    "extra",             # Over the top
    "dope",              # Awesome
    "mojo",              # Charm or appeal
    "fit",               # Outfit
    "goat",              # Greatest of all time
    "all the feels",     # A lot of emotions
    "throw shade",       # Insult someone subtly
    "catch feelings",     # Develop romantic feelings
    "realness",          # Authenticity
    "no cap",            # No lie
    "shook",             # Shocked
    "smoke",             # To provoke someone
    "lit",               # Exciting
    "stay woke",         # Stay aware
    "main character",     # The focus of attention
    "headass",          # Silly or foolish person
    "adulting",          # Taking on adult responsibilities
    "bad vibes",         # Negative energy
    "mood",              # A state of mind
    "all that",          # Everything
    "flexing",           # Showing off
    "turnt",             # Excited
    "extra",             # Over the top
    "shade",             # Insult or slight
    "stan",              # An obsessed fan
    "simp",              # Someone who is overly attentive to someone else
    "cringe",            # Awkward
    "bet",               # Agreement
    "low-key",           # Not obvious
    "high-key",          # Very obvious
    "finesse",           # Skillfully handling a situation
    "fam",               # Family or close friends
    "clout",             # Influence or fame
    "juice",             # Charm or charisma
    "good vibes",        # Positive energy
    "cuffed",            # In a relationship
    "bless up",          # To show gratitude
    "wavy",              # Cool
    "catch these hands",  # Fight
    "that part",         # Agreed
    "savage",            # Bold and fierce
    "high key",          # Very obvious
    "go off",            # To speak passionately
    "lit",               # Exciting
    "hype",              # Excitement
    "big mood",          # A strong feeling
    "pull up",           # To arrive
    "flex",              # To show off
    "getting ghosted",    # Being ignored
    "lowkey",            # Subtle
    "bet",               # Agreement
    "sipping tea",       # Enjoying gossip
    "blow up",           # To become popular
    "real talk",         # Honest conversation
    "turn up",           # To party
    "flex",              # To show off
    "dope",              # Cool
    "on fleek",          # Perfect
    "spill",             # To share information
    "extra",             # Over the top
    "drag",              # Criticize harshly
    "cancel culture",    # The practice of canceling individuals
    "big yikes",         # An exaggerated reaction
    "vibe check",        # Assessing the atmosphere
    "no cap",            # No lie
    "feels",             # Feelings or emotions
    "gassed",            # Overly excited
    "cringe",            # Awkward
    "salty",             # Bitter
    "spill the tea",     # Share gossip
    "catching feelings",  # Developing romantic feelings
    "thirsty",           # Desperate for attention
    "shady",             # Untrustworthy
    "drip",              # Stylish
    "finesse",           # Skillfully handling a situation
    "savage",            # Bold and fierce
    "on brand",          # Consistent with one's image
    "throwing shade",    # Insulting someone subtly
    "ghosting",          # Cutting off communication
    "vibe out",          # To relax and enjoy
    "lowkey",            # Not obvious
    "lit",               # Exciting
    "good vibes only",   # Positive energy only
    "smol",              # Small or cute
    "realness",          # Authenticity
    "hangry",            # Hungry and angry
    "clout chasing",     # Seeking fame or influence
    "squad",             # A group of friends
    "wholesome",         # Pure or good-hearted
    "shooketh",         # Shocked or surprised
    "vibes",             # Atmosphere
    "fire",              # Amazing
    "mood",              # A state of mind
    "lit",               # Exciting
    "drip",              # Stylish
    "beef",              # Conflict
    "adulting",          # Taking on adult responsibilities
    "sipping tea",       # Enjoying gossip
    "cringe",            # Awkward or embarrassing
    "slay",              # To do something exceptionally well
    "turnt",             # Excited
    "vibe check",        # Assessing the atmosphere
    "on point",          # Exactly right
    "stoked",            # Excited
    "spill the tea",     # Share gossip
    "good vibes",        # Positive energy
    "real talk",         # Seriously speaking
    "caught feelings",    # Developed romantic feelings
    "flex",              # To show off
    "major key",         # Important advice or information
    "turning up",        # Partying or having a good time
    "poppin'",           # Excellent or cool
    "mojo",              # Charm or appeal
    "cringe",            # Awkward or embarrassing
    "spill",             # To share information
    "savage",            # Bold and fierce
    "adulting",          # Taking on adult responsibilities
    "realness",          # Authenticity
    "dope",              # Cool
    "extra",             # Over the top
    "big mood",          # A strong feeling
    "bet",               # Agreement
    "chill",             # Relaxed
    "gassed",            # Overly excited
    "spill the tea",     # Share gossip
    "that part",         # Agreed
    "turnt",             # Intoxicated or excited
    "shade",             # Insult or slight
    "swole",             # Muscular
    "vibe check",        # Assessing the mood
    "fire",              # Really good
    "stay woke",         # Stay aware
    "finesse",           # Skillfully handling a situation
    "salty",             # Upset
    "living rent-free",  # Thoughts that linger in your mind
    "clutch",            # A crucial moment
    "drama",             # Gossip or conflict
    "popping off",       # Becoming successful or popular
    "spill the tea",     # Share gossip
    "vibes",             # Atmosphere
    "all the feels",     # A lot of emotions
    "cringe",            # Awkward
    "mojo",              # Charm or appeal
    "throw shade",       # Insult someone subtly
    "catching feelings",  # Developing romantic feelings
    "on the grind",      # Working hard
    "stay lit",          # Staying excited
    "good vibes only",   # Positive energy only
    "bad vibes",         # Negative energy
    "turning up",        # Partying or having a good time
    "adulting",          # Taking on adult responsibilities
    "mood",              # A state of mind
    "lit fam",           # Fun family or friends
    "clout chasing",     # Seeking fame or influence
    "no cap",            # No lie
    "sipping tea",       # Enjoying gossip
    "spill",             # To share information
    "drama",             # Gossip or conflict
    "hype",              # Excitement
    "flexing",           # Showing off
    "bless up",          # To show gratitude
    "salty",             # Bitter
    "shade",             # Subtle criticism
    "on point",          # Exactly right
    "finesse",           # Skillfully handling a situation
    "good vibes",        # Positive energy
    "big yikes",         # An exaggerated reaction
    "turn up",           # To party
    "vibe check",        # Assessing the atmosphere
    "drip",              # Stylish
    "stay woke",         # Stay aware
    "savage",            # Bold and fierce
    "spill the tea",     # Share gossip
    "catching vibes",     # Feeling the atmosphere
    "throwing shade",    # Insulting someone subtly
    "turnt",             # Intoxicated or excited
    "adulting",          # Taking on adult responsibilities
    "no cap",            # No lie
    "hyped",             # Excited
    "shook",             # Shocked
    "dope",              # Cool
    "real talk",         # Seriously speaking
    "ratchet",           # Wild or out of control
    "beef",              # Conflict
    "vibe check",        # Assessing the atmosphere
    "drama",             # Gossip or conflict
    "spicy",             # Interesting or exciting
    "lowkey",            # Subtle
    "sipping tea",       # Enjoying gossip
    "catching feelings",  # Developing romantic feelings
    "cringe",            # Awkward
    "savage",            # Bold and fierce
    "on brand",          # Consistent with one's image
    "lit",               # Exciting
    "bless up",          # To show gratitude
    "squad",             # A group of friends
    "realness",          # Authenticity
    "stay lit",          # Staying excited
    "catch these hands",  # Fight
    "big mood",          # A strong feeling
    "fam",               # Close friends
    "lowkey",            # Not obvious
    "thirsty",           # Desperate for attention
    "ghosting",          # Cutting off communication
    "clout",             # Influence or fame
    "turning up",        # Partying or having a good time
    "spill the tea",     # Share gossip
    "dope",              # Cool
    "vibes",             # Atmosphere
    "drama",             # Gossip or conflict
    "salty",             # Bitter
    "mood",              # A state of mind
    "on fleek",          # Perfect
    "living rent-free",  # Thoughts that linger in your mind
    "fire",              # Amazing
    "drip",              # Stylish
    "slay",              # To do something exceptionally well
    "catching feelings",  # Developing romantic feelings
    "flexing",           # Showing off
    "adulting",          # Taking on adult responsibilities
    "lit",               # Exciting
    "gassed",            # Overly excited
    "real talk",         # Seriously speaking
    "turn up",           # To party
    "cringe",            # Awkward
    "vibe out",          # To relax and enjoy
    "popping off",       # Becoming successful or popular
    "spicy",             # Interesting or exciting
    "that part",         # Agreed
    "flex",              # To show off
    "squad",             # A group of friends
    "drama",             # Gossip or conflict
    "stay woke",         # Stay aware
    "good vibes",        # Positive energy
    "adulting",          # Taking on adult responsibilities
    "catch feelings",     # Develop romantic feelings
    "lit",               # Exciting
    "high-key",          # Very obvious
    "shook",             # Shocked
    "salty",             # Bitter
    "drip",              # Stylish
    "vibes",             # Atmosphere
    "spill the tea",     # Share gossip
    "mojo",              # Charm or appeal
    "thirsty",           # Desperate for attention
    "big mood",          # A strong feeling
    "good vibes only",   # Positive energy only
    "savage",            # Bold and fierce
    "on point",          # Exactly right
    "adulting",          # Taking on adult responsibilities
    "drama",             # Gossip or conflict
    "that part",         # Agreed
    "fire",              # Amazing
    "spill",             # To share information
    "low-key",           # Not obvious
    "catching feelings",  # Developing romantic feelings
    "flexing",           # Showing off
    "bless up",          # To show gratitude
    "sipping tea",       # Enjoying gossip
    "catch these hands",  # Fight
    "living rent-free",  # Thoughts that linger in your mind
    "cringe",            # Awkward
    "good vibes",        # Positive energy
    "squad",             # A group of friends
    "big yikes",         # An exaggerated reaction
    "turnt",             # Excited
    "shady",             # Untrustworthy
    "realness",          # Authenticity
    "finesse",           # Skillfully handling a situation
    "savage",            # Bold and fierce
    "spicy",             # Interesting or exciting
    "drama",             # Gossip or conflict
    "cringe",            # Awkward
    "adulting",          # Taking on adult responsibilities
    "that part",         # Agreed
    "vibe check",        # Assessing the atmosphere
    "fire",              # Amazing
    "drip",              # Stylish
    "salty",             # Bitter
    "on fleek",          # Perfect
    "spicy",             # Interesting or exciting
    "living rent-free",  # Thoughts that linger in your mind
    "good vibes",        # Positive energy
    "bless up",          # To show gratitude
    "sipping tea",       # Enjoying gossip
    "popping off",       # Becoming successful or popular
    "mood",              # A state of mind
    "vibe out",          # To relax and enjoy
    "adulting",          # Taking on adult responsibilities
    "shook",             # Shocked
    "no cap",            # No lie
    "extra",             # Over the top
    "on point",          # Exactly right
    "drama",             # Gossip or conflict
    "catching feelings",  # Developing romantic feelings
    "stay woke",         # Stay aware
    "salty",             # Bitter
    "lit",               # Exciting
    "sipping tea",       # Enjoying gossip
    "turn up",           # To party
    "good vibes",        # Positive energy
    "drip",              # Stylish
    "beef",              # Conflict
    "real talk",         # Seriously speaking
    "adulting",          # Taking on adult responsibilities
    "finesse",           # Skillfully handling a situation
    "savage",            # Bold and fierce
    "cringe",            # Awkward
    "big mood",          # A strong feeling
    "bet",               # Agreement
    "ghosting",          # Cutting off communication
    "vibe check",        # Assessing the atmosphere
    "wholesome",         # Pure or good-hearted
    "turnt",             # Excited
    "squad",             # A group of friends
    "drama",             # Gossip or conflict
    "no cap",            # No lie
    "living rent-free",  # Thoughts that linger in your mind
    "stay woke",         # Stay aware
    "on point",          # Exactly right
    "dope",              # Cool
    "spill the tea",     # Share gossip
    "savage",            # Bold and fierce
    "thirsty",           # Desperate for attention
    "catch feelings",     # Develop romantic feelings
    "adulting",          # Taking on adult responsibilities
    "lit",               # Exciting
    "hyped",             # Excited
    "savage",            # Bold and fierce
    "spicy",             # Interesting or exciting
    "on fleek",          # Perfect
    "mood",              # A state of mind
    "vibes",             # Atmosphere
    "living rent-free",  # Thoughts that linger in your mind
    "fire",              # Amazing
    "realness",          # Authenticity
    "popping off",       # Becoming successful or popular
    "extra",             # Over the top
    "adulting",          # Taking on adult responsibilities
    "salty",             # Bitter
    "big yikes",         # An exaggerated reaction
    "catch feelings",     # Develop romantic feelings
    "vibe check",        # Assessing the atmosphere
    "flex",              # To show off
    "bless up",          # To show gratitude
    "drama",             # Gossip or conflict
    "sipping tea",       # Enjoying gossip
    "thirsty",           # Desperate for attention
    "spill the tea",     # Share gossip
    "on brand",          # Consistent with one's image
    "dope",              # Cool
    "lit",               # Exciting
    "savage",            # Bold and fierce
    "that part",         # Agreed
    "mood",              # A state of mind
    "real talk",         # Seriously speaking
    "ghosting",          # Cutting off communication
    "on point",          # Exactly right
    "stay woke",         # Stay aware
    "finesse",           # Skillfully handling a situation
    "drama",             # Gossip or conflict
    "beef",              # Conflict
    "good vibes",        # Positive energy
    "no cap",            # No lie
    "hype",              # Excitement
    "turnt",             # Excited
    "spill the tea",     # Share gossip
    "squad",             # A group of friends
    "adulting",          # Taking on adult responsibilities
    "savage",            # Bold and fierce
    "good vibes only",   # Positive energy only
    "fire",              # Amazing
    "shook",             # Shocked
    "flexing",           # Showing off
    "stay woke",         # Stay aware
    "vibe check",        #
]