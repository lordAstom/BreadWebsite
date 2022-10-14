import werkzeug.security
from flask import Flask, render_template, redirect, url_for, flash, g, request
from functools import wraps
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import *
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, Column, Integer, String, and_
import json
from extra import *
from config import Data, SecretData
import datetime

data = Data()
secret_data = SecretData()

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_data.secret_key
ckeditor = CKEditor(app)
Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)
# Flask-SQLAlchemy settings
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///breadshop.db'  # File-based SQL database
SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning
db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    group = db.Column(db.String(255), nullable=False)
    orders = relationship("Order", back_populates="customer")


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    order = db.Column(db.String(255), nullable=False)
    date = db.Column(db.String(255), nullable=False)
    completed = db.Column(db.Boolean(), nullable=False)
    delivered = db.Column(db.Boolean(), nullable=False)
    time_day = db.Column(db.String(255), nullable=False)
    customer = relationship("User", back_populates="orders")
    client = db.Column(db.String(255), nullable=False)


db.create_all()


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return redirect(url_for('indexEng', next=request.url))
        else:
            return f(*args, **kwargs)

    return decorated_function


loggin_logger = Log("login ssuccseful", "login_info.log")
order_logger = Log("order ssuccseful", "order_info.log")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return redirect(url_for('indexEng'))


@app.route('/Eng', methods=['POST', 'GET'])
def indexEng():
    order_form = BreadOrderForm()
    order_form.validate_on_submit()
    error1 = None
    error2 = None
    if order_form.validate_on_submit():
        error1 = valid_day(order_form.date.data, "en")
        error2 = valid_period(order_form.date.data, order_form.day_time.data, "en")
        order_logger.info(f"{order_form.day_time.data}")
        verifier = ReVerify(order_logger)

        order = {}
        # start of secondary vailidation
        valid_order = True
        if (error1 and error2):
            valid_order = False
        order_logger.info(f"{order_form.White_loaf.data}")
        for bread in data.prices.keys():
            if verifier.verify_int(eval(f'order_form.{bread}.data'), 0, 6):
                order[bread] = eval(f'order_form.{bread}.data')
        order_logger.info(f"{error2}")
        if not verifier.verify_int(order_form.recurring.data, 0, 7):
            valid_order = False
        if sum(order.values())==0:
            valid_order = False
        if valid_order:
            # end of secondary validation
            date = order_form.date.data
            for i in range(order_form.recurring.data):
                new_order = Order(user_id=current_user.id, order=json.dumps(order), date=date, completed=False,
                                  delivered=False, time_day=order_form.day_time.data, client=current_user.username)
                db.session.add(new_order)
                db.session.commit()
                date = date + timedelta(weeks=1)
                order_logger.info("order received")
            return redirect(url_for("orders"))

    return render_template("indexEng.html", bread_types=data.bread_types,
                           order_form=order_form, error1=error1, error2=error2)

@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    form.validate_on_submit()
    error1 = None
    error2 = None
    if form.validate_on_submit():
        valid = True
        if User.query.filter_by(username=form.username.data).first():
            error1 = 'username taken'
            valid = False
        if User.query.filter_by(username=form.email.data).first():
            error2 = "email taken"
            valid = False
        if valid:
            verifier = ReVerify(loggin_logger)
            if verifier.verify_string(form.username.data) and verifier.verify_string(
                    form.password.data) and verifier.verify_string(form.group.data) and verifier.verify_string(
                form.email.data):
                new_user = User(username=form.username.data, password=generate_password_hash(str(form.password.data),
                                    method="pbkdf2:sha256", salt_length=14), group=form.group.data, email=form.email.data)
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                loggin_logger.info(f"user {form.username.data} from group {form.group.data} registered correctly")
                return redirect(url_for("indexEng"))
    return render_template("register.html", form=form, error1=error1, error2=error2)

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    verifier = ReVerify(loggin_logger)
    if form.validate_on_submit():
        if verifier.verify_string(form.password.data) and verifier.verify_string(form.username.data):
            user_db = User.query.filter_by(username=form.username.data).first()
            if user_db:  # check if user in database
                if werkzeug.security.check_password_hash(user_db.password,
                                                         form.password.data):  # check if correct password
                    login_user(user_db)
                    loggin_logger.info(f"user {form.username.data} logged in correctly")
                    return redirect(url_for("indexEng"))
    return render_template("login.html", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('indexEng'))


@app.route('/orders', methods=['POST', 'GET'])
@login_required
def orders():
    user_id = current_user.id
    undelivered_orders = OrderViewer(db.session.query(Order).filter(and_(Order.user_id == user_id, Order.date > (datetime.date.today()-datetime.timedelta(days=1)))).all(), "en")
    delivered_orders = OrderViewer(db.session.query(Order).filter(and_(Order.user_id == user_id, Order.date < (datetime.date.today()-datetime.timedelta(days=1)))).all(), "en")
    form = DeleteForm()
    undelivered_orders.add_form(form)
    form.validate_on_submit()
    if form.validate_on_submit():
        for i in undelivered_orders:
            if undelivered_orders.form_data.data:
                db.session.delete(undelivered_orders.order_instance)
        db.session.commit()
        return redirect(url_for("orders"))
    return render_template("orders.html", form=form, delivered_orders=delivered_orders, undelivered_orders=undelivered_orders)


@app.route('/account', methods=['POST', 'GET'])
@login_required
def account():
    form = ModifyUser()
    form.validate_on_submit()
    error1 = None
    error2 = None
    user_data = {"user": current_user.username, "email": current_user.email, "group": current_user.group}
    if form.validate_on_submit():
        valid = True
        user = User.query.filter_by(username=current_user.username).first()
        if User.query.filter_by(username=form.username.data).first():
            if user.username != form.username.data:
                error1 = 'username taken'
                valid = False
        if User.query.filter_by(username=form.email.data).first():
            if user.email != form.email.data:
                error2 = "email taken"
                valid = False
        if valid:
            loggin_logger.info("works")
            if werkzeug.security.check_password_hash(current_user.password, form.old_password.data):
                user.username = form.username.data
                user.email = form.email.data
                user.group = form.group.data
                if form.new_password.data:
                    user.password = generate_password_hash(str(form.new_password.data), method="pbkdf2:sha256", salt_length=14)
                db.session.commit()
    return render_template("user.html", form=form, error1=error1, error2=error2, user_data=user_data)

@app.route('/baker')
@admin_required
def baker():
    undelivered_orders = OrderViewer(db.session.query(Order).filter(
        and_(Order.date > (datetime.date.today()))).all(), "en")
    delivered_orders = OrderViewer(db.session.query(Order).filter(
        Order.date < (datetime.date.today())).all(), "en")
    today_orders = OrderViewer(db.session.query(Order).filter(
        Order.date == (datetime.date.today())).all(), "en")

    return render_template("admin.html",undelivered_orders=undelivered_orders,delivered_orders=delivered_orders,today_orders=today_orders)


# Spanish version
@app.route('/Es', methods=['POST', 'GET'])
def indexEs():
    order_form = PedidoPan()
    order_form.validate_on_submit()
    error1 = None
    error2 = None
    if order_form.validate_on_submit():
        error1 = valid_day(order_form.date.data, "es")
        error2 = valid_period(order_form.date.data, order_form.day_time.data, "es")
        order_logger.info(f"{order_form.day_time.data}")
        verifier = ReVerify(order_logger)

        order = {}
        # start of secondary vailidation
        valid_order = True
        if (error1 and error2):
            valid_order = False
        order_logger.info(f"{order_form.White_loaf.data}")
        for bread in data.prices.keys():
            if verifier.verify_int(eval(f'order_form.{bread}.data'), 0, 6):
                order[bread] = eval(f'order_form.{bread}.data')
        order_logger.info(f"{error2}")
        if not verifier.verify_int(order_form.recurring.data, 0, 7):
            valid_order = False
        if sum(order.values())==0:
            valid_order = False
        if valid_order:
            # end of secondary validation
            date = order_form.date.data
            for i in range(order_form.recurring.data):
                new_order = Order(user_id=current_user.id, order=json.dumps(order), date=date, completed=False,
                                  delivered=False, time_day=order_form.day_time.data, client=current_user.username)
                db.session.add(new_order)
                db.session.commit()
                date = date + timedelta(weeks=1)
                order_logger.info("order received")
            return redirect(url_for("pedidos"))

    return render_template("indexEs.html", bread_types=data.bread_types,
                           order_form=order_form, error1=error1, error2=error2)

@app.route('/registro', methods=['POST', 'GET'])
def registro():
    form = RegisterForm()
    form.validate_on_submit()
    error1 = None
    error2 = None
    if form.validate_on_submit():
        valid = True
        if User.query.filter_by(username=form.username.data).first():
            error1 = 'este usario ya ha sido elegido'
            valid = False
        if User.query.filter_by(username=form.email.data).first():
            error2 = "este correo ya ha sido elegido"
            valid = False
        if valid:
            verifier = ReVerify(loggin_logger)
            if verifier.verify_string(form.username.data) and verifier.verify_string(
                    form.password.data) and verifier.verify_string(form.group.data) and verifier.verify_string(
                form.email.data):
                new_user = User(username=form.username.data, password=generate_password_hash(str(form.password.data),
                                    method="pbkdf2:sha256", salt_length=14), group=form.group.data, email=form.email.data)
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                loggin_logger.info(f"user {form.username.data} from group {form.group.data} registered correctly")
                return redirect(url_for("indexEs"))
    return render_template("registro.html", form=form, error1=error1, error2=error2)

@app.route('/acceso', methods=['POST', 'GET'])
def acceso():
    form = LoginForm()
    verifier = ReVerify(loggin_logger)
    if form.validate_on_submit():
        if verifier.verify_string(form.password.data) and verifier.verify_string(form.username.data):
            user_db = User.query.filter_by(username=form.username.data).first()
            if user_db:  # check if user in database
                if werkzeug.security.check_password_hash(user_db.password,
                                                         form.password.data):  # check if correct password
                    login_user(user_db)
                    loggin_logger.info(f"user {form.username.data} logged in correctly")
                    return redirect(url_for("indexEs"))
    return render_template("loginES.html", form=form)


@app.route('/pedidos', methods=['POST', 'GET'])
@login_required
def pedidos():
    user_id = current_user.id
    undelivered_orders = OrderViewer(db.session.query(Order).filter(and_(Order.user_id == user_id, Order.date > (datetime.date.today()-datetime.timedelta(days=1)))).all(), "es")
    delivered_orders = OrderViewer(db.session.query(Order).filter(and_(Order.user_id == user_id, Order.date < (datetime.date.today()-datetime.timedelta(days=1)))).all(), "es")
    form = DeleteForm()
    undelivered_orders.add_form(form)
    form.validate_on_submit()
    if form.validate_on_submit():
        for i in undelivered_orders:
            if undelivered_orders.form_data.data:
                db.session.delete(undelivered_orders.order_instance)
        db.session.commit()
        return redirect(url_for("pedidos"))
    return render_template("pedidos.html", form=form, delivered_orders=delivered_orders, undelivered_orders=undelivered_orders)


@app.route('/usuario', methods=['POST', 'GET'])
@login_required
def usuario():
    form = ModifyUser()
    form.validate_on_submit()
    error1 = None
    error2 = None
    user_data = {"user": current_user.username, "email": current_user.email, "group": current_user.group}
    if form.validate_on_submit():
        valid = True
        user = User.query.filter_by(username=current_user.username).first()
        if User.query.filter_by(username=form.username.data).first():
            if user.username != form.username.data:
                error1 = 'Usuario ya cogido'
                valid = False
        if User.query.filter_by(username=form.email.data).first():
            if user.email != form.email.data:
                error2 = "Correo ya escogido"
                valid = False
        if valid:
            loggin_logger.info("works")
            if werkzeug.security.check_password_hash(current_user.password, form.old_password.data):
                user.username = form.username.data
                user.email = form.email.data
                user.group = form.group.data
                if form.new_password.data:
                    user.password = generate_password_hash(str(form.new_password.data), method="pbkdf2:sha256", salt_length=14)
                db.session.commit()
    return render_template("usuario.html", form=form, error1=error1, error2=error2, user_data=user_data)

# Run Stuff
if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
