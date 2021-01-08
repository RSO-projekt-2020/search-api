from flask import *
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ
import datetime

# logging imports
import logging
from logstash_async.handler import AsynchronousLogstashHandler
from logstash_async.handler import LogstashFormatter

route = '/v1'
app = Flask(__name__)
CORS(app, resources={r"/v1/*": {"origins": "*"}})

# -------------------------------------------
# DB settings
# -------------------------------------------
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = environ['DB_URI']
db = SQLAlchemy(app)

# -------------------------------------------
# Logging setup
# -------------------------------------------
# Create the logger and set it's logging level
logger = logging.getLogger("logstash")
logger.setLevel(logging.INFO)        

log_endpoint_uri = str(environ["LOGS_URI"]).strip()
log_endpoint_port = int(environ["LOGS_PORT"].strip())


# Create the handler
handler = AsynchronousLogstashHandler(
    host=log_endpoint_uri,
    port=log_endpoint_port, 
    ssl_enable=True, 
    ssl_verify=False,
    database_path='')

# Here you can specify additional formatting on your log record/message
formatter = LogstashFormatter()
handler.setFormatter(formatter)

# Assign handler to the logger
logger.addHandler(handler)

# -------------------------------------------
# Models
# -------------------------------------------
class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String)
    password_hash = db.Column(db.String)
    n_followers = db.Column(db.Integer)
    n_following = db.Column(db.Integer)
    created_on = db.Column(db.String)

    def __init__(self, email, password):
        self.email = email
        self.password_hash = self.create_pwd_hash(password)
        self.created_on = str(datetime.datetime.utcnow())
        self.n_followers = 0
        self.n_following = 0
        
    def to_dict(self):
        tmp = {'user_id': self.user_id,
                'email': self.email,
                'n_followers': self.n_followers,
                'n_following': self.n_following,
                'created_on': self.created_on}
        return tmp


# -------------------------------------------
# Views
# -------------------------------------------
@app.route(route + '/search', methods=['GET'])
def search():
    query = request.args.get('q', default=None)
    if query is None or query is '':
        return make_response({'msg': 'empty query', 'content': []})
    logger.info("[search-api] someone is querying for users like:" + str(query))
    users = User.query.filter(User.email.like(query + '%')).all()
    return make_response({'msg': 'ok', 'content': [x.to_dict() for x in users]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080')

