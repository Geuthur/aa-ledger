CREATE USER 'aauth' @'%' IDENTIFIED BY 'dbpassword';
CREATE DATABASE alliance_auth CHARACTER SET utf8mb4;
GRANT ALL PRIVILEGES ON alliance_auth.* TO 'aauth' @'%';
GRANT ALL PRIVILEGES ON test_alliance_auth.* TO 'aauth' @'%';