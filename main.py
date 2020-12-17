# -*- coding: utf-8 -*-
"""
Created on Sun Dec  6 17:29:07 2020

@author: a-t-g
"""

import pyrebase
import json
from datetime import datetime

config = {
    "apiKey": "AIzaSyBdDxSy6n46GCRH3HtUtLJSeaIkBdY3tzc",
    "authDomain": "pinti-eca.firebaseapp.com",
    "databaseURL": "https://pinti-eca-default-rtdb.europe-west1.firebasedatabase.app",
    "projectId": "pinti-eca",
    "storageBucket": "pinti-eca.appspot.com",
    "messagingSenderId": "772617968614",
    "appId": "1:772617968614:web:5828afaf504bda0c38d427",
    "measurementId" : "G-D5QDC8WR09"
    }

firebase = pyrebase.initialize_app(config)

db = firebase.database()

from flask import Flask, request, jsonify,Response

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/create-user', methods=["GET"])
def createUser():
    name = request.args.get('name')
    email = request.args.get('email')
    profilephotoURL = request.args.get('profilephotourl')
    
    new_user = {
        "name" : name,
        "email" : email,
        "profilePhotoURL" : profilephotoURL
        }
    
    try:
        db.child("UserInfos").push(new_user)
        return {'success' : True}
    except:
        return {'success' : False}

@app.route('/find-user', methods=["GET"])
def findUser():
    email = request.args.get('email')
    user = db.child('UserInfos').order_by_child("email").equal_to(email).get()
    if type(user.val()) == list:
        return Response(status = 404)
    else:
        for u in user.each():
            return u.val()

@app.route('/add-product', methods=["GET"])
def createProduct():
    barcode = request.args.get('barcode',type=str)
    name = request.args.get('name')
    brand = request.args.get('brand')
    categoryId = request.args.get("categoryid")
    shopId = request.args.get("shopid")
    location = request.args.get("location")
    price = request.args.get("price",type=float)
    recordDate = request.args.get("recorddate")
    photoURL = request.args.get("photourl")
    
    product = db.child('Products').order_by_key().equal_to(barcode).get()
    
    new_record = {
        'barcode' : barcode,
        'shopId' : shopId,
        'location' : location,
        'price' : price,
        'recordDate' : recordDate
        }
    
    if type(product.val()) == list:
        new_product = {
            'name' : name,
            'brand' : brand,
            'categoryId' : categoryId,
            'photoURL' : photoURL
            }
        try:
            db.child('Products').child(barcode).set(new_product)
            db.child('Records').push(new_record)
            return {'success' : True}
        except:
            return {'success' : False}
    else:
        result = returnRecordId(shopId,barcode)
        if result != False:
            db.child('Records').child(result).remove()
            
        try:
            db.child('Records').push(new_record)
            return {'success' : True}
        except:
            return {'success' : False}

@app.route('/find-product', methods=["GET"])
def findProduct():
    barcode = request.args.get('barcode',type= str)
    product_dict = {}
    result = db.child('Products').get().val()
    result_records = db.child('Records').get().val()
    for val in result.keys():
            if val == barcode:
                product_dict[val] = result[val]
                
    for val in result_records.values():
            if val['barcode'] == barcode:
                product_dict[barcode]['Records'] = val
    return product_dict
        
@app.route('/get-records', methods=["GET"])
def getRecords():
    barcode = request.args.get('barcode',type= str)
    records = db.child('Records').order_by_child('barcode').equal_to(barcode).get()
    return records.val()
    
@app.route('/add-shop', methods=['GET'])
def addShop():
    shopName = request.args.get('shopname',type=str)
    shops = db.child('Shops').get().val()
    if shops is None:
        count = 0
    else:
        count = len(shops)
    
    try:
        db.child('Shops').child(str(count)).set(shopName)
        return {'success' : True}
    except:
        return {'success' : False}

@app.route('/add-category', methods=['GET'])
def addCategory():
    categoryName = request.args.get('categoryname',type=str)
    categories = db.child('Categories').get().val()
    if categories is None:
        count = 0
    else:
        count = len(categories)
    
    try:
        db.child('Categories').child(str(count)).set(categoryName)
        return {'success' : True}
    except:
        return {'success' : False}
    
@app.route('/fetch-categories', methods=['GET'])
def fetchCategories():
    categories = db.child('Categories').get()
    
    cat_dict = dict(enumerate(categories.val()))
    if type(categories.val()) == list:
            return cat_dict
    else:
        return {'success' : False}

@app.route('/fetch-shops', methods=['GET'])
def fetchShops():
    shops = db.child('Shops').get()
    
    shop_dict = dict(enumerate(shops.val()))
    if type(shops.val()) == list:
            return shop_dict
    else:
        return {'success' : False}
    
@app.route('/fetch-products-by-shop', methods=['GET'])
def fetchProductsByShop():
    shopId = request.args.get('shopid',type=str)
    barcode_list = []
    result = db.child("Records").order_by_child("shopId").equal_to(shopId).get().val()
    
    if type(result) != list:
        for val in result.values():
            if val['shopId'] == shopId:
                barcode_list.append(val['barcode'])
        product_list = barcodeToProduct(barcode_list)
        if not product_list:
            return {'success' : False}
        else:
            return product_list
    else:
        return {'success' : False}
        

@app.route('/fetch-products-by-category', methods=['GET'])
def fetchProductsByCategory():
    categoryId = request.args.get('categoryid',type=str)
    barcode_list = []
    result = db.child('Products').order_by_child('categoryId').equal_to(categoryId).get().val()
    if type(result) != list:
        for val in result.keys():
            barcode_list.append(val)
        product_list = barcodeToProduct(barcode_list)
        if not product_list:
            return {'success' : False}
        else:
            return product_list
    else:
        return {'success' : False}
    
@app.route('/fetch-last-products', methods=['GET'])
def fetchLastProducts():
    my_dict = {}
    my_list = []
    barcode_list = []
    result =  db.child('Records').get().val()
    if type(result) != list:
        for val in result.values():
            datetime_obj = datetime.strptime(val['recordDate'],'%d.%m.%Y')
            my_dict[val['barcode']] = datetime_obj
            
        my_list = sorted(my_dict.items(),key=lambda p: p[1],reverse=True)
        count = len(my_list)
        if count > 10:
            for i in range (0,10):
                barcode_list.append(my_list[i][0]) 
            products = barcodeToProduct(barcode_list)
        else:
            for i in range(0,count):
                barcode_list.append(my_list[i][0]) 
            products = barcodeToProduct(barcode_list)
        return json.dumps(products, indent=4)
            
    
def returnRecordId(shopId,barcode):
    result = db.child('Records').order_by_child('shopId').equal_to(shopId).get().val()
    if result != list:
        for k,v in result.items():
            if v['barcode'] == barcode:
                return k
            else:
                return False
    else: 
        return False
    
def barcodeToProduct(barcode_list):
    product_dict = {}
    result = db.child('Products').get().val()
    result_records = db.child('Records').get().val()
    for barcode in barcode_list:
        for val in result.keys():
            if val == barcode:
                product_dict[val] = result[val]
                
    for barcode in barcode_list:
        for val in result_records.values():
            if val['barcode'] == barcode:
                product_dict[barcode]['Records'] = val
    return product_dict

if __name__ == '__main__': 
    app.run(debug=True)