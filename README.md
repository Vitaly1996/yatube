# Yatube
### Описание
Сервис разработан по классической MVT архитектуре. Пользователи сервиса могут создавать свои странички, делиться своими фото. Если зайти на страничку, то можно увидеть все записи автора. Также пользователи могут заходить на чужие странички, подписываться на авторов и комментировать их записи.

### Технологии
- Python 3.7
- Django 2.2
- Django ORM
- SQlite3
- nginx
- unit testing

### Установка
- склонировать репозиторий

```sh
git clone github.com/Vitaly1996/yatube.git
```
- создать и активировать виртуальное окружение для проекта

```commandline
python -m venv venv
source venv/scripts/activate (Windows)    
source venv/bin/activate (MacOS/Linux)
python3 -m pip install --upgrade pip
```
- установить зависимости

```commandline
python pip install -r requirements.txt
```
- сделать миграции
```commandline
python manage.py makemigrations
python manage.py migrate
```

- запустить сервер
```commandline
python manage.py runserver
```
