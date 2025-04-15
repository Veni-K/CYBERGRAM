from flask import *
from database import *

admin=Blueprint("admin" , __name__)

@admin.route("/admin")
def admin_home():
    return render_template("admin/admin_home.html")

@admin.route("/change_password" , methods=['post' , 'get'])
def change_password():
    login_id=session['login_id']
    if "submit" in request.form:
        password=request.form['password']
        q1="UPDATE `login` SET password='%s' WHERE login_id='%s'"%(password,login_id)
        update(q1)
        return "<script>alert('password changed');window.location='/change_password';</script>"
    return render_template('admin/change_password.html')

@admin.route("/view_user")
def view_user():
    
    data={} 
    # log={}
    # q3="select * from login where user_type='user'"
    # log=select(q3)
    # q2="select * from user"
    # data=select(q2)
    q1="select * from user inner join login on user.login_id = login.login_id"
    data=select(q1)
    if 'action' in request.args:
        action=request.args['action']
        id=request.args['id']
        
    else:
        action=None
        
    if action=='block':
        q="UPDATE `user` SET status='blocked' WHERE user_id='%s'"%(id)
        update(q)
        if data[0]['status']=='blocked':
            return "<script>alert('Already Blocked');window.location='/view_user';</script>"    
        return "<script>alert('Blocked');window.location='/view_user';</script>"
    if action=='unblock':
        q="UPDATE `user` SET status='user' WHERE user_id='%s'"%(id)
        update(q)
        if data[0]['status']=='user':
            return "<script>alert('Already unblocked');window.location='/view_user';</script>"    
        return "<script>alert('unblocked');window.location='/view_user';</script>"
    return render_template("admin/view_user.html",data=data )


@admin.route("/view_blocked_user")
def view_blocked_user():
    data={}
    q1="select * from user where status='blocked'"
    data=select(q1)
    return render_template('admin/view_blocked_users.html' , data=data)


@admin.route("/view_complaints" , methods=['post' , 'get'] )
def view_complaints():
    data={}
    q1="select * from complaint"
    data=select(q1)
    if 'submit' in request.form:
        reply = request.form['reply']
        complaint_id = request.form['complaint_id'] 
        q2 = "UPDATE complaint SET reply='%s', status='complaint considered by admin' WHERE complaint_id='%s'"%(reply, complaint_id)
        update(q2)
        return "<script>alert('replied');window.location='/view_complaints';</script>"
    return render_template('admin/view_complaints.html' , data=data)