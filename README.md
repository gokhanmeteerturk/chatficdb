# chatficdb

For a clean ec2 container with Ubuntu:
```bash
sudo apt update
sudo apt upgrade
sudo apt install nginx
sudo systemctl status nginx
```
you may need to do Ctrl+C
```bash
python3 --version
curl -O https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py --user
```
Install docker and docker-compose:
```bash
sudo apt install ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

sudo echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update

sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
pip install docker-compose
```

clone this repo:
```bash
git clone https://github.com/gokhanmeteerturk/chatficdb.git
cd chatficdb
ls
```
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
sudo cp -f ./fastapi.conf /etc/nginx/sites-available/fastapi.conf
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


```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d chatficdb.top
```

This will change your sites-available file too. Make sure to check its contents for better understanding of what just happened:

```bash
cat /etc/nginx/sites-available/fastapi.conf
```
```bash
crontab -e
1
# add to end of file, then ctrl-x , y, enter:
0 12 * * * /usr/bin/certbot renew --quiet
```

You can also check this one out:
https://www.nginx.com/blog/using-free-ssltls-certificates-from-lets-encrypt-with-nginx/

Start your FastAPI application using Docker Compose:
```bash
sudo docker compose up -d --build
```
With this setup, Nginx will act as a reverse proxy, forwarding requests to your FastAPI application served by Gunicorn on port 8000. This configuration allows you to take advantage of Nginx's performance and load balancing capabilities while serving your FastAPI application using Gunicorn.