import jwt
import datetime
import boto3
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from functools import wraps

app = Flask(__name__)
app.secret_key = 'ABCD' 

# DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('cl-client-database') 

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get('token')

        if not token:
            return jsonify({'message': 'Token is missing'}), 403

        try:
            # Decode the JWT token
            data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid'}), 403

        return f(*args, **kwargs)

    return decorated

@app.route('/')
def index():
    return render_template('login.html')  # Return login page when accessed

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    # Query DynamoDB to fetch user info based on 'username'
    response = table.get_item(Key={'username': username})
    user = response.get('Item')

    if user and user['password'] == password:
        # Generate JWT token
        token = jwt.encode({
            'user_id': user['username'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, app.secret_key)

        # Store the token in the session
        session['token'] = token

        # Redirect to the greetings page with the username
        return redirect(url_for('greetings', username=user['username']))

    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/greetings/<username>')
@token_required
def greetings(username):
    return render_template('greetings.html', username=username)

if __name__ == '__main__':
    app.run(debug=True)
