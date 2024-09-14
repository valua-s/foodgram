## FOODGRAM

Проект предствляет собой социальную сеть в которой пользователя могут:
  - делиться рецептами блюд
  - подписываться на авторов рецептов
  - получать список продуктов необходимых для рецепта
И еще много другое, что вы можете увидеть в рабочей версии

<img src="2024-08-21_19-30-29.png" height='150'/>
<img src="2024-08-22_19-57-57.png" height='150'/>

http://84.252.139.254:7000

---
Бэкенд проекта разработан с помощью: <br><br> ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)<br>

Фреймворки: <br><br>
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)

База данных:<br><br>
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)

Серверная часть: <br><br>
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)

---
Установка на локальном компьютере

1. Клонируйте репозиторий:

```
git clone git@github.com:hqcamp/test-backend-3.git
```

2. Установите и активируйте виртуальное окружение:
```
python -m venv venv
source venv/Scripts/activate  - для Windows
source venv/bin/activate - для Linux
```
3. Установите зависимости:
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4. Перейдите в папку product и выполните миграции:
```
cd product
python manage.py migrate
```
5. Создайте суперпользователя:
```
python manage.py createsuperuser
```
6.Запустите проект:
```
python manage.py runserver
```
