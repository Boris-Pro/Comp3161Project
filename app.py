from flask import Flask, make_response, redirect, request, render_template, jsonify, url_for
from authhandler import AuthHandler
from config import Config

# Initialize app
app = Flask(__name__)
app.config.from_object(Config)

# Instantiate AuthHandler
auth_handler = AuthHandler(app.config['SECRET_KEY'])

# Home route
# @app.route('/')
# def home():
#     return render_template('home.html')

# Home Route
@app.route('/')
def home():
    # Check if the user is logged in by verifying the token
    current_user, error_response, status_code = auth_handler.verify_token(request)
    
    # If there's an error (token is missing or invalid), redirect to login
    if error_response:
        return redirect(url_for('login'))  # Redirect to the login page
    
    # If token is valid, render the home page
    return render_template('home.html', user=current_user)

# Register endpoint
@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        # Extract data from the incoming JSON and pass to register_user
        user_id = data.get('user_id')
        user_name = data.get('user_name')
        user_email = data.get('user_email')
        user_password = data.get('user_password')
        user_type = data.get('user_type')
        
        if not all([user_id, user_name, user_email, user_password, user_type]):
            return jsonify({'message': 'Missing fields'}), 400
        
        return auth_handler.register_user(user_id, user_name, user_email, user_password, user_type)
    return render_template('register.html')


# Login endpoint (set token in cookie)
@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        user_id = data.get('user_id')
        user_password = data.get('user_password')

        if not all([user_id, user_password]):
            return jsonify({'message': 'Missing credentials'}), 400

        # Authenticate user and get the token response
        user_response = auth_handler.authenticate_user(user_id, user_password)
        
        if isinstance(user_response, tuple):  # If invalid credentials
            return user_response  # Return error response (message and status)
        
        # Get the token from the response returned by authenticate_user
        token = user_response.get_json().get('token')

        # Create response
        response = make_response(jsonify({'message': 'Login successful'}))

        # Set the JWT token in the cookie (httpOnly to prevent JS access)
        response.set_cookie('auth_token', token, httponly=True, secure=True, max_age=3600)

        return response
    return render_template('login.html')

@app.route('/auth/logout')
def logout():
    # Create a response to redirect the user
    response = make_response(redirect(url_for('home')))  # Redirect to home after logout
    
    # Remove the 'auth_token' cookie by setting it to an expired date
    response.set_cookie('auth_token', '', expires=0)
    
    return response


# Protected route
@app.route('/auth/protected', methods=['GET'])
def protected():
    current_user, error_response, status_code = auth_handler.verify_token(request)
    
    if error_response:
        return error_response, status_code  # Return the error if the token is invalid
    
    # If the token is valid, render the protected page with the user information
    return render_template('protected.html', user=current_user)



if __name__ == '__main__':
    app.run(debug=True)
