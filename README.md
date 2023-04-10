# Foodgram

![foodgram workflow](https://github.com/ezereul/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)

***

Проект Foodgram позволяет пользователям делиться своими рецептами
с другими. Вот некоторый функционал:
- Публикация рецепта
- Подписка на автора рецепта
- Добавление рецепта в избранное
- Добавление рецепта в список покупок
- Возможность скачать список покупок в формате PDF

### Адрес сервера
158.160.49.9

### Запустить проект локально
Клонировать репозиторий 

```bash
git clone https://github.com/Ezereul/foodgram-project-react
```
Создать и активировать виртуальное окружение
```bash
python -m venv venv
source venv/Scripts/activate
```
Установить зависимости
```bash
python -m pip install --upgrade pip
pip install -r requiremtns.txt
```
Применить миграции
```bash
python manage.py migrate
```
Создать суперпользователя
```bash
python manage.py createsuperuser
```
Запустить проект
```bash
python mange.py runserver
```

### Примеры запросов приведены в документации 
`158.160.49.9/redoc/`

### Админка
`158.160.49.9/admin/`

Логин: `admin@admin.com`

Пароль: `11111`