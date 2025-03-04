# About
This is the code repository for the main assignment infrastructure components and is intended to serve as a future repository for the CI/CD pipeline for the project.

The full prototype is explained and demonstrated in the .ppt presentation attached to my e-mail. 
For details on the infrastructure deployment project, see my [other repository](https://github.com/vxmm/circulion-infra-deployment).

## Overview of the entire infrastructure

 ![cl-overview-assignment-final](https://github.com/user-attachments/assets/350a4f44-577f-4c24-8b46-8770a49be23f)


## Configuring the web server

Either connect to the instance or attach these to an EC2 user script: 

- sudo yum install python3 -y

- sudo yum install python3-pip

- sudo yum install nginx -y # web server as reverse proxy

- sudo pip3 install Flask Flask-JWT-Extended werkzeug boto3 # app server, dependencies

- sudo vi /etc/nginx/nginx.conf # modifying some config files

- sudo systemctl restart nginx

- flask run --host=0.0.0.0 --port=5000

## Lambda libraries 

Please note that the Lambda running cl-signed-url-generator.py uses the rsa library is not included in the list of available modules in AWS. 
