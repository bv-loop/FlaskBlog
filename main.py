###################################################
######IMPORTING PACKAGES#######
###################################################

from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
from functools import wraps
import os
import smtplib

###################################################
######CREATING AND CONFIGURING THE FLASK APP#######
###################################################

#SETUP THE FLASK APP
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
ckeditor = CKEditor(app)
Bootstrap(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)
#EMAIL CREDENTIALS
OWN_EMAIL = os.environ.get("EMAIL_ADDRESS")
OWN_PASSWORD = os.environ.get("EMAIL_PASSWORD")

##CONNECT TO DB / CONFIGURING THE APP
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


#CONFIGURE FLASK LOG IN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)


#LOGIN MANAGER FUNCTION TO RETURN THE CURRENT ACTIVE USER OBJECT
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#CREATING A NEW WRAPPER FUNCTION/ DECORATOR FOR ADMIN ONLY
def admin_only(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_func


###################################################
######CONFIGURE TABLES FOR DATABASE#######
###################################################

#USER TABLE
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique= True)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    # ***Parent Relationship with Blogpost Table***
    posts = relationship("BlogPost", back_populates='author')

    # ***Parent Relationship with Comment Table***
    comments = relationship("Comment", back_populates="comment_author")


#BLOG POSTS TABLE
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    # ***Child Relationship with User Table***
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = relationship('User',back_populates='posts')

    # ***Parent Relationship with Comment Table***
    comments = relationship("Comment", back_populates="parent_post")    
    
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


#COMMENTS TABLE
class Comment(db.Model):
    __tablename__= "comments"
    id = db.Column(db.Integer, primary_key = True)
    text = db.Column(db.Text, nullable=False)

    # ****Child relationship with User table****
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    # ****Child relationship with BlogPost table****
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")


###################################################
######ROUTES AND FUNCTIONS FOR THE WEBSITE#######
###################################################

#HOME PAGE ROUTE AND PAGE
@app.route('/')
def get_all_posts():
    posts = BlogPost.query.order_by(BlogPost.id.desc()).all()
    return render_template("index.html", all_posts=posts, current_user = current_user)


#REGISTER ROUTE AND PAGE
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email = request.form.get('email')).first():
            print(User.query.filter_by(email=request.form.get('email')).first())
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256', 
            salt_length=8
        )
            
        new_user = User(
            email = request.form.get('email'),
            password = hash_and_salted_password,
            name = request.form.get('name')
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('get_all_posts'))

    return render_template("register.html", form = form, current_user = current_user)


#LOGIN ROUTE AND PAGE
@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email = email).first()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password,password):
            flash("Password incorrect, please try again.")
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))
    return render_template("login.html", form = form, current_user = current_user)


#LOGOUT FUNCTION, REDIRECT TO HOMEPAGE
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


#ROUTE FOR DISPLAYING A POST
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to log in or register to comment.")
            return redirect(url_for("login"))
        
        new_comment = Comment(
            text = request.form.get("comment_text"),
            comment_author = current_user,
            parent_post = requested_post)
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", form = form, post=requested_post, current_user = current_user)


#ROUTE FOR ABOUT PAGE
@app.route("/about")
def about():
    return render_template("about.html", current_user = current_user)


#ROUTE FOR CONTACT PAGE
@app.route("/contact",  methods=["GET","POST"])
def contact():
    if request.method=="POST":
        data = request.form
        send_email(data['name'],data['email'],data['phone'],data['message'])
        return render_template('contact.html', msg_sent = True)
    return render_template("contact.html", current_user = current_user, msg_sent = False)


#FUNCTION TO SEND EMAILS TO OWNER
def send_email(name, email, phone, message):
    email_message = f"Subject:New Blog Message\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage: {message}"
    OWN_EMAIL = os.environ.get("EMAIL_ADDRESS")
    OWN_PASSWORD = os.environ.get("EMAIL_PASSWORD")
    RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL")
    SMTP_HOST = os.environ.get("SMTP_HOST")
    SMTP_PORT = int(os.environ.get("SMTP_PORT"))
    with smtplib.SMTP(host = SMTP_HOST, port=SMTP_PORT) as connection:
        connection.starttls()
        connection.login(OWN_EMAIL, OWN_PASSWORD)
        connection.sendmail(from_addr=OWN_EMAIL, to_addrs=RECIPIENT_EMAIL, msg= email_message)


#ROUTE TO CREATE A NEW POST, REDIRECT TO HOMEPAGE
@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, current_user = current_user)


#ROUTE TO EDIT POST AND RENDER UPDATED POST
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=current_user,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, is_edit = True, current_user = current_user)


#ROUTE TO DELETE POSTS
@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


#CONTEXT PROCESSER TO INJECT CURRENT YEAR INTO THE FOOTER TEMPLATE
@app.context_processor
def inject_date():
    return {'year': date.today().strftime("%Y") }


###################################################
#RUN SCRIPT
###################################################

if __name__ == "__main__":
    app.run(host = '0.0.0.0', port = 5000)
