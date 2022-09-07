import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
#db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks')
def get_drinks():
    drinks = ""
    try: 
        un_drinks = Drink.query.all()
        drinks = [drink.short() for drink in un_drinks]
    except:
        abort(404)
        
    
    
    
    return jsonify({
        "success": True,
        "drinks": drinks
    })
    
    

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt):
    drinks = ""
    try:
        un_drinks = Drink.query.all()
        drinks = [drink.long() for drink in un_drinks]
    except:
        abort(404)

    return jsonify({
        "success": True,
        "drinks": drinks
    })





'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(jwt):
    body = request.get_json()
    n_title = ""
    n_recipe = ""
    n_drink = []
    """
        it is important to use json.dumps to turn every sent data as a json data.
        I have created two ways to insert the data as for the test in postman, the recipe is
        sent as dictionary and the front send it as a list. 
    """
    try:
        n_title = body.get("title")
        n_recipe = body.get("recipe")
        if type(n_recipe) == dict:
            print("from dictionnaire")
            obj = f'[{json.dumps(n_recipe)}]'
            print(obj)
            drink = Drink(
            title = n_title,
            recipe = obj
            )
            drink.insert()
        else:
            recipes = json.dumps(n_recipe)
            print(recipes, type(recipes))
            drink = Drink(
            title = n_title,
            recipe = recipes
            )
            print(drink)
            
            drink.insert()
            
        
        q = Drink.query.filter_by(title = drink.title).first()
        n_drink.append(q.long())
        
        
    except:
        abort(422)

    
    return jsonify({
        "success": True,
        "drinks": n_drink
    })
    
'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth("patch:drinks")
def patch_drink(jwt, id):
    body = request.get_json()
    title = body.get('title', None)
    drink = []
    if not title:
        abort(400)
    
    drink_toUpdate = Drink.query.filter(Drink.id == id).one_or_none()
    if drink_toUpdate :
        drink_toUpdate.title = title
        drink_toUpdate.update()
        drink.append(drink_toUpdate.long())

        
    else:
        abort(404)

    return jsonify({
        "success": True,
        "drinks": drink
    })



'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(jwt, id):
    deleted_drink = ""
    drink_toDelete = Drink.query.filter(Drink.id == id).one_or_none()
    if drink_toDelete :
        deleted_drink = drink_toDelete.id
        drink_toDelete.delete()        
    else:
        abort(404)

    return jsonify({
        "success": True,
        "delete": deleted_drink
    })


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''
@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    })
'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "ressource not found"
    }), 404

'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''

@app.errorhandler(AuthError)
def authorization_failed(er):
    return jsonify({
        "success": False,
        "error": er.status_code,
        "message": er.error['error']
    })


