from flask import Flask, render_template
from flask import request, url_for, redirect, jsonify, flash
from flask import session as login_session
from flask import make_response

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, exists
from database_setup import *

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

import datetime
import random
import string
import httplib2
import json
import requests
from functools import wraps

app = Flask(__name__)
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# Create session
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create a state token to prevent request forgery
# Store it in the session for later validation
@app.route('/login')
def showLogin():
    state = ''.join(
                random.choice(string.ascii_uppercase + string.digits)
                for x in range(32))
    login_session['state'] = state
    return render_template("login.html", STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1].decode('utf-8'))
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
                    json.dumps('Current user is already connected.'),
                    200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    uid = createUser(login_session)
    login_session['user_id'] = uid

    return render_template("welcome.html", login_session=login_session)

    # DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print(result)

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']

        flash('Successfully disconnected.')
        return redirect(url_for('show_home'))

    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# User info operations
def createUser(login_session):
    exist = session.query(
                exists().where(User.gid == login_session['gplus_id'])).scalar()
    if not exist:
        newUser = User(
                gid=login_session['gplus_id'],
                name=login_session['username'],
                email=login_session['email'],
                picture=login_session['picture'])
        session.add(newUser)
        session.commit()

    user = session.query(User).filter_by(gid=login_session['gplus_id']).one()
    return user.id


def getUserInfo(gplus_id):
    user = session.query(User).filter_by(gid=login_session['gplus_id']).one()
    return user


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        if 'username' not in login_session:
            return redirect('/login')
        return f(*args, **kwds)
    return wrapper


# Home page
@app.route('/')
@app.route('/catalog')
@app.route('/catalog/')
def show_home():
    categories = session.query(Category).order_by(Category.name).all()
    latest_items = session.query(Item).order_by(Item.date.desc()).all()
    return render_template(
            "index.html",
            categories=categories,
            items=latest_items,
            name="Latest")


# All items of a category
@app.route('/catalog/<string:category_name>')
def show_category(category_name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=category_name).first()
    citems = session.query(Item).filter_by(category_id=category.id)
    return render_template("index.html", categories=categories,
                           items=citems, name=category.name)


# Display a item description
@app.route('/catalog/<string:category_name>/<string:item_name>')
def show_item(category_name, item_name):
    item = session.query(Item).filter_by(name=item_name).first()
    isowner = False
    if 'user_id' in login_session:
        isowner = item.user_id == login_session['user_id']

    return render_template("display_item.html", item=item, isowner=isowner)


# Edit an item
@app.route('/catalog/<string:category_name>/<string:item_name>/edit',
           methods=['GET', 'POST'])
@login_required
def edit_item(category_name, item_name):
    if request.method == 'POST':
        category = session.query(Category) \
            .filter(Category.name == category_name) \
            .first()
        item = session.query(Item) \
            .filter(Item.category_id == category.id, Item.name == item_name) \
            .first()
        new_category_name = request.form['category']
        new_category = session.query(Category) \
            .filter(Category.name == new_category_name) \
            .first()
        item.name = request.form['name']
        item.description = request.form['description']
        item.category_id = new_category.id
        session.add(item)
        session.commit()
        return redirect(url_for('show_home'))
    else:
        categories = session.query(Category).all()
        category = session.query(Category) \
            .filter(Category.name == category_name) \
            .first()
        item = session.query(Item) \
            .filter(Item.category_id == category.id, Item.name == item_name) \
            .first()
        print(item_name)
        return render_template(
                'edit_item.html',
                categories=categories,
                name=item.name,
                description=item.description,
                selected=category_name)


# Add item
@app.route('/catalog/additem', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        name = request.form['category']
        category = session.query(Category).filter_by(name=name).first()
        new_item = Item(name=request.form['name'],
                        description=request.form['description'],
                        date=datetime.datetime.now(),
                        user_id=login_session['user_id'],
                        category_id=category.id)
        session.add(new_item)
        session.commit()
        return redirect(url_for('show_home'))
    else:
        categories = session.query(Category).all()
        return render_template('add_item.html', categories=categories)


# Delete an item
@app.route(
    '/catalog/<string:category_name>/<string:item_name>/delete',
    methods=['GET', 'DELETE'])
@login_required
def delete_item(category_name, item_name):
    if request.method == 'DELETE':
        item = session.query(Item).filter_by(name=item_name).one()
        session.delete(item)
        session.commit()
        return redirect(url_for('show_home'))
    else:
        return render_template('delete_item.html')


# Add a category
@app.route('/catalog/addcategory', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        name = request.form['category_name']
        category = Category(name=name, user_id=login_session['user_id'])
        session.add(category)
        session.commit()
        return redirect(url_for('show_home'))
    else:
        return render_template('category_name.html', action_name='Add')


# Rename a category
@app.route('/catalog/<string:category_name>/rename', methods=['GET', 'POST'])
@login_required
def rename_category(category_name):
    if request.method == 'POST':
        category = session.query(Category) \
                    .filter(Category.name == category_name) \
                    .one()
        category.name = request.form['category_name']
        session.add(category)
        session.commit()
        return redirect(url_for('show_home'))
    else:
        return render_template(
                'category_name.html',
                action_name='Rename',
                name=category_name)


# Delete a category
@app.route('/catalog/<string:category_name>/delete', methods=['GET', 'DELETE'])
@login_required
def delete_category(category_name):
    if request.method == 'DELETE':
        print(category_name)
        category = session.query(Category) \
            .filter(Category.name == category_name) \
            .one()
        session.delete(category)
        session.commit()
        return redirect(url_for('show_home'))
    else:
        return render_template('delete_category.html')


# JSON End Points

# full details
@app.route('/catalog/JSON')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(catalog=[i.serialize for i in categories])


# items uder this category
@app.route('/catalog/<string:category_name>/JSON')
def categoryJSON(category_name):
    try:
        cat = session.query(Category).filter_by(name=category_name).one()
        if cat:
            return jsonify(category_name=cat.serialize)
    except:
        return "{'message': 'Not found'}"


# JSON of an item
@app.route('/catalog/<string:category_name>/<string:item_name>/JSON')
def itemJSON(category_name, item_name):
    try:
        cat = session.query(Category) \
            .filter_by(name=category_name).one()
        item = session.query(Item) \
            .filter_by(name=item_name, category_id=cat.id) \
            .one()
        if item:
            return jsonify(item_name=item.serialize)
    except:
        return "{'message': 'Not found'}"


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='127.0.0.1', port=9090)
