# qDiff
## Overview
A tool for finding the difference between multiple data sources which should have the same value.

---
## Goals
1. Reduce the efforts required to check data validation from different source.
1. Report the differences to user.
1. Resolve the differences for user basing on input rules.

---
## setup on EC2
### Install
1. install mysql
    ```shell
    sudo yum install mysql-server
    ```
1. install python 3.6
    ```shell
    sudo yum install python36
    ```
1. clone repository
    ```shell
    ssh-agent bash -c 'ssh-add /path/to/your/private/rsakey; git clone git@github.com:analyticsMD/datadiff.git'
    ```
1. install gcc for compiling mysql-connector
    ```shell
    sudo yum install gcc
    ```
1. install python-devel for compiling mysql-connector
    ```shell
    sudo yum install -y python36-devel
    ```
1. install dependency
    ```shell
    python3 -m pip install -r datadiff/requirements.txt --user
    ```


### Setup database - mysql
1. start mysql server
    ```shell
    sudo service mysqld start
    ```
1. login into mysql with root user
    ```shell
    mysql -u root -p
    ```
1. create database qdiff and qdiff_test
    ```shell
    mysql> create database qdiff;
    mysql> create database qdiff_test;
    ```
1. change database password in the /qdiff/setting/settings.py and settings_test.py
1. install the database schema
    ```shell
    python3 manage.py makemigrations
    python3 manage.py migrate
    ```

### install rabbitmq as broker for celery
1. install Erlang Version 20.1
    ```
    cd /opt
    sudo wget https://github.com/rabbitmq/erlang-rpm/releases/download/v20.1.7/erlang-20.1.7-1.el6.x86_64.rpm
    sudo rpm -ivh erlang-20.1.7-1.el6.x86_64.rpm
    ```
1. install Socat
    ```
    sudo yum install socat
    ```
1. RabbitMQ v3.7.0
    ```
    sudo wget https://dl.bintray.com/rabbitmq/all/rabbitmq-server/3.7.0/rabbitmq-server-3.7.0-1.el6.noarch.rpm
    sudo rpm -ivh rabbitmq-server-3.7.0-1.el6.noarch.rpm
    ```
1. start rabbitmq, run the command
    ```
    rabbitmq-server
    ```
1. or you can start rabbitmq as service
    ```
    sudo service rabbitmq-server start
    ```


### start celery worker, use daemon or inline cli. check http://docs.celeryproject.org/en/latest/userguide/daemonizing.html
```
celery -A qdiff worker -l info --detach
```

### Sanity test
1. run command
    ```shell
    sudo python3 manage.py test --settings=setting.settings_test
    ```
1. Cheers if all the test cases are successful

---
## Deploy with Nginx, UWSGI in EC2
### pull the code into the folder /opt/datadiff/
1. make directory /opt/
    ```shell
    sudo mkdir /opt
    ```
1. clone the code with git
    ```shell
    cd /opt
    git clone git@github.com:analyticsMD/datadiff.git
    ``` 

### install uwsgi
1. run command
    ```shell
    sudo python3 -m pip install uwsgi
    ```

### install nginx
1. run command
    ```shell
    sudo yum install nginx
    ```

### create qdiff.conf file for nginx
1. run command
    ```shell
    sudo vim /etc/nginx/nginx.conf
    ```
1. edit context for your requirement, this is a simple sample
    ```
    user ec2-user ec2-user;
    worker_processes auto;
    error_log /var/log/nginx/error.log;
    pid /var/run/nginx.pid;
    include /usr/share/nginx/modules/*.conf;

    events {
        worker_connections 1024;
    }
    http {
        server_names_hash_bucket_size 128;
        log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                          '$status $body_bytes_sent "$http_referer" '
                          '"$http_user_agent" "$http_x_forwarded_for"';

        access_log  /var/log/nginx/access.log  main;

        sendfile            on;
        tcp_nopush          on;
        tcp_nodelay         on;
        keepalive_timeout   65;
        types_hash_max_size 2048;
        include             /etc/nginx/mime.types;
        default_type        application/octet-stream;
        include /etc/nginx/conf.d/*.conf;
        include /etc/nginx/sites-enable/*;
        index   index.html index.htm;
    }
    ```

### create qdiff_nginx.conf for nginx
1. make two directories, /etc/nginx/sites-enable/ and /etc/nginx/sites-available/
    ```shell
    mkdir /etc/nginx/sites-enable/
    mkdir /etc/nginx/sites-available/
    ```
1. create qdiff_nginx.conf in /etc/nginx/sites-available/
    ```shell
    sudo vim /etc/nginx/sites-available/qdiff_nginx.conf
    ```
1. edit content as follow
    ```
    # the upstream component nginx needs to connect to
    upstream django {
        server unix:///opt/datadiff/qdiff.sock; # for a file socket
        # server 127.0.0.1:8001; # for a web port socket
    }

    # configuration of the server
    server {
        # the port your site will be served on
        listen      8000;
        # the domain name it will serve for
        server_name ec2-54-183-250-158.us-west-1.compute.amazonaws.com; # substitute your machine's IP address or FQDN
        charset     utf-8;

        # max upload size
        client_max_body_size 1000M;   # adjust to taste

        # Django media
        location /media  {
            alias /opt/datadiff/media;  # your Django project's media files - amend as required
        }
        location /static {
            alias /opt/datadiff/static; # your Django project's static files - amend as required
        }

        # Finally, send all non-media requests to the Django server.
        location / {
            uwsgi_pass  django;
            include     /opt/datadiff/uwsgi_params; # the uwsgi_params file you installed
        }
    }

    ```

### make sure the permissions of the folder /var/lib/nginx/tmp/client_body/ is readable
1. check the read write permissions
    ```shell
    ls -l /var/lib/nginx/tmp/
    ```
    it should return
    ```shell
    drwxr-xr-x 2 ec2-user ec2-user 4096 Jul 31 19:36 client_body
    drwx------ 2 ec2-user ec2-user 4096 Jul 24 02:06 fastcgi
    drwx------ 2 ec2-user ec2-user 4096 Jul 24 02:06 proxy
    drwx------ 2 ec2-user ec2-user 4096 Jul 24 02:06 scgi
    drwx------ 7 ec2-user ec2-user 4096 Jul 31 19:36 uwsgi

    ```

### start the qdiff
1. start the nginx service
    ```shell
    sudo service nginx start
    ```

1. start uwsgi worker
    ```shell
    cd /opt/datadiff
    uwsgi --socket qdiff.sock --module setting.wsgi --chmod-socket=664 --daemonize uwsgi.log
    ```

### start and test your machine
1. access URL host:port/tasks to check if it works or not

for example: http://ec2-xx-xx-xx-xx.us-west-1.compute.amazonaws.com/tasks

1. if not working, check following files for debug
    ```shell
    /var/log/nginx/error.log    #nginx reverse server log
    /opt/datadiff/uwsgi.log     #uwsgi server log
    /opt/datadiff/dev.log       #qdiff log
    ```
---

## System architecture
### Architecture

    For database, the user should config access in qDiff database.
    For API, the user should input an description for the API, including endpoint, method, parameters, and authentication information.

<img src="./diagrams/sa.png">
<a href="https://drive.google.com/open?id=1GzHV_wweiGHNRarZlgLIKfL8TgOqlY5i">link</a>

### Data flow
<img src="./diagrams/df.png">
<a href="https://drive.google.com/open?id=1rTqiyL6w3TEEVXfZsxA1inN8pERg8vrF">link</a>


### Components
1. Data reader
    * Using ORM framework to read the data
    * Supporting multiple databases and file sources
1. file reader
    * Importing the file into the database, support  DSV(CSV, TSV) and excel
1. Comparator
    
    1. Brief description

        data1, data2: the input data, can be queryset, list, dictionary

        item1, item2: the elements from data1 and data2
        
        list1, list2: the list for saving unmatch records

    1. steps
        1. Sort the data1 and data2
        1. Iterate over data1 and data2 at same time, item1 comes from data1 and item2 comes from data2
            1. If the item1 is identical to item2, iterate next item
            1. If the item1 in list2, save the all elements in list2 except item1 as conflicted results
            1. If the item2 in list1, save the all elements in list1 except item2 as conflicted results
            1. If the item1 is different from the item2, put item1 in list1 and item2 in list2

    1. Complexity.

        given m,n = len(data1),len(data2)
    
        Time complexity:

            Average Case: O(m+n)

            Amortized Worst Case: O(m*n)

        Space complexity:

            O(m+n)

    1. pseudo code in python

        ```python
        qDiff(data1, data2):
            iter1 = iter(sorted(data1))
            iter2 = iter(sorted(data2))
            temp_dict1 ={}
            temp_dict2 ={}
            item1 = None
            item2 = None
            try:
                while True:
                    item1 = next(iter1)
                    item2 = next(iter2)
                    h1 = hash(item1)
                    h2 = hash(item2)
                    if h1==h2:
                        item1 = None
                        item2 = None
                        continue
                    elif h1 in temp_dict2 or h2 in temp_dict1:
                        if h1 in temp_dict2:
                            temp_dict2.pop(h1)
                            saveToConflictedResult(temp_dict2.values())
                        if h2 in temp_dict1:
                            temp_dict1.pop(h2) 
                            saveToConflictedResult(temp_dict1.values())
                    else:
                        temp_dict1[h1]=item1
                        temp_dict2[h2]=item2
                    item1 = None
                    item2 = None
            except StopIteration as e:
                if not item1:
                    saveToConflictedResult(list(iter2))
                else:
                    saveToConflictedResult([item1] + list(iter1))
        ```


1. Rule parser
    * Parsing the input rules and save as rule set for reuse
    * Rules:

        Where to write the resolved result
        Left join, right join, inner join, and outer join
        Condition based rule, (E.X. when field1 == 0 and field2 > 3)


1. Report viewer
    * Providing the comparison result    
    * GUI for accepting rules for resolving (phase 3)

1. Conflict resolver
    * Filtering the conflicted results basing on the input rules


---
## Scenarios
1. Comparing tables within same database
1. Comparing tables from different databases
1. Comparing tables with different range of data within same/different database
1. Comparing table and CSV file
1. Comparing unordered CSV file and database 

---

## Milestone
### Development
| phase | timeline | items
---|---|---
1 | Week 2 | Data reader, file reader, comparator
2 | Week 4 | Report viewer
3 | Week 6 | Rule parser, conflict resolver

### SIT
| phase | timeline | items
---|---|---
1 | Week 3 | Data reader, file reader, comparator
2 | Week 5 | Report viewer
3 | Week 7 | Rule parser, conflict resolver

### CAT/UAT
| phase | timeline | items
---|---|---
1 | Week 4 | Data reader, file reader, comparator
2 | Week 6 | Report viewer
3 | Week 8 | Rule parser, conflict resolver

---

## ERD
### entities	
<img src="./diagrams/erd.png">
1. Task

    * Information of datasource
    * Uploaded file path
    * Database information (encryption required, use what as secret key, what as salt) 
    * Datetime, Recording the start time and end time for performance evaluation
    * Owner 

1. Conflict record
    * Raw data
    * What source it belongs to
1. Rule set
    * Name 
    * Description
    * Rule, formatted rules in json format
    
