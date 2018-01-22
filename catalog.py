from flask import Flask, render_template, request, url_for, redirect, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import *

# import requests
import datetime


# Create session
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Home page
@app.route('/')
@app.route('/catalog')
@app.route('/catalog/')
def show_home():
    categories = session.query(Category).order_by(Category.name).all()
    latest_items = session.query(Item).order_by(Item.date.desc()).all()
    return render_template("index.html", 
                            categories=categories, 
                            items=latest_items,
                            name="Latest")

# All items of a category
@app.route('/catalog/<string:category_name>')
def show_category(category_name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=category_name).first()
    print category.id
    citems = session.query(Item).filter_by(category_id=category.id)
    return render_template("index.html", categories=categories,
                           items=citems, name=category.name)
    

# Display a item description
@app.route('/catalog/<string:category_name>/<string:item_name>')
def show_item(category_name, item_name):
    item = session.query(Item).filter_by(name=item_name).first()
    owner = True
    return render_template("display_item.html", item=item, isowner=owner)


# Edit an item
@app.route('/catalog/<string:category_name>/<string:item_name>/edit',
           methods=['GET', 'POST'])
def edit_item(category_name, item_name):
    if request.method == 'POST':
        category = session.query(Category).filter(Category.name == category_name).first()
        item = session.query(Item).filter(Item.category_id == category.id, Item.name == item_name).first()
        new_category_name = request.form['category']
        new_category = session.query(Category).filter(Category.name == new_category_name).first()
        item.name = request.form['name']
        item.description = request.form['description']
        item.category_id = new_category.id
        session.add(item)
        session.commit()
        return redirect(url_for('show_home'))
    else:
        categories = session.query(Category).all()
        category = session.query(Category).filter(Category.name == category_name).first()
        item = session.query(Item).filter(Item.category_id == category.id, Item.name == item_name).first()
        print(item_name)
        return render_template('edit_item.html', categories=categories,
                                name=item.name,
                                description=item.description,
                                selected=category_name)


# Add item
@app.route('/catalog/additem', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        name = request.form['category']
        category = session.query(Category).filter_by(name=name).first()
        new_item = Item(name=request.form['name'],
                        description=request.form['description'],
                        date=datetime.datetime.now(),
                        user_id=1,
                        category_id=category.id)
        session.add(new_item)
        session.commit()
        return redirect(url_for('show_home'))
    else:
        categories = session.query(Category).all()
        return render_template('add_item.html', categories=categories)


# Delete an item
@app.route('/catalog/<string:category_name>/<string:item_name>/delete',
            methods=['GET', 'POST'])
def delete_item(category_name, item_name):
    if request.method == 'POST':
        item = session.query(Item).filter_by(name=item_name).one()
        session.delete(item)
        session.commit()
        return redirect(url_for('show_home'))
    else:
        print('delete_item')
        return render_template('delete_item.html')


# Add a category
@app.route('/catalog/addcategory', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        name = request.form['category_name']
        print name
        category = Category(name=name, user_id=1)
        session.add(category)
        session.commit()
        return redirect(url_for('show_home'))
    else:
        return render_template('category_name.html', action_name='Add')


# Rename a category
@app.route('/catalog/<string:category_name>/rename', methods=['GET', 'POST'])
def rename_category(category_name):
    if request.method == 'POST':
        category = session.query(Category).filter(Category.name == category_name).one()
        category.name = request.form['category_name']
        session.add(category)
        session.commit()
        return redirect(url_for('show_home'))
    else:
        return render_template('category_name.html', action_name='Rename', name=category_name)


# Delete a category
@app.route('/catalog/<string:category_name>/delete', methods=['GET', 'POST'])
def delete_category(category_name):
    if request.method == 'POST':
        print(category_name)
        category = session.query(Category).filter(Category.name == category_name).one()
        session.delete(category)
        session.commit()
        return redirect(url_for('show_home'))
    else:
        return render_template('delete_category.html')

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)