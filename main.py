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


from flask import Flask, request,Response

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

#OKEY
@app.route('/create-user', methods=["GET"])
def createUser():
    uid = request.args.get('uid')
    name = request.args.get('name')
    email = request.args.get('email')
    profilephotoURL = request.args.get('profilephotourl')
    
    new_user = {
        "uid" : uid,
        "name" : name,
        "email" : email,
        "profilePhotoURL" : profilephotoURL
        }
    
    try:
        db.child("UserInfos").push(new_user)
        return {'success' : True}
    except:
        return {'success' : False}

#FAİL
@app.route('/find-user', methods=["GET"])
def findUser():
    uid = request.args.get('uid')
    user = db.child('UserInfos').order_by_child("uid").equal_to(uid).get()
    if type(user.val()) == list:
        return Response(status = 404)
    else:
        for u in user.each():
            return u.val()

#2ye ayır
@app.route('/add-product', methods=["GET"])
def createProduct():
    barcode = request.args.get('barcode',type=str)
    name = request.args.get('name')
    brand = request.args.get('brand')
    categoryId = request.args.get("categoryid")
    photoURL = request.args.get("photourl")
    
    product = db.child('Products').order_by_key().equal_to(barcode).get()
    
    
    if type(product.val()) == list:
        new_product = {
            'name' : name,
            'brand' : brand,
            'categoryId' : categoryId,
            'photoURL' : photoURL
            }
        try:
            db.child('Products').child(barcode).set(new_product)
            return {'success' : True}
        except:
            return {'success' : False}
    else:
            return {'success' : False}

@app.route('/delete-product',methods=["GET"])
def deleteProduct():
    barcode = request.args.get('barcode')
    product = db.child('Products').child(barcode).remove()
    records = db.child('Records').order_by_child('barcode').equal_to(barcode).get().val()
    for record in records:
        db.child('Records').child(record).remove()
    return {'success': True}

@app.route('/delete-record',methods=["GET"])
def deleteRecord():
    shopId = request.args.get('shopid')
    barcode = request.args.get('barcode')
    records = db.child('Records').order_by_child('barcode').equal_to(barcode).get().val()
    if isinstance(records,dict):
        for k,v in records.items():
            for key,val in v.items():
                if key == 'shopId':
                    if val == shopId:
                        db.child('Records').child(k).remove()
        return {'success': True}
    else:
        return {'success':False}
    

@app.route('/delete-records',methods=["GET"])
def deleteRecords():
    barcode = request.args.get('barcode')
    records = db.child('Records').order_by_child('barcode').equal_to(barcode).get().val()
    if isinstance(records,dict):
        for record in records:
            db.child('Records').child(record).remove()   
        return {'success': True}
    else:
        return {'success':False}

@app.route('/add-record',methods=['GET'])
def addRecord():
    barcode = request.args.get('barcode',type=str)
    ownerId = request.args.get('ownerid',type=str)
    ownerName = request.args.get('ownername',type=str)
    shopId = request.args.get("shopid",type=str)
    locationTitle = request.args.get("locationtitle")
    locationCoordinate = request.args.get("locationcoordinate")
    price = request.args.get("price",type=float)
    recordDate = request.args.get("recorddate")
    
    new_record = {
        'barcode':barcode,
        'ownerId':ownerId,
        'ownerName':ownerName,
        'shopId':shopId,
        'locationTitle':locationTitle,
        'locationCoordinate':locationCoordinate,
        'price':price,
        'recordDate':recordDate
        }
    
    result = returnRecordId(shopId,barcode)
    if result != False:
        db.child('Records').child(result).remove()
    
    try:
        db.child('Records').push(new_record)
        return {'success' : True}
    except:
        return {'success' : False}
    

#OKEY
@app.route('/find-product', methods=["GET"])
def findProduct():
    barcode = request.args.get('barcode',type= str)
    product = barcodeToProduct([barcode])
    return json.dumps(product, indent=4,ensure_ascii=False)

@app.route('/search-product',methods=['GET'])
def searchProduct():
    name = request.args.get('name',type= str)
    if not name:
        return json.dumps(list())
    barcode_list = []
    products = db.child('Products').get().val()
    for key,value in products.items():
        for k,v in value.items():
            if 'name' in k:
                v = v.lower()
                if name in v:
                    barcode_list.append(key)
    
    product_list = barcodeToProduct(barcode_list)
    return json.dumps(product_list, indent=4,ensure_ascii=False)
            

 #OKEY 
@app.route('/add-shop', methods=['GET'])
def addShop():
    shopName = request.args.get('shopname',type=str)
    photoURL = request.args.get('photourl',type=str)
    
    shops = db.child('Shops').get().val()
    
    if shops is None:
        count = 0
    else:
        count = len(shops)
    
    new_shop = {
        "shopId" : str(count),
        "shopName" : shopName,
        "photoURL" : photoURL
        }
    try:
        db.child('Shops').child(str(count)).set(new_shop)
        return {'success' : True}
    except:
        return {'success' : False}

#OKEY
@app.route('/add-category', methods=['GET'])
def addCategory():
    categoryName = request.args.get('categoryname',type=str)
    photoURL = request.args.get('photourl',type=str)
    
    categories = db.child('Categories').get().val()
    if categories is None:
        count = 0
    else:
        count = len(categories)
    
    new_cat = {
        "categoryId" : str(count),
        "categoryName" : categoryName,
        "photoURL" : photoURL,
        }
    try:
        db.child('Categories').child(str(count)).set(new_cat)
        return {'success' : True}
    except:
        return {'success' : False}
    
#OKEY
@app.route('/fetch-categories', methods=['GET'])
def fetchCategories():
    categories = db.child('Categories').get().val()
    
    if type(categories) == list:
            return json.dumps(categories, indent=4,ensure_ascii=False)
    else:
        return json.dumps(list())

#OKEY
@app.route('/fetch-shops', methods=['GET'])
def fetchShops():
    shops = db.child('Shops').get().val()
    
    if type(shops) == list:
            return json.dumps(shops,indent=4,ensure_ascii=False)
    else:
        return json.dumps(list())
 
#OKEY
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
            return json.dumps(list())
        else:
            return json.dumps(product_list, indent=4,ensure_ascii=False)
    else:
        return json.dumps(list())
        

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
            return json.dumps(list())
        else:
            return json.dumps(product_list, indent=4,ensure_ascii=False)
    else:
        return json.dumps(list())
    
@app.route('/fetch-last-products', methods=['GET'])
def fetchLastProducts():
    count = request.args.get('count',type=int,default = 10)
    count = 10 if count <= 0 else count
    my_list = []
    barcode_list = []
    result =  db.child('Records').get().val()
    if type(result) != list:
        for val in result.values():
            datetime_obj = datetime.strptime(val['recordDate'],'%d.%m.%Y %H:%M')
            my_dict = {
                'barcode' : val['barcode'],
                'date' : datetime_obj,
                }
            my_list.append(my_dict)
            
        #my_list = sorted(my_list,key=lambda p: p[1],reverse=True)
        my_list = sorted(my_list, key = lambda k: k["date"],reverse=True)
        
        done = set()
        for d in my_list:
            if d['barcode'] not in done:
                done.add(d['barcode'])
                if len(barcode_list) < count:
                    barcode_list.append(d['barcode'])
                    
        products = barcodeToProduct(barcode_list)
        return json.dumps(products, indent=4,ensure_ascii=False)
            
    
def returnRecordId(shopId,barcode):
    result = db.child('Records').order_by_child('shopId').equal_to(shopId).get().val()
    if isinstance(result,dict):
        for k,v in result.items():
            if v['barcode'] == barcode:
                return k
        return False
    else: 
        return False
    
def barcodeToProduct(barcode_list):
    product_list = []
    result = db.child('Products').get().val()
    for barcode in barcode_list:
        for val in result.keys():
            if val == barcode:
                result[val]['barcode'] = barcode
                result[val]['Records'] = getRecords(val)
                product_list.append(result[val])
    return product_list

def getRecords(barcode):
    record_list = []
    records = db.child('Records').order_by_child('barcode').equal_to(barcode).get().val()
    if isinstance(records,dict):
        for rec in records.values():
            record_list.append(rec)
    return record_list
  


if __name__ == '__main__': 
   app.run(debug=True)