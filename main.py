from flask import *
from database import *
from public import *
from admin import*
from user import *



app = Flask(__name__)
app.register_blueprint(public)
app.register_blueprint(user)
app.register_blueprint(admin)


app.secret_key="abcd"
app.run(debug=True)

