# Catalog-App

## Description
Keyword: Python Flask Jinja3 SQLAlchemy SQL CRUD
<br>
This is an application that provides a list of items within a variety of 
categories as well as provide a user registration and authentication system. 
Registered users will have the ability to post, edit and delete their own items.

## Build Requirements
- python 3.5.4
- Flask 0.11.1
- SQLAlchemy 1.0.13

## Setup & Run
1. Setup Database
```
$ python database_setup.py
```
2. Add sample data (optional)
```
$ python database_sample.py
```
3. Run server
```
$ python catalog.py
```
4. Visit [localhost:9090](localhost:9090) in browser
5. Make sure to login to modify content

## URLs & API Endpoints
```
# login page
/login
# home page
/catalog
# show items of specific category
/catalog/<string:category_name>
# display specific item
/catalog/<string:category_name>/<string:item_name>
# edit specific item
/catalog/<string:category_name>/<string:item_name>/edit
# add an item
/catalog/additem
# delete an item
/catalog/<string:category_name>/<string:item_name>/delete
# add a category
/catalog/addcategory
# rename a category
/catalog/<string:category_name>/rename
# delete a category
/catalog/<string:category_name>/delete

# API Endpoints
# JSON of all catalog data
/catalog/JSON
# JSON of a category
/catalog/<string:category_name>/JSON
# JSON of an item
/catalog/<string:category_name>/<string:item_name>/JSON
```

