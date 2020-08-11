from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, BooleanField, TextField, PasswordField, validators
import os
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
app = Flask(__name__)

####################################################################
# Config Section
####################################################################
#Setup app configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
#Because login relies on session to keep users logged in,
#we have to specify where this information will be stored and
#provide an app key to associate with the session
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = os.urandom(12)

#Setup database and login managers
#Flask Login module helps with session management,
#ensuring that once the user is logged in, it remains like That
#and has access to the app throughout his/her time
#using the app
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'

#Tells the login manager which field to lookup when checking
#if user is authorized
@login.user_loader
def load_user(id):
    return User.query.get(int(id))

#Helper function to populate Task Type table and create all tables in the database
def dbHelper():
    db.create_all()
    types = list()
    t1 = TodoType.query.filter(TodoType.id==1).filter(TodoType.type=="todo").first()
    if not t1:
        types.append(TodoType(id=1, type="todo"))
    t1 = TodoType.query.filter(TodoType.id==2).filter(TodoType.type=="doing").first()
    if not t1:
        types.append(TodoType(id=2, type="doing"))
    t1 = TodoType.query.filter(TodoType.id==3).filter(TodoType.type=="done").first()
    if not t1:
        types.append(TodoType(id=3, type="done"))

    if types:
        db.session.add_all(types)
        db.session.commit()


####################################################################
# Database Schema Section
####################################################################
class User(UserMixin, db.Model):
    __tablename__ = 'User'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))
    passwordHash = db.Column(db.String)
    passwordSalt = db.Column(db.String)

#Both functions below are responsible for generating
#secure passwords by generating a salt to append to user's selected
#password and hashing the hash+password string
    def set_password(self, password):
        self.passwordSalt = str(bcrypt.gensalt())
        self.passwordHash = generate_password_hash(password + self.passwordSalt)

    def check_password(self, password):
        return check_password_hash(self.passwordHash, password + self.passwordSalt)

class TodoType(db.Model):
    __tablename__ = 'TodoType'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(80))

class Todo(db.Model):
    __tablename__ = 'Todo'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200))
    userid = db.Column(db.Integer, db.ForeignKey('User.id'))
    type = db.Column(db.Integer, db.ForeignKey('TodoType.id'))


####################################################################
# Flask Form Section
####################################################################
#Flasf forms facilitate form management and validation, used for user login and registration
class Registration(Form):
    username = TextField("Username", [validators.Required(),validators.Length(min=4, max=20)])
    password = PasswordField("Password", [validators.Required()])

class LoginForm(Form):
    username = TextField("Username", [validators.Required(),validators.Length(min=4, max=20)])
    password = PasswordField("Password", [validators.Required()])


####################################################################
# Routes Section
####################################################################

#Checks if user is already logged in, and if not,
#it logs in registered user
@app.route('/login', methods=['GET','POST'])
def login():
    #Checks if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm(request.form)
    #If request method is POST and form is validated,
    #proceeds to check if login is valid
    if request.method == "POST" and form.validate():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            if user is None:
                error="Invalid Username"
            elif not user.check_password(form.password.data):
                error = "Invalid Password"
            return render_template('login.html', form=form, error=error)
        login_user(user, True)
        #Flask login immediately adds "next" argument into
        #the login request to redirect to the index page and
        #prevent malicious attacks in the URL, as it only allows
        #redirects inside the application
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = 'index.html'
        return redirect(url_for('index'))
    #If request method is GET, just returns login page
    return render_template('login.html', form=form)

#Logs user out
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

#Checks if username is already taken, and if not,
#if registers users and perform login
@app.route('/register',methods=['GET','POST'])
def register_page():
    form = Registration(request.form)
    if request.method == "POST" and form.validate():
        usern = form.username.data
        passw = form.password.data
        #checks if username is already taken
        user = User.query.filter_by(username=usern).first()
        if user is not None:
            error = "That username is already taken, please choose another"
            return render_template('register.html', form=form, error=error)
        else:
            #if not, registers user and calls set_password function to secure
            #users' password
            newuser = User(username=usern)
            newuser.set_password(passw)
            db.session.add(newuser)
            db.session.commit()
            login_user(newuser)

            return render_template('index.html', error="Registered with success!")
    #If request method is GET, returns register page
    return render_template("register.html", form=form)


#Routes to add tasks by type (To do, doing, done)
@app.route('/addTodoTask', methods=['POST'])
def addtodo():
    addTaskHelper("todo", request)
    return redirect(url_for('index'))

@app.route('/addDoingTask', methods=['POST'])
def adddoing():
    addTaskHelper("doing",request)
    return redirect(url_for('index'))

@app.route('/addDoneTask', methods=['POST'])
def adddone():
    addTaskHelper("done",request)
    return redirect(url_for('index'))

#Helper function to add tasks in the database under the correct user id and task type
def addTaskHelper(typetask,request):
    tasktype = TodoType.query.filter_by(type=typetask).first()
    todo =Todo(text=request.form['todoitem'],type=tasktype.id ,userid=current_user.get_id())
    db.session.add(todo)
    db.session.commit()

#Helper function to change the task type,
#moving from one state to the next (except for "done" tasks)
def moveTask(request):
    tasks = request.form.getlist("todotask")
    for task in tasks:
        t = Todo.query.filter(Todo.id==task).filter(Todo.userid==current_user.get_id()).first()
        if t:
            tasktype = TodoType.query.filter_by(id=t.type).first()
            if tasktype.type =="todo":
                newtype = "doing"
            elif tasktype.type =="doing":
                newtype = "done"
            tasktype = TodoType.query.filter_by(type=newtype).first()
            t.type = tasktype.id
            db.session.add(t)
    if tasks:
        db.session.commit()

#Helper function to delete all selected tasks on the database according to user id
def deleteTask(request):
    tasks = request.form.getlist("todotask")
    for task in tasks:
        t = Todo.query.filter(Todo.id==task).filter(Todo.userid==current_user.get_id()).first()
        if t:
            db.session.delete(t)
    if tasks:
        db.session.commit()

#Route to delete or move tasks, depending on the button used
#to call the route
@app.route('/todo', methods=['POST'])
def todo():

    if request.method == 'POST':
        if request.form.get('button') == 'Delete task':
            deleteTask(request)
        elif request.form.get('button') == 'Move task to next stage':
            moveTask(request)
    return redirect(url_for('index'))

#Route to the main page. It requires login to access it.
#Returns all the tasks registered under the logged in user
@app.route('/')
@login_required
def index():
    todo = Todo.query.filter(TodoType.type=="todo").filter(Todo.type==TodoType.id).filter(Todo.userid==current_user.get_id()).all()
    doing = Todo.query.filter(TodoType.type=="doing").filter(Todo.type==TodoType.id).filter(Todo.userid==current_user.get_id()).all()
    done = Todo.query.filter(TodoType.type=="done").filter(Todo.type==TodoType.id).filter(Todo.userid==current_user.get_id()).all()
    return render_template('index.html', todoall=todo, doingall=doing, doneall=done)


####################################################################
# Runs application
####################################################################
if __name__ == '__main__':
    dbHelper()
    app.run(debug=True)
