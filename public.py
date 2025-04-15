import uuid
from flask import *
from database import *

public = Blueprint ("public",__name__)

@public.route("/")
def index():
    return render_template("public/login.html")

@public.route("/login" , methods=['post' , 'get'])
def login():
    
    if 'submit' in request.form:
        username=request.form['uname']
        password=request.form['pas']
        q="select * from login where username='%s' and password='%s'"%(username,password)
        res=select(q)
        
        if res:
            session['login_id']=res[0]['login_id']
            if res[0]['user_type']=='admin':
                
                return "<script>alert('admin login success'); window.location='/admin'</script>"
            
            elif res[0]['user_type']=='user':
                q3="select * from user where login_id='%s'"%(session['login_id'])
                res2=select(q3)
                if res2:
                    # session['user_id']=res2[0]['user_id']
                    # return "<script>alert('user login success'); window.location='/user_home'</script>"
                    user_status=res2[0]['status']
                    if user_status != 'blocked':
                        session['user_id']=res2[0]['user_id']
                        return "<script>alert('user login success'); window.location='/user_home'</script>"
                    else:
                        return "<script>alert('you are blocked by admin'); window.location='/login'</script>"
                else:
                    return "<script>alert('invalid user login '); window.location='/login'</script>"
        else:
            return "<script>alert('invalid user login '); window.location='/login'</script>"
    return render_template("public/login.html")


@public.route('/registration', methods=['get' , 'post'] )
def registration():
    if 'submit' in request.form:
        fname=request.form['fname']
        lname=request.form['lname']
        dob=request.form['dob']
        gender=request.form['gender']
        place=request.form['place']
        phone=request.form['phone']
        email=request.form['email']
        username=request.form['username']
        password=request.form['password']
        photo=request.files['photos']
        path="static/image/"+str(uuid.uuid4())+photo.filename
        photo.save(path)
        q1="insert into login values(NULL,'%s','%s','user')"%(username,password)
        q11=insert(q1)
        q2="insert into user values(NULL,'%s','%s','%s','%s','%s','%s','%s','%s' , '%s' , '%s' ,'user','0')"%(q11,fname,lname,username,dob,gender , place , path , phone , email)
        insert(q2)
        return "<script>alert('Register Success');window.location='/login';</script>"
    return render_template("public/registration.html")