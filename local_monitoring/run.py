from flask import Flask,render_template,jsonify
from time import sleep
import socket
from config import config


mysql_data = {'data':[]}
reddis_data ={'data':[]}
solr_data ={'data':[]}
rabbitmq_data ={'data':[]}
vmservers_data ={'data':[]}

def check(ip_addr,port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((ip_addr,port))
    sock.close()
    if result == 0:
        return "up"
        print "Port is open"
    else:
        return "down"
        print "Port is not open"


def mysql():
    mysql_data['data'] = []
    for i in config['mysql']:
        print i
        status = check(i,3306)
        print status
        mysql_data['data'].append({'IP':i,'Status':status.upper()})
    return mysql_data
def solr():
    solr_data['data'] = []
    for i in config['solr']:
        print i
        status = check(i,8080)
        print status
        solr_data['data'].append({'IP':i,'Status':status.upper()})
    return solr_data
def reddis():
    reddis_data['data'] = []
    for i in config['reddis']:
        print i
        status = check(i,6379)
        print status
        reddis_data['data'].append({'IP':i,'Status':status.upper()})
    return reddis_data
def rabbitmq():
    rabbitmq_data['data'] = []
    for i in config['rabbitmq']:
        print i
        status = check(i,5672)
        print status
        rabbitmq_data['data'].append({'IP':i,'Status':status.upper()})
    return rabbitmq_data

def vmservers():
    vmservers_data['data'] = []
    for i in config['vmservers']:
        print i
        status = check(i,22)
        print status
        vmservers_data['data'].append({'IP':i,'Status':status.upper()})
    return vmservers_data


app = Flask(__name__)

@app.route('/')
def index():
    # dict = {'phy':50,'che':60,'maths':70}
    # dict = {'MYSQL':{'172.17.7.87':'UP','172.17.7.77':'DOWN'},'REDIS':{'172.17.7.57':'UP','172.17.7.27':'DOWN'},'SOLR':{'172.17.7.81':'UP','172.17.7.71':'DOWN'},'RMQ':{'172.17.7.53':'UP','172.17.7.23':'DOWN'}}
    #dict = {'solr': {'172.17.8.56': 'down', '172.17.7.37': 'up', '172.17.7.87': 'up', '127.0.0.1': 'up'}, 'reddis': {'172.17.8.56': 'down', '172.17.7.37': 'down', '172.17.7.87': 'up', '127.0.0.1': 'down'}, 'rabbitmq': {'172.17.8.56': 'down', '172.17.7.37': 'down', '172.17.7.87': 'down', '127.0.0.1': 'down'}, 'mysql': {'172.17.8.56': 'down', '172.17.7.37': 'down', '172.17.7.87': 'down', '127.0.0.1': 'up'}}

    return render_template('index.html',result=dict)



@app.route('/mysql')
def mysql_test():
    #sleep(1)
    sample = mysql()
    return jsonify(sample)


@app.route('/reddis')
def redis_test():

    sample = reddis()
    return jsonify(sample)

@app.route('/solr')
def solr_test():
    sample = solr()
    return jsonify(sample)

@app.route('/rabbitmq')
def rmq_test():
    sample = rabbitmq()
    return jsonify(sample)

@app.route('/vmservers')
def vmservers_test():
    sample = vmservers()
    return jsonify(sample)


if __name__ == '__main__':
   app.run(host='0.0.0.0',port=80,debug = True)
