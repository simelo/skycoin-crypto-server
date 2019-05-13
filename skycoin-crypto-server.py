#!/bin/python
from flask import Flask, jsonify, request, make_response, abort
import skycoin
from skycoin.skycoin import *
import threading



app = Flask(__name__)

lock = threading.Lock()

SwigPyObjectContainer = {}

    


@app.errorhandler(404)
def not_method(error):
    return make_response(jsonify({"error":"method not found"}), 403)

@app.errorhandler(400)
def incorrect_parameters(error):
    return make_response(jsonify({"error": "incorrect parameters"}), 402)

@app.errorhandler(403)
def not_created(error):
    return make_response(jsonify({"error":"you are using an object that has not been created yet"}))




@app.route("/", methods = ['POST', 'GET'])
def execute_method():
    method = request.json['method']
    params = get_params(request.json['params'])
    try:
        return_values = getattr(skycoin, method)(*params)
    except AttributeError:
        abort(404)
    except TypeError:
        abort(400)
    
    
    
    if isinstance(return_values, (tuple, list)):
        response = {'return_code' : return_values[0]}
        response['returns'] = []
        for obj in return_values[1:]:
            response["returns"].append(create_json(obj))
    else:
        if isinstance(return_values, int):
            response = {'return_code' : return_values}
        else:
            response = {"return" : create_json(return_values)}

    
    return jsonify(response)




def get_params(params):
    objs = []
    for param in params:
        objs.append(create_object(param))
    return objs

def create_object(obj_json):
    tp = obj_json['type']
    if tp == 'int':
        return int(obj_json['value'])
    if tp == 'str':
        return obj_json['value']
    if tp == 'float':
        return float(obj_json['value'])
    if tp == 'NoneType':
        return None
    if tp == 'list':
        obj = []
        for item in obj_json['value']:
            obj.append(create_object(item))
        return obj
    if tp == "dict":
        obj = {}
        for key in obj_json['value'].keys():
            obj[key] = create_object(obj_json['values'][key])
        return obj
    if tp == 'bytes':
        return bytes(obj_json['value'].encode(errors="surrogateescape"))
    if tp == 'SwigPyObject':
        global SwigPyObjectContainer
        
        try:
            
            return SwigPyObjectContainer[obj_json["value"]]
        except KeyError:
            abort(403)
    
    if "skycoin.skycoin." in tp:
        tp = tp[16:]
    try:     
        obj = (globals()[tp])()
    except KeyError:
        abort(400)

    for key in obj.__dict__.keys():
        obj.__dict__[key] = create_object(obj_json[key])
    return obj


def create_json(obj):
    tp = str(type(obj)).split()[1][1:-2]
    data = {"type":tp}
    
    if '.' in tp:
        tp = tp.split('.')[-1]
    
    if tp == 'str':
        data["value"] = obj
        return data
    
    if tp == 'int':
        data["value"] = str(obj)
        return data

    if tp == 'float':
        data["value"] = str(obj)
        return data
    
    if tp == 'list':
        data["value"] = []
        for item in obj:
            data["value"].append(create_json(item))
        return data

    if tp == 'dict':
        data["value"] = {}
        for key in obj.keys():
            data["value"][key] = create_json(obj[key])
        return data
    if tp == 'bytes':
        data["value"] = str(obj.decode(errors="surrogateescape"))
        return data
    if tp == "SwigPyObject":
        global SwigPyObjectContainer
        global lock
        lock.acquire()
        index = str(obj).split()[-1][:-1]
        SwigPyObjectContainer[index] = obj
        data["value"] = str(index)
        lock.release()
        return data
    
    if tp == "NoneType":
        return data

    for key in obj.__dict__.keys():
        data[key] = create_json(obj.__dict__[key])
    return data

if __name__ =="__main__":
    app.run(debug=True, host="0.0.0.0")