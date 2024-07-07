import werkzeug.security
from flask import Flask, render_template, redirect, url_for, request
from functools import wraps
from flask_bootstrap import Bootstrap
from datetime import date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import *
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, Column, Integer, String, and_, text
import json
from extra import *
from config import Data, SecretData
import datetime

MAX_BREADS = 15
data = Data()
secret_data = SecretData()

app = Flask(__name__)



# Flask-SQLAlchemy settings
# Avoids SQLAlchemy warning


def create_app():
    """
    Creates framework for it website to run (blackbox)
    """
    global app
    global db
    global login_manager
    app = Flask(__name__)
    Bootstrap(app)
    app.config['SECRET_KEY'] = "gdfgsksdflsdfjksjfkdsjfksjkfjdls"
    login_manager = LoginManager()
    login_manager.init_app(app)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///breadshop.db'  # File-based SQL database
    db = SQLAlchemy(app)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    return app

create_app()

def find_num_breads(date,time):
        """
        
        """
        stmt = text("""SELECT SUM(num_breads) FROM "orders" WHERE time_day = '"""+time+"""' AND date = '"""+str(date)+"""'""")
        b = db.session.execute(stmt)
        return b.first()[0]

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    group = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    orders = relationship("Order", back_populates="customer")
    date = db.Column(db.String(255), nullable=False)



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
    num_breads = db.Column(db.Integer)


def admin_required(f):
    """
    Makes sure only admin (user.id == 1) can acces when decorating page function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if current_user.id != 1:
                return redirect(url_for('indexEng', next=request.url))
            else:
                return f(*args, **kwargs)
        except AttributeError:
            return "Item not found", 400
    return decorated_function

loggin_logger = Log("login ssuccseful", "login_info.log")
order_logger = Log("order succseful", "order_info.log")

def index(lang):
    """
    Presents the main webpage in either spaninsh or english and allows for ordering the right amount of bread if logged in
    Checks that not more than 15 breads ordered in a day
     """
    if lang == "es":
        order_form = PedidoPan()
    elif lang == "en":
        order_form = BreadOrderForm()        
    order_form.validate_on_submit()
    error1,error2,error3 = None, None, None
    if order_form.validate_on_submit(): #
        error1 = valid_day(order_form.date.data, lang)
        error2 = valid_period(order_form.date.data, order_form.day_time.data, lang)
        verifier = ReVerify(order_logger)
        order = {}
        # start of secondary vailidation
        valid_order = True
        if (error1 and error2):
            valid_order = False
        for bread in data.prices.keys():
            if verifier.verify_int(eval(f'order_form.{bread}.data'), 0, 6):
                order[bread] = eval(f'order_form.{bread}.data')
        if error2:
            order_logger.info(f"{error2}")
        if not verifier.verify_int(order_form.recurring.data, 0, 7):
            valid_order = False
        num_loafs = sum(list(order.values())[:len(order.values())-1])+sum(list(order.values())[len(order.values())-1:])/2
        if sum(order.values()) == 0:
            valid_order = False
        elif num_loafs > 15:
            if lang == "es":
                error3 = f"No se puede pedir mas de {MAX_BREADS} panes"
            elif lang == "en":
                error3 = f"You may not order more than {MAX_BREADS} breads"
            valid_order = False
        if valid_order:
            order_logger.info(f"{list(order.values())}--")
            # end of secondary validation
            date = order_form.date.data
            new_order_list = []
            for i in range(order_form.recurring.data):
                previous = find_num_breads(date,order_form.day_time.data)
                if num_loafs > 15:
                    if lang == "es":
                        error3 = f"No se puede pedir mas de {MAX_BREADS} panes"
                    elif lang == "en":
                        error3 = f"You may not order more than {MAX_BREADS} breads"
                elif previous == None:
                    new_order = Order(user_id=current_user.id, order=json.dumps(order), date=date, completed=False,
                    delivered=False, time_day=order_form.day_time.data, client=current_user.username, num_breads = num_loafs)
                    db.session.add(new_order)

                elif previous + num_loafs > 15:
                    if lang == "es":
                        error3 = f"No se puede pedir mas de {MAX_BREADS-previous} panes el {date}"
                    elif lang == "en":
                        error3 = f"You may not order more than {MAX_BREADS-previous} bread on {date}"
                else:
                    new_order = Order(user_id=current_user.id, order=json.dumps(order), date=date, completed=False,
                    delivered=False, time_day=order_form.day_time.data, client=current_user.username, num_breads = num_loafs)
                    db.session.add(new_order)
 
                date = date + timedelta(weeks=1)
                order_logger.info("order received")
            db.session.commit()
            if not error3:
                if lang == "es":
                    return redirect(url_for("pedidos"))
                elif lang == "en":
                    return redirect(url_for("orders"))
    if lang == "es":
        return render_template("indexEs.html", bread_types=data.bread_types,
                           order_form=order_form, error1=error1, error2=error2, error3=error3)
    elif lang == "en":
        return render_template("indexEng.html", bread_types=data.bread_types,
                           order_form=order_form, error1=error1, error2=error2, error3 = error3)       

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return redirect(url_for('indexEng'))


@app.route('/Eng', methods=['POST', 'GET'])
def indexEng():
    return index("en")


@app.route('/register', methods=['POST', 'GET'])
def register():
    """
    Backend of english registering a new user after checking the email and user do not exist already in database.
    If no issues happen logs in new user, adds them to database and redirects to the mainpage
    """
    form = RegisterForm()
    form.validate_on_submit()
    error1, error2 = None, None
    if form.validate_on_submit():
        valid = True
        if User.query.filter_by(username=form.username.data).first():
            error1 = 'username taken'
            valid = False
        if User.query.filter_by(email=form.email.data).first():
            error2 = "email taken"
            valid = False
        if valid:
            verifier = ReVerify(loggin_logger)
            if verifier.verify_string(form.username.data) and verifier.verify_string(
                    form.password.data) and verifier.verify_string(form.group.data) and verifier.verify_string(
                form.email.data):
                new_user = User(username=form.username.data, password=generate_password_hash(str(form.password.data),
                    method="pbkdf2:sha256",salt_length=14),group=form.group.data, address = form.address.data, email=form.email.data, date=str(datetime.date.today()))
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                loggin_logger.info(f"user {form.username.data} from group {form.group.data} registered correctly")
                return redirect(url_for("indexEng"))
    return render_template("register.html", form=form, error1=error1, error2=error2)


@app.route('/login', methods=['POST', 'GET'])
def login():
    """
    Backend of english registering a new user after checking the user and logs in.
    If no issues happen logs in new user, adds them to database and redirects to the mainpage
    """
    error_no_user = None
    form = LoginForm()
    verifier = ReVerify(loggin_logger)
    if form.validate_on_submit():
        if verifier.verify_string(form.password.data) and verifier.verify_string(form.username.data):
            user_db = User.query.filter_by(username=form.username.data).first()
            if user_db:  # check if user in database
                if werkzeug.security.check_password_hash(user_db.password,form.password.data):  # check if correct password
                    login_user(user_db)
                    loggin_logger.info(f"user {form.username.data} logged in correctly")
                    return redirect(url_for("indexEng"))
            else: 
                error_no_user = "No such user exists"
    return render_template("login.html", form=form, error_no_user = error_no_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('indexEng'))

@app.route('/desconectar')
@login_required
def desconectar():
    logout_user()
    return redirect(url_for('indexEs'))

@app.route('/delete')
@login_required
def delete():
    """
    Deletes the user from database when directed from user page in english
    """
    user_id = current_user.id
    logout_user()
    stmt = text('''DELETE FROM "users" WHERE id IN ('''+str(user_id)+");")
    db.session.execute(stmt)
    stmt = text('''DELETE FROM "orders" WHERE user_id IN ('''+str(user_id)+");")  
    db.session.execute(stmt)
    db.session.commit()
    return redirect(url_for('indexEng'))

@app.route('/eliminar')
@login_required
def eliminar():
    """
    Deletes the user from database when directed from user page in spanish
    """
    user_id = current_user.id
    logout_user()
    stmt = text('''DELETE FROM "users" WHERE id IN ('''+str(user_id)+");")
    db.session.execute(stmt)
    stmt = text('''DELETE FROM "orders" WHERE user_id IN ('''+str(user_id)+");")
    db.session.execute(stmt)
    db.session.commit()
    return redirect(url_for('indexEs'))

@app.route('/orders', methods=['POST', 'GET'])
@login_required
def orders():
    """
    Presents the user with their orders and allows them to delete them
    """
    user_id = current_user.id
    undelivered_orders = OrderViewer(db.session.query(Order).filter(
        and_(Order.user_id == user_id, Order.date > (datetime.date.today() - datetime.timedelta(days=1)))).all(), "en")
    delivered_orders = OrderViewer(db.session.query(Order).filter(
        and_(Order.user_id == user_id, Order.date < (datetime.date.today() - datetime.timedelta(days=1)))).all(), "en")
    form = DeleteForm()
    undelivered_orders.add_form(form)
    form.validate_on_submit()
    if form.validate_on_submit():
        for i in undelivered_orders:
            if undelivered_orders.form_data.data:
                db.session.delete(undelivered_orders.order_instance)
        db.session.commit()
        return redirect(url_for("orders"))
    return render_template("orders.html", form=form, delivered_orders=delivered_orders,undelivered_orders=undelivered_orders)


@app.route('/account', methods=['POST', 'GET'])
@login_required
def account():
    """
    Presents user with a way to change the inforamationif the user has their password and username in english
    """
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
            if werkzeug.security.check_password_hash(current_user.password, form.old_password.data):
                user.username = form.username.data
                user.email = form.email.data
                user.group = form.group.data
                if form.new_password.data:
                    user.password = generate_password_hash(str(form.new_password.data), method="pbkdf2:sha256",
                                                           salt_length=14)
                db.session.commit()
    return render_template("user.html", form=form, error1=error1, error2=error2, user_data=user_data)


@app.route('/baker')
@admin_required
def baker():
    """
    Admin page to see all orders and delete future ones
    """
    undelivered_orders = OrderViewer(db.session.query(Order).filter(
        and_(Order.date > (datetime.date.today()))).all(), "en")
    delivered_orders = OrderViewer(db.session.query(Order).filter(
        Order.date < (datetime.date.today())).all(), "en")
    today_orders = OrderViewer(db.session.query(Order).filter(
        Order.date == (datetime.date.today())).all(), "en")
    form = DeleteForm()
    undelivered_orders.add_form(form)
    form.validate_on_submit()
    if form.validate_on_submit():
        for i in undelivered_orders:
            if undelivered_orders.form_data.data:
                db.session.delete(undelivered_orders.order_instance)
        db.session.commit()
        return redirect(url_for("baker"))
    return render_template("admin.html", form=form, undelivered_orders=undelivered_orders, delivered_orders=delivered_orders,
                           today_orders=today_orders)

@app.route('/baker_users', methods=['POST', 'GET'])
@admin_required
def baker_users():
    """
    Admin page to control and allow the deleting of users by admin
    """
    users = db.session.query(User).all()
    form = DeleteUserForm()
    form.validate_on_submit()  
    if form.validate_on_submit():
        stmt = text('''DELETE FROM "users" WHERE id IN ('''+str(form.users_to_delete.data)+");")
        db.session.execute(stmt)
        stmt = text('''DELETE FROM "orders" WHERE user_id IN ('''+str(form.users_to_delete.data)+");")
        db.session.execute(stmt)
        db.session.commit()
        return redirect(url_for("baker_users"))   
    return render_template("admin_users.html", users = users,form = form)

# Spanish version
@app.route('/Es', methods=['POST', 'GET'])
def indexEs():
    return index("es")


@app.route('/registro', methods=['POST', 'GET'])
def registro():
    """
    Backend of spanish registering a new user after checking the email and user do not exist already in database.
    If no issues happen logs in new user, adds them to database and redirects to the mainpage
    """
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
                                                                                             method="pbkdf2:sha256",
                                                                                             salt_length=14),
                                group=form.group.data, address = form.address.data, email=form.email.data)
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                loggin_logger.info(f"user {form.username.data} from group {form.group.data} registered correctly")
                return redirect(url_for("indexEs"))
    return render_template("registro.html", form=form, error1=error1, error2=error2)


@app.route('/acceso', methods=['POST', 'GET'])
def acceso():
    """
    Page that allows user to log in to the account and get redirectod to main page in spanish
    """
    form = LoginForm()
    verifier = ReVerify(loggin_logger)
    error_no_user = None
    if form.validate_on_submit():
        if verifier.verify_string(form.password.data) and verifier.verify_string(form.username.data):
            user_db = User.query.filter_by(username=form.username.data).first()
            if user_db:  # check if user in database
                if werkzeug.security.check_password_hash(user_db.password,
                                                         form.password.data):  # check if correct password
                    login_user(user_db)
                    loggin_logger.info(f"user {form.username.data} logged in correctly")
                    return redirect(url_for("indexEs"))
            else: 
                error_no_user = "No existe ese usuario"
    return render_template("loginES.html", form=form, error_no_user= error_no_user)


@app.route('/pedidos', methods=['POST', 'GET'])
@login_required
def pedidos():
    """
    Page thath shows all orders the user has  done in spaninsh
    """
    user_id = current_user.id
    undelivered_orders = OrderViewer(db.session.query(Order).filter(
        and_(Order.user_id == user_id, Order.date > (datetime.date.today() - datetime.timedelta(days=1)))).all(), "es")
    delivered_orders = OrderViewer(db.session.query(Order).filter(
        and_(Order.user_id == user_id, Order.date < (datetime.date.today() - datetime.timedelta(days=1)))).all(), "es")
    form = DeleteForm()
    undelivered_orders.add_form(form)
    form.validate_on_submit()
    if form.validate_on_submit():
        for i in undelivered_orders:
            if undelivered_orders.form_data.data:
                db.session.delete(undelivered_orders.order_instance)
        db.session.commit()
        return redirect(url_for("pedidos"))
    return render_template("pedidos.html", form=form, delivered_orders=delivered_orders,
                           undelivered_orders=undelivered_orders)


@app.route('/usuario', methods=['POST', 'GET'])
@login_required
def usuario():
    """
    Presents user with a way to change the inforamationif the user has their password and username in spanish
    """
    form = ModifyUser()
    form.validate_on_submit()
    delete_form = DeleteForm()
    delete_form.validate_on_submit()
    error1 = None
    error2 = None
    user_data = {"user": current_user.username, "email": current_user.email, "group": current_user.group}
    if delete_form.validate_on_submit():
        user_id = current_user.id
        logout_user()
        stmt = text('''DELETE FROM "users" WHERE id IN ('''+str(user_id)+");")
        db.session.execute(stmt)
        stmt = text('''DELETE FROM "orders" WHERE user_id IN ('''+str(user_id)+");")
        db.session.execute(stmt)
        db.session.commit()
        return redirect(url_for("indexEs"))
    elif form.validate_on_submit():
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
            if werkzeug.security.check_password_hash(current_user.password, form.old_password.data):
                user.username = form.username.data
                user.email = form.email.data
                user.group = form.group.data
                if form.new_password.data:
                    user.password = generate_password_hash(str(form.new_password.data), method="pbkdf2:sha256",
                                                           salt_length=14)
                db.session.commit()
    return render_template("usuario.html", form=form, error1=error1, error2=error2, user_data=user_data)


# Run Stuff
if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
    
