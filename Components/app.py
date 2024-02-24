from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from enum import Enum as PyEnum
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)

#chawin only dont change!!
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/chs/Desktop/flaskproject21/python-try/Components/instance/carvis.db'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carvis.db'
db = SQLAlchemy(app)
app.secret_key = 'eb3d197e1633fd5193f89ff8b2887923d12645b647a97893'


class UserLevels(PyEnum):
    BUYER_SELLER = 'Buyer/Seller'
    SALESPERSON = 'Salesperson'
    SUPERADMIN = 'Superadmin'


class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    user_level = db.Column(db.Enum(UserLevels), nullable=False)
    personal_info = db.relationship('PersonalInformation', backref='user', uselist=False)


class PersonalInformation(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), primary_key=True)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    address = db.Column(db.Text)


class CarModel(db.Model):
    model_id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(50))
    model = db.Column(db.String(50))
    year = db.Column(db.Integer)
    mileage = db.Column(db.Integer)
    price = db.Column(db.Numeric(10, 2))
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))  
    image_url_2 = db.Column(db.String(255))  
    image_url_3 = db.Column(db.String(255))  
    fuel_type = db.Column(db.Text)  
    safety_features = db.Column(db.Text)  
    additional_details = db.Column(db.Text) 


class Order(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    model_id = db.Column(db.Integer, db.ForeignKey('car_model.model_id'))
    order_date = db.Column(db.Date)
    total_price = db.Column(db.Numeric(10, 2))


class SalesHistory(db.Model):
    sale_id = db.Column(db.Integer, primary_key=True)
    salesperson_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    model_id = db.Column(db.Integer, db.ForeignKey('car_model.model_id'))
    sale_date = db.Column(db.Date)
    total_price = db.Column(db.Numeric(10, 2))


class Advertisement(db.Model):
    ad_id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('car_model.model_id'))
    ad_title = db.Column(db.String(255))
    ad_description = db.Column(db.Text)
    ad_expiry_date = db.Column(db.Date)
    is_new = db.Column(db.Boolean)


class Salesperson(db.Model):
    salesperson_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    commission_rate = db.Column(db.Numeric(5, 2))


class Superadmin(db.Model):
    superadmin_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))


class SalespersonCarModel(db.Model):
    salesperson_car_id = db.Column(db.Integer, primary_key=True)
    salesperson_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    model_id = db.Column(db.Integer, db.ForeignKey('car_model.model_id'))


@app.route('/create_account')
def show_create_account_form():
    return render_template('create_account.html')


# creating an account
@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    full_name = request.form['full_name']
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    address = request.form['address']
    phone_number = request.form['phone_number']
    user_level = request.form.get('user_level', 'Buyer/Seller')

    if password != confirm_password:
        return render_template('create_account.html', error="Passwords do not match.")

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return render_template('create_account.html', error="Username already exists.")

    hashed_password = generate_password_hash(password)
    user_level_enum = UserLevels(user_level)

    new_user = User(username=username, password=hashed_password, user_level=user_level_enum)
    db.session.add(new_user)
    db.session.flush()  # This assigns an ID to new_user without committing the transaction

    new_personal_info = PersonalInformation(
        user_id=new_user.user_id,
        full_name=full_name,
        email=email,
        phone_number=phone_number,
        address=address
    )
    db.session.add(new_personal_info)
    db.session.commit()
    print("User added")
    return redirect(url_for('login'))



@app.route('/login')
def show_login_account_form():
    return render_template('user_login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    print(username)
    print(password)

    existing_user = User.query.filter_by(username=username).first()
    if existing_user and check_password_hash(existing_user.password, password):
        session['username'] = username
        if existing_user.user_level == UserLevels.BUYER_SELLER:
            return redirect(url_for('homepage'))
        else:
            return redirect(url_for('show_dashboard_form'))
    
    
    return render_template('user_login.html', error="Username and Password dont match")


@app.route('/logout')
def logout():
    # Clear session
    session.pop('username', None)
    return redirect(url_for('show_login_account_form'))

@app.route('/dashboard')
def show_dashboard_form():
    if 'username' in session:
        current_user = User.query.filter_by(username=session["username"]).first()
        return render_template('dashboard.html', user_name=current_user.username,  user_role=current_user.user_level)
    return render_template('user_login.html')

@app.route('/admindashboard')
def show_admin_dashboard_form():
    if 'username' in session:
        current_user = User.query.filter_by(username=session["username"]).first()
        if current_user.user_level.name == "SUPERADMIN":
            user_list = []
            users = User.query.all()
            for user in users:
                user_info = PersonalInformation.query.filter_by(user_id=user.user_id).first()
                user_list.append({"username" : user.username ,"email" : user_info.email})

            print(user_list[0])

            return render_template('admin_dashboard2.html', user_name=current_user.username, users=user_list) #Just testing
        else:
            return render_template("forbidden.html"), 403
    return render_template('user_login.html')


@app.route('/homepage', methods=['GET', 'POST'])
def homepage():
    if 'username' in session:
        current_user = User.query.filter_by(username=session["username"]).first()
        if current_user.user_level == UserLevels.BUYER_SELLER:
            ads_with_cars = db.session.query(
                Advertisement,
                CarModel.make,
                CarModel.model,
                CarModel.year,
                CarModel.mileage,
                CarModel.price,
                CarModel.image_url
            ).join(CarModel, Advertisement.model_id == CarModel.model_id).all()
            return render_template('homepage.html', ads_with_cars=ads_with_cars)
        else:
            return render_template('user_login.html')
    else:
        return render_template('user_login.html')

@app.route('/ad/<int:ad_id>')
def ad_detail(ad_id):
    advertisement = Advertisement.query.get_or_404(ad_id)
    car_model = CarModel.query.get(advertisement.model_id)
    return render_template('ad_detail.html', advertisement=advertisement, car_model=car_model)

#@app.route('/car-images')
    #def car_images():
    # Fetch all car model image URLs as a list of strings
    #  car_images = [url for (url,) in CarModel.query.with_entities(CarModel.image_url).all()]
   # return render_template('car_images.html', car_images=car_images)

@app.route('/agentdashboard')
def agentdashboard():
    return render_template('agentDisplay.html')

@app.route('/account')
def account():
    return render_template('account.html')

@app.route('/superadmindashboard')
def superadmindashboard():
    return render_template('superadmin_dashboard.html')

@app.route('/sellerview')
def sellerview():
    return render_template('sellerview.html')

@app.route('/changepassword')
def changepassword():
    return render_template('changePassword.html')

@app.route('/confirmpassword')
def confirmpassword():
    return render_template('passwordConfirm.html')

@app.route('/buyerask')
def buyerask():
    return render_template('buyernegotiation.html')

@app.route('/askconfirm')
def askconfirm():
    return render_template('negotiationconfirm.html')

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

if __name__ == '__main__':
    app.run(debug=True)



