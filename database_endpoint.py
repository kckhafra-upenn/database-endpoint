from flask import Flask, request, g
from flask_restful import Resource, Api
from sqlalchemy import create_engine, select, MetaData, Table
from flask import jsonify
import json
import eth_account
import algosdk
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import load_only
import hashlib, secrets
from pycoin.ecdsa import generator_secp256k1, sign, verify
import hashlib, secrets
from models import Base, Order, Log
engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

app = Flask(__name__)

#These decorators allow you to use g.session to access the database inside the request code
@app.before_request
def create_session():
    g.session = scoped_session(DBSession) #g is an "application global" https://flask.palletsprojects.com/en/1.1.x/api/#application-globals

@app.teardown_appcontext
def shutdown_session(response_or_exc):
    g.session.commit()
    g.session.remove()

"""
-------- Helper methods (feel free to add your own!) -------
"""
def sha3_256Hash(msg):
    hashBytes = hashlib.sha3_256(msg.encode("utf8")).digest()
    return int.from_bytes(hashBytes, byteorder="big")

# def signECDSAsecp256k1(msg, privKey):
#     msgHash = sha3_256Hash(msg)
#     signature = sign(generator_secp256k1, privKey, msgHash)
#     return signature

def verifyECDSAsecp256k1(msg, signature, pubKey):
    msgHash = sha3_256Hash(msg)
    valid = verify(generator_secp256k1, pubKey, msgHash, signature)
    return valid

def log_message(d):
    print("ZZZ",json.dumps(d['payload']))
    payload = json.dumps(d['payload'])
    log_obj = Log(message=payload)
    g.session.add(log_obj)
    g.session.commit()
    print("LOG",g.session.query(Log).all())
    # log_obj = Log( sender_pk=newLog['sender_pk'],receiver_pk=newOrder['receiver_pk'], buy_currency=newOrder['buy_currency'], sell_currency=newOrder['sell_currency'], buy_amount=newOrder['buy_amount'], sell_amount=newOrder['sell_amount'] )
    # session.add(order_obj)
    # session.commit()
    # Takes input dictionary d and writes it to the Log table
    
    pass

"""
---------------- Endpoints ----------------
"""
    
@app.route('/trade', methods=['POST'])
def trade():
    if request.method == "POST":
        content = request.get_json(silent=True)
        print( f"content = {json.dumps(content)}" )
        columns = [ "sender_pk", "receiver_pk", "buy_currency", "sell_currency", "buy_amount", "sell_amount", "platform" ]
        fields = [ "sig", "payload" ]
        error = False
        for field in fields:
            if not field in content.keys():
                print( f"{field} not received by Trade" )
                print( json.dumps(content) )
                log_message(content)
                return jsonify( False )
        
        error = False
        for column in columns:
            if not column in content['payload'].keys():
                print( f"{column} not received by Trade" )
                error = True
        if error:
            print( json.dumps(content) )
            log_message(content)
            return jsonify( False )
            
        #Your code here
        #Note that you can access the database session using g.session
        if(content['payload']['platform']=="Ethereum"):
            sha3_256Hash(content)
            print("VERIFY",verifyECDSAsecp256k1(content,content['sig'],content['sender_pk']))
            print("YES")
        return {}

@app.route('/order_book')
def order_book():
    result = {"data": g.session.query(Order).all()}
    return jsonify(result)


if __name__ == '__main__':
    app.run(port='5002')

