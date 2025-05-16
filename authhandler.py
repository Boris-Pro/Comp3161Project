import jwt
import datetime
import mysql.connector
from flask import current_app, jsonify, request
from mysql.connector import Error

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host=current_app.config['MYSQL_HOST'],
        user=current_app.config['MYSQL_USER'],
        password=current_app.config['MYSQL_PASSWORD'],
        database=current_app.config['MYSQL_DATABASE']
    )

class AuthHandler:
    def __init__(self, secret_key):
        self.secret_key = secret_key

    def generate_token(self, user_id):
        """
        Generates a JWT token for a user.
        """
        token = jwt.encode(
            {'id': user_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
            self.secret_key, algorithm="HS256"
        )
        return token

    def verify_token(self, request):
        """
        Verifies a JWT token from the request and returns the current user.
        """
        token = request.cookies.get('auth_token')  # <-- read from cookies
        print(f"Token: {token}")  # Debugging line to check the token value
        if not token:
            return None, jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM User WHERE user_id=%s", (data['id'],))
            current_user = cursor.fetchone()
            cursor.close()
            connection.close()
            return current_user, None, None
        except jwt.ExpiredSignatureError:
            return None, jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return None, jsonify({'message': 'Token is invalid!'}), 401

    def register_user(self, user_id, user_name, user_email, user_password, user_type):
        """
        Registers a new user by saving the user_id, user_name, user_email, user_password, and user_type
        in the database.
        """
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO User (user_id, user_name, user_email, user_password, user_type) "
                "VALUES (%s, %s, %s, %s, %s)",
                (user_id, user_name, user_email, user_password, user_type)  
            )
            connection.commit()
        except Error as e:
            if e.errno == 1062:
                return jsonify({'message': 'User ID or email already exists'}), 409
            else:
                return jsonify({'message': 'Database error'}), 500
        finally:
            cursor.close()
            connection.close()

        return jsonify({'message': 'User registered successfully'})

    def authenticate_user(self, user_id, user_password):
        """
        Authenticates the user by checking their credentials and returning a JWT token.
        """
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM User WHERE user_id=%s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if not user or user['user_password'] != user_password:  # Comparing password directly (no hash)
            return jsonify({'message': 'Invalid credentials'}), 401

        token = self.generate_token(user['user_id'])
        print(f"Generated Token: {token}")  # Debugging line to check the generated token
        return jsonify({'message': 'Login successful','token': token})
        
