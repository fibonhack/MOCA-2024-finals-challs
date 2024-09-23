CREATE DATABASE IF NOT EXISTS price_checker_db;
USE price_checker_db;

CREATE TABLE users (
    userid int AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(30) UNIQUE NOT NULL,
    password VARCHAR(1000) NOT NULL
);