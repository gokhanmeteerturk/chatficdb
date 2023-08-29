# chatficdb

Create .env:
```bash
cp env-example .env
```
Change contents.
```bash
nano .env
```
move fastapi.conf

```bash
yes | cp -f ./fastapi.conf /etc/nginx/sites-available/fastapi.conf
```


Create a symbolic link to the configuration file in the sites-enabled directory:
```bash
sudo ln -s /etc/nginx/sites-available/fastapi.conf /etc/nginx/sites-enabled/
```
Test the Nginx configuration and restart Nginx:
```bash
sudo nginx -t
sudo systemctl restart nginx
```
Start your FastAPI application using Docker Compose:
```bash
sudo docker-compose up -d --build
```
With this setup, Nginx will act as a reverse proxy, forwarding requests to your FastAPI application served by Gunicorn on port 8000. This configuration allows you to take advantage of Nginx's performance and load balancing capabilities while serving your FastAPI application using Gunicorn.