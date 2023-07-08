## Decision Making Systems
Assignment for the course "Decision Making Systems" [2022-2023]. Code was written in python with PyCharm Professional 2023.1.2 IDE, MySQL was used as database management system and Ubuntu 22.04 was the operating system. 
Authors: 
- Jason-Alexander Karafotias
- Apostolos Kalamaras
- Ilias Tolos


## Requirements
You must use Python 3 or higher.
You much have a python enviroment set up.
You must have a valid API key for last.fm.
You must have all CSV file located in the same directory as main.py.


### Install MySQL Server https://dev.mysql.com/downloads/mysql/

```bash
sudo apt install mysql-server
```

Check MySQL version
```bash
mysql --version
```

### Install MySQL connector for python
```bash
pip install mysql-connector-python
```

Go to PyCharm → File → Settings → Project → Python Interpreter → Press “+” to install packages 
- mysql-connector
- mysql-connector-python
- mysql-connector-python-dd

and update pip, if needed (go to PyCharm’s Terminal → pip install --upgrade pip)

### Configure MySQL https://www.digitalocean.com/community/tutorials/how-to-install-mysql-on-ubuntu-22-04
```bash
sudo mysql
```
```bash
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'password';
```
```bash
exit
```
```bash
sudo mysql_secure_installation
```

Start MySQL service
```bash
systemctl start mysql.service
```

Check MySQL status
```bash
systemctl status mysql.service
```
```bash
systemctl is-active mysql
```

Stop MySQL service
```bash
systemctl stop mysql.service
```

### Connect to database using MySQL through terminal
```bash
mysql -u root -p
```

### Install MySQL Workbench https://www.mysql.com/products/workbench/
```bash
sudo snap install mysql-workbench-community
```

Open MySQL Workbench application and press “+” to create a test connection
Connection name: test
Password: Store in Keychain… and enter password
Test connection → OK

## Existing Users in configured MySQL

| USER  | PASSWORD |
|-------|----------|
| root  | password |


### Create last.fm account to get API Key
https://www.last.fm/api/account/create


## Execute main functionality
```bash
python main.py
```


## Execute Arima model
```bash
python arima.py
```

## Execute genetic algorithm model
```bash
python genetic_algorithm.py
```




