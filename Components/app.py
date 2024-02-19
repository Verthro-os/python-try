from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from enum import Enum as PyEnum
from werkzeug.security import generate_password_hash


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carvis.db'
db = SQLAlchemy(app)

class UserLevels(PyEnum):
    BUYER_SELLER='Buyer/Seller'
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

#creating an account
@app.route('/create_account', methods=['GET','POST'])    
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
    print ("User added")
    return redirect(url_for('show_create_account_form'))


@app.route('/homepage', methods=['GET','POST'])
def homepage():
    # Joining CarModel and Advertisement tables to fetch all necessary details
    car_ads = db.session.query(
        CarModel,
        Advertisement.is_new
    ).join(Advertisement, CarModel.model_id == Advertisement.model_id).all()

    return render_template('homepage.html', car_ads=car_ads)

if __name__ == '__main__':
    app.run(debug=True)