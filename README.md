<h2>Проектное задание для Yandex Backend School</h2>
Задача: разработать на python REST API сервис, который позволит нанимать курьеров на работу, принимать заказы и оптимально распределять заказы между курьерами, попутно считая их рейтинг и заработок.
Сервис необходимо развернуть на предоставленной виртуальной машине на 0.0.0.0:8080
</br>


<h3>Используемые библиотеки:</h3>

* [Django](https://www.djangoproject.com/)

* [Django Rest Framework](https://www.django-rest-framework.org/)

* СУБД [PostgreSQL](https://www.postgresql.org/)

* WSGI сервер [Gunicorn](https://gunicorn.org/)

<h3>Реализованные обработчики:</h3>

*       POST /couriers
  Для загрузки списка курьеров в систему.
*       PATCH /couriers/courier_id
  Позволяет изменить информацию о курьере.
*       POST /orders
  Для загрузки списка заказов в систему
*       POST /orders/assign
  Принимает id курьера и назначает максимальное количество заказов, подходящих по весу, району и графику работы.
*       POST /orders/complete
  Принимает 3 параметра: id курьера, id заказа и время выполнения заказа, отмечает заказ выполненным.
*       GET /couriers/courier_id
  Возвращает информацию о курьере и дополнительную статистику: рейтинг и заработок.


<h3>Инструкции по деплою</h3>
Для деплоя я использовал связку gunicorn и nginx как обратный прокси сервер, хоть это и необязательно
1. Установка PostgreSQL

        sudo apt install postgresql postgresql-contrib
    
    Создание базы данных для проекта:
   
        sudo -u postgres psql
        CREATE DATABASE <имя БД>;

    Создание нового пользователя и предоставления ему полного доступа над БД:
   
        CREATE USER <имя пользователя> WITH PASSWORD 'пароль';
        GRANT ALL PRIVILEGES ON DATABASE <имя БД> TO <имя пользователя>;

2. Настройка проекта

    Прежде чем выполнить миграцию, надо настроить подключение к бд в файле `settings.py`:
   
        DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'имя бд',
            'USER': 'имя пользователя',
            'PASSWORD': 'пароль',
            'HOST': '127.0.0.1',
            'PORT': '',
            }
        }

    В корневом каталоге надо запустить скрипт управления для начальной миграции:
   
        python3 manage.py makemigrations
        python3 manage.py migrate

    Проверяем, что gunicorn может корректно обсуживать проект

        gunicorn --bind 0.0.0.0:8000 wsgi

3. Настройка сервиса для правильного запуска приложения

    Создание сокета, который будет автоматический прослушивать подключения, для этого нужно создать файл сокета в директории `/etc/systemd/system/gunicorn.socket`:
   
    Конфигурация сокета:
   
        [Unit]
        Description=gunicorn socket
        
        [Socket]
        ListenStream=/run/gunicorn.sock
        
        [Install]
        WantedBy=sockets.target

    Создание служебного файла, который будет открывать наш сокет:

        sudo nano /etc/systemd/system/gunicorn.service
    
    Конфигурация:

        [Unit]
        Description=gunicorn daemon
        Requires=gunicorn.socket
        After=network.target
        
        [Service]
        User=sammy
        Group=www-data
        Restart=Always
        WorkingDirectory=директория к проекту
        ExecStart=диркетория к исполняемому файлу gunicorn ( (virtualenvdir) -> /bin/unicorn) \
                  --access-logfile - \
                  --workers 3 \
                  --bind unix:/run/gunicorn.sock \
                  wsgi
        
        [Install]
        WantedBy=multi-user.target

4. Настройка nginx

        sudo nano /etc/nginx/sites-available/candy

   Конфигурация:

       server {
        listen 8080;
        server_name 0.0.0.0;
    
        location = /favicon.ico { access_log off; log_not_found off; }
    
        location / {
            include proxy_params;
            proxy_pass http://unix:/run/gunicorn.sock;
            }
        }
    Активация конфига:
   
        sudo ln -s /etc/nginx/sites-available/candy /etc/nginx/sites-enabled

    Запуск всего :)

        sudo systemctl start gunicorn.socket
        sudo systemctl enable gunicorn.socket
        sudo systemctl daemon-reload
        sudo systemctl restart gunicorn