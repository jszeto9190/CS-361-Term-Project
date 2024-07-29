-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS cs361;

-- Use the database
USE cs361;

-- Create the restaurants table
CREATE TABLE IF NOT EXISTS restaurants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    rating INT NOT NULL,
    cuisine VARCHAR(255) NOT NULL,
    price VARCHAR(10) NOT NULL,
    comments TEXT,
    ammenities TEXT
);