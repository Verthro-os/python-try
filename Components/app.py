import os
import time

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from enum import Enum as PyEnum
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)

UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# chawin only dont change!!
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/chs/Desktop/flaskproject21/python-try/Components/instance/carvis.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users\Verty\Documents\python try\Components\instance\carvis.db' #Mickey Test
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'), primary_key=True)
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'))
    model_id = db.Column(db.Integer, db.ForeignKey('car_model.model_id', ondelete='CASCADE'))
    ad_id = db.Column(db.Integer, db.ForeignKey('advertisement.ad_id', ondelete='CASCADE'))
    order_date = db.Column(db.Date)
    total_price = db.Column(db.Numeric(10, 2))
    negotiated_price = db.Column(db.Numeric(10, 2))
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    country = db.Column(db.String(50))
    order_status = db.Column(db.Integer, default=1)  # Assuming default is 'pending'

    # Relationships
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    car_model = db.relationship('CarModel', backref=db.backref('orders', lazy=True))
    advertisement = db.relationship('Advertisement', backref=db.backref('orders', lazy=True))


class SalesHistory(db.Model):
    sale_id = db.Column(db.Integer, primary_key=True)
    salesperson_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'))
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'))
    model_id = db.Column(db.Integer, db.ForeignKey('car_model.model_id', ondelete='CASCADE'))
    sale_date = db.Column(db.Date)
    total_price = db.Column(db.Numeric(10, 2))


class Advertisement(db.Model):
    ad_id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('car_model.model_id', ondelete='CASCADE'))
    ad_title = db.Column(db.String(255))
    ad_description = db.Column(db.Text)
    ad_expiry_date = db.Column(db.Date)
    is_new = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'))
    is_hidden = db.Column(db.Boolean)


class Salesperson(db.Model):
    salesperson_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'))
    commission_rate = db.Column(db.Numeric(5, 2))


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
        elif existing_user.user_level == UserLevels.SUPERADMIN:
            return redirect(url_for('homepage'))
        else:
            return redirect(url_for('account'))

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
        return render_template('dashboard.html', user_name=current_user.username, user_role=current_user.user_level)
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
                if user.user_level.name == "SALESPERSON":
                    user_list.append(
                        {"username": user.username, "email": user_info.email, "fullname": user_info.full_name})
            if len(user_list) > 0:
                return render_template('admin_dashboard2.html', user_name=current_user.username,
                                       users=user_list)  # Just testing
            else:
                return render_template('admin_dashboard2.html', user_name=current_user.username, users=user_list,
                                       no_users=True)
        else:
            return render_template("forbidden.html"), 403
    return render_template('login.html')


@app.route('/deleteuser/<string:username>')
def delete_user(username):
    if 'username' in session:
        current_user = User.query.filter_by(username=session["username"]).first()
        if current_user.user_level.name == "SUPERADMIN":
            del_user = User.query.filter_by(username=username).first()
            print("USERID -> " + str(del_user.user_id))

            PersonalInformation.query.filter_by(user_id=del_user.user_id).delete()
            Advertisement.query.filter_by(model_id=del_user.user_id).delete()
            Salesperson.query.filter_by(salesperson_id=del_user.user_id).delete()

            db.session.delete(del_user)
            db.session.commit()

            return show_admin_dashboard_form()
    return render_template("forbidden.html"), 403


@app.route('/create_account_salesperson')
def show_create_account_salesperson():
    return render_template('create_account_salesperson.html')


@app.route('/create_account_salesperson', methods=['GET', 'POST'])
def create_account_salesperson():
    full_name = request.form['full_name']
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    address = request.form['address']
    phone_number = request.form['phone_number']
    user_level = request.form.get('user_level', 'Salesperson')

    if password != confirm_password:
        return render_template('create_account_salesperson.html', error="Passwords do not match.")

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return render_template('create_account_salesperson.html', error="Username already exists.")

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
    print("Salesperson added")
    return redirect(url_for('show_admin_dashboard_form'))


@app.route('/changepassword', methods=['POST'])
def change_password():
    if 'username' in session:
        current_user = User.query.filter_by(username=session["username"]).first()
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password == confirm_password:
            if check_password_hash(current_user.password, new_password):
                return render_template('changePassword.html', error="Please enter a new Password")
            else:
                hashed_password = generate_password_hash(new_password)
                current_user.password = hashed_password
                db.session.commit()
                flash('Password Changed', 'success')
                return render_template('changePassword.html')
                # return redirect(url_for('homepage'))
        else:
            return render_template('changePassword.html', error="Passwords dont match")


@app.route('/add_car_advertisement', methods=['POST'])
def add_car_advertisement():
    current_user = User.query.filter_by(username=session["username"]).first()

    car_name = request.form['car_name']
    car_made = request.form['car_made']
    price = request.form['price']
    car_overview = request.form['car_overview']

    if 'mileage' in request.form:
        mileage = request.form['mileage']
    else:
        mileage = "0"

    fuel_economy = request.form['fuel_economy']

    if 'year_of_produce' in request.form:
        year_of_produce = request.form['year_of_produce']  # Be
    else:
        current_year = datetime.now().year
        year_of_produce = current_year

    if 'car_images' in request.files:
        images = request.files.getlist('car_images')
        if len(images) != 3:
            return redirect(url_for('account'))
        for image in images:
            print(image.filename)
            if image.filename != '':
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))

    split_items = car_overview.split(",")
    first_string = split_items[0]
    second_string = split_items[1]

    new_car = CarModel(
        make=car_made,
        model=car_name,
        year=year_of_produce,
        mileage=mileage,
        price=price,
        description=car_overview,  # First Safety Features, then additioanl
        image_url="images/" + images[0].filename,
        image_url_2="images/" + images[1].filename,
        image_url_3="images/" + images[2].filename,
        fuel_type=fuel_economy,
        safety_features=first_string,
        additional_details=second_string
    )

    db.session.add(new_car)
    db.session.flush()
    db.session.commit()

    if new_car.mileage == 0 and new_car.year == datetime.now().year:
        is_new = True
    else:
        is_new = False

    new_ad = Advertisement(
        model_id=new_car.model_id,
        ad_title=car_made + "  " + car_name,
        ad_description=first_string + "-" + second_string,
        ad_expiry_date=datetime.strptime("2024-12-12", '%Y-%m-%d').date(),  # Convert to datetime object
        is_new=is_new,
        user_id=current_user.user_id,
        is_hidden=False

    )
    db.session.add(new_ad)
    db.session.commit()

    flash('Your car has been added', 'success')

    return redirect(url_for('account'))


@app.route('/show_my_advertisements')
def show_my_advertisements():
    if 'username' in session:
        current_user = User.query.filter_by(username=session["username"]).first()
        entries = Advertisement.query.filter_by(user_id=current_user.user_id).all()
        advertisements = []
        no_advertisements = False

        for entry in entries:
            if not entry.is_hidden:
                advertisements.append({"title": entry.ad_title, "id": entry.ad_id, "condition": entry.is_new,
                                       "expire": entry.ad_expiry_date})
        if len(advertisements) == 0:
            no_advertisements = True
    # for ad in advertisements
    return render_template('show_my_advertisements.html', advertisements=advertisements,
                           no_advertisements=no_advertisements)


@app.route('/delete_ad/<int:advertisement_id>', methods=['POST'])
def delete_offer(advertisement_id):
    advertisement = Advertisement.query.filter_by(ad_id=advertisement_id).first()

    advertisement.is_hidden = True

    db.session.commit()

    flash("Advertisement Deleted", "success")

    return redirect(url_for('show_my_advertisements'))


@app.route('/show_my_received_offers')
def show_my_received_offers():
    if 'username' in session:
        current_user = User.query.filter_by(username=session["username"]).first()
        advertisements = Advertisement.query.filter_by(user_id=current_user.user_id).all()
        current_orders = []
        print(len(advertisements))

        for ad in advertisements:
            print(ad.ad_title)
            active_orders = Order.query.filter_by(ad_id=ad.ad_id).filter_by(order_status=1).all()
            for order in active_orders:
                linked_car = CarModel.query.filter_by(model_id=ad.model_id).first()
                order_name = order.name
                oder_date = order.order_date
                oder_price = order.negotiated_price
                order_title = ad.ad_title
                order_condition = ad.is_new
                current_orders.append({"name": order_name, "date": oder_date, "price": linked_car.price, "orderprice" : oder_price,
                                       "title": order_title, "condition": order_condition, "id" : order.order_id})

    return render_template('show_my_received_offers.html', orders=current_orders)



@app.route('/reject_offer/<int:offer_id>', methods=['POST'])
def reject_offer(offer_id):
    offer = Order.query.filter_by(order_id=offer_id).first();

    offer.order_status=3

    db.session.commit()

    flash("Offer Rejected", "success")

    return redirect(url_for('show_my_received_offers'))




@app.route('/accept_offer/<int:offer_id>', methods=['POST'])
def accept_offer(offer_id):
    offer = Order.query.filter_by(order_id=offer_id).first();

    offer.order_status=2

    db.session.commit()

    flash("Offer Accepted", "success")

    return redirect(url_for('show_my_received_offers'))


@app.route('/homepage', methods=['GET', 'POST'])
def homepage():
    if 'username' in session:
        current_user = User.query.filter_by(username=session["username"]).first()
        if current_user.user_level == UserLevels.BUYER_SELLER or current_user.user_level == UserLevels.SALESPERSON:
            ads_with_cars = db.session.query(
                Advertisement,
                CarModel.make,
                CarModel.model,
                CarModel.year,
                CarModel.mileage,
                CarModel.price,
                CarModel.image_url
            ).join(CarModel, Advertisement.model_id == CarModel.model_id).filter(Advertisement.is_hidden == False).all()
            return render_template('homepage.html', ads_with_cars=ads_with_cars)
        else:
            return render_template('user_login.html')
    else:
        return render_template('user_login.html')


@app.route('/ad/<int:ad_id>', methods=['GET', 'POST'])
def ad_detail(ad_id):
    if 'username' in session:
        current_user = User.query.filter_by(username=session["username"]).first()
        if current_user and current_user.user_level == UserLevels.BUYER_SELLER or current_user.user_level == UserLevels.SALESPERSON:
            advertisement = Advertisement.query.get_or_404(ad_id)
            car_model = CarModel.query.get_or_404(advertisement.model_id)

            if request.method == 'POST':
                name = request.form['name']
                email = request.form['email']
                country = request.form['country']
                bank_account = float(request.form.get('bank_account', 0))

                # Determine the price to check against the bank account
                asking_price = float(car_model.price)
                negotiated_price = None  # Default value

                if not advertisement.is_new:
                    negotiated_price = float(request.form.get('negotiation_price', 0) or 0)
                    price_to_check = negotiated_price if negotiated_price else asking_price
                else:
                    price_to_check = asking_price

                # Check if the bank account covers the price
                if bank_account < price_to_check:
                    flash("Insufficient funds in the bank account for this purchase.", "error")
                else:
                    # Only create and save the order if there are no errors
                    new_order = Order(
                        user_id=current_user.user_id,
                        model_id=car_model.model_id,
                        ad_id=advertisement.ad_id,
                        order_date=datetime.utcnow(),
                        total_price=asking_price,
                        negotiated_price=negotiated_price,
                        name=name,
                        email=email,
                        country=country,
                        order_status=1
                    )
                    db.session.add(new_order)
                    db.session.commit()
                    flash("Order successfully created!", "success")

            fuel_type_details = car_model.fuel_type.split(",") if car_model.fuel_type else []
            return render_template(
                'ad_detail.html',
                advertisement=advertisement,
                car_model=car_model,
                fuel_type_details=fuel_type_details
            )
    else:
        flash('You must be logged in as a buyer or seller to view this page.')
        return redirect(url_for('user_login'))


@app.route('/update_personal_info', methods=['POST'])
def update_personal_info():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=username).first()
    if not user:
        return redirect(url_for('login'))

    personal_info = PersonalInformation.query.filter_by(user_id=user.user_id).first()
    if not personal_info:
        return redirect(url_for('account'))

    personal_info.full_name = request.form['full_name']
    personal_info.email = request.form['email']
    personal_info.address = request.form['address']

    try:
        db.session.commit()

    except Exception as e:
        db.session.rollback()

        app.logger.error(f'Error updating personal info: {e}')

    return redirect(url_for('account'))


@app.route('/agentdashboard')
def agentdashboard():
    return render_template('agentDisplay.html')


@app.route('/account', methods=['GET'])
def account():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=username).first()
    if not user:
        return redirect(url_for('login'))

    personal_info = PersonalInformation.query.filter_by(user_id=user.user_id).first()
    if not personal_info:
        # If no PersonalInformation exists, return a 404 error
        abort(404)

    orders = Order.query.filter_by(user_id=user.user_id).join(Advertisement, Advertisement.ad_id == Order.ad_id).join(
        CarModel, CarModel.model_id == Order.model_id).order_by(Order.order_date.desc()).limit(5).all()
    # Render the account page with the current user info
    return render_template('account.html', user=user, personal_info=personal_info, orders=orders,
                           user_role=user.user_level.name)


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


# with app.app_context():  #Just on Inital RUN

#    db.create_all()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
