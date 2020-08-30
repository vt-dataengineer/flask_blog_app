from flask import Flask,render_template,request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
import json
import os
import math
from werkzeug.utils import secure_filename

'''read config file'''

with open('config.json','r') as c:
    params = json.load(c)['params']


local_server = True

'''define app'''

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD-FOLDER'] = params['upload_location']

'''Email configuration'''

app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']

)

mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']


db = SQLAlchemy(app)

'''Contact Model'''

class Contacts(db.Model):
    '''sno,name,phone_num,msg,date,email'''
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    phone_num = db.Column(db.String(12), unique=True, nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)

'''Posts Model'''

class Posts(db.Model):
    '''sno,title,slug,content,date'''
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=False, nullable=False)
    slug = db.Column(db.String(25), unique=True, nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)

'''Homapage'''

@app.route('/')
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]

    #Pagination Logic
    if page == 1:
        prev = '#'
        next = '/?page='+str(page + 1)
    elif page == last:
        prev = '/?page=' + str(page - 1)
        next  = '#'
    else:
        prev = '/?page=' + str(page - 1)
        next = '/?page=' + str(page + 1)




    return render_template('index.html',params = params, posts = posts, prev = prev, next = next)

'''About'''

@app.route('/about')
def about():
    return render_template('about.html',params = params)

'''Dashboard'''

@app.route('/dashboard', methods=['GET','POST'])
def dashboard():

    if 'user' in session and session['user'] == params['admin_user']:
        posts = Posts.query.all()
        return render_template('dashboard.html', params = params, posts = posts)


    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if username == params['admin_user'] and userpass == params['admin_password']:
            # set the session variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html',params = params, posts = posts)
    return render_template('login.html',params = params)

'''edit a post'''

@app.route("/edit/<string:sno>", methods=['GET','POST'])
def edit(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if sno == '0':
                post = Posts(title =box_title, slug = slug, content = content, img_file = img_file, tagline = tline, date = date)
                db.session.add(post)
                db.session.commit()

            else:
                post = Posts.query.filter_by(sno = sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect("/edit/"+sno)

        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html',params = params, post = post)

'''Upload a file'''

@app.route('/uploader', methods = ['GET','POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD-FOLDER'], secure_filename(f.filename)))
            return 'Uploaded Successfully'

'''Logout'''

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')

'''Delete a post'''

@app.route("/delete/<string:sno>", methods=['GET','POST'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(sno = sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

'''Contact'''

@app.route('/contact', methods = ['GET','POST'])
def contact():
    if (request.method=='POST'):
        '''add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        entry = Contacts(name=name, phone_num=phone, msg=message, date= datetime.now(), email=email)

        db.session.add(entry)
        db.session.commit()
        mail.send_message('New Blog Entry from ' +name,
                          sender = email,
                          recipients = [params['gmail-user']],
                          body = 'Message: '+ message + "\n" + 'Phone: '+phone
                          )


    return render_template('contact.html',params = params)

'''Open post'''

@app.route('/post/<string:post_slug>', methods =['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug = post_slug).first()

    return render_template('post.html',params = params, post = post)


app.run(debug=True)