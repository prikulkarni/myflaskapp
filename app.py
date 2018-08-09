from flask import Flask, render_template, flash, redirect, url_for, request, session, logging
#from data import Articles
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:linux123@localhost/testdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'change'
db = SQLAlchemy(app)
#Articles = Articles()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)

    def __init__(self, name, email, username, password):
        self.name =  name
        self.email = email
        self.username = username
        self.password = password

    def __repr__(self):
        return '<id {}>'.format(self.id)

class Article(db.Model):
    __tablename__ = "articles"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    body = db.Column(db.Text, nullable=False)
    create_date = db.Column(db.DateTime)

    def __init__(self, title, author, body):
        self.title =  title
        self.author = author
        self.body = body

    def __repr__(self):
        return '<id {}>'.format(self.id)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    #Get Articles
    articles = Article.query.all()
    if (articles != None):
        return render_template('articles.html', articles=articles)
    else:
        msg = "No articles yet"
        return render_template('articles.html', msg=msg)

#Single Article
@app.route('/article/<string:id>/')
def article(id):
    #Get Single Article
    article = Article.query.filter_by(id=id).one()
    return render_template('article.html', article=article)

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    password = PasswordField('Password', [
    validators.DataRequired(),
    validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        rec = User(name, email, username, password)
        db.session.add(rec)
        db.session.commit()

        flash('Registered', 'success' )
        return redirect(url_for('index'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        user = User.query.filter_by(username=username).one_or_none()
        if user != None:
            pwd = user.password
            if sha256_crypt.verify(password_candidate, pwd):
                #Passes
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Password'
                return render_template('login.html', error=error)
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorised. Please Login', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    #Get Articles
    username = session['username']
    articles = Article.query.filter_by(author=username).all()
    if (articles != None):
        return render_template('dashboard.html', articles=articles)
    else:
        msg = "No articles written by you yet"
        return render_template('dashboard.html', msg=msg)

#Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=5)])

#Add Article Route
@app.route('/add_article',methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        username = session['username']
        body = form.body.data
        art = Article(title, username, body)
        db.session.add(art)
        db.session.commit()

        flash('Article Created','success')
        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
