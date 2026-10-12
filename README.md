
# Three-Tier Application

A three-server application deployed on RHEL.

## Architecture
- Frontend: HTML, CSS, JavaScript, Apache HTTP Server
- Backend: Python Flask, Gunicorn
- Database: MySQL

## Project structure
- frontend/ - frontend source code
- backend/ - Flask API source code
- database/ - database schema and migrations
- deploy/ - deployment configurations and instructions

## Deployment
Deployment is performed manually to each RHEL server.
Do not commit production credentials, private keys, or environment files.
