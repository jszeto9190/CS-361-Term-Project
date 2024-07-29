# CS-361-Term-Project: Restaurant Explorer

## Steps to Run This Application

### 1. Install Dependencies
Ensure you have all the necessary Python packages installed.

### 2. Create .env File
Create a file named '.env' in the root directory of the project. Copy and paste the following code into the file and replace the placeholders with your database information.

FLASK_SECRET_KEY='your_secret_key'
DB_USER='root'
DB_PASSWORD='your_database_password'
DB_HOST='localhost'
DB_NAME='cs361'

### 3. Create Database and Tables
Run create_restaurant_tables.sql file with a MySQL client.

### 4. Run the Application
Run the following command in the root directory:

python app.py

### 5. Access the Application
Run http://127.0.0.1:5000 in your web browser.