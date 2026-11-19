# Методические рекомендации — сайт

Интерактивная версия методических рекомендаций по экспериментальной оценке эффективной вязкости неньютоновской жидкости при ударной нагрузке в домашних условиях (Платонов М.А.).

На сайте: текст методички, схема установки, калькулятор (скорость удара, сила сопротивления, эффективная вязкость) и таблица для записи опытов. Пример в калькуляторе — условные значения, не результаты измерений.

## Локальный запуск

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Как выложить на Streamlit Community Cloud

Нужен аккаунт GitHub: **m-platonov-1ss**.

1. Создай на GitHub новый публичный репозиторий (например, `metod-site`). Бесплатный Community Cloud работает с публичными репозиториями.
2. Загрузи в репозиторий все файлы этой папки: `app.py`, `requirements.txt`, каталог `assets/` (схема и PDF), `.streamlit/config.toml` и этот README. Можно через сайт GitHub («Add file» → «Upload files») или через git:

   ```bash
   git init
   git add .
   git commit -m "Сайт-методичка"
   git branch -M main
   git remote add origin https://github.com/m-platonov-1ss/metod-site.git
   git push -u origin main
   ```

3. Открой [Streamlit Community Cloud](https://share.streamlit.io) и войди через GitHub (разреши доступ, если сайт попросит).
4. Нажми **Create app**. Укажи репозиторий `m-platonov-1ss/metod-site`, ветку `main` и главный файл `app.py`.
5. Нажми **Deploy**. Через одну-две минуты сайт будет доступен по адресу вида `https://metod-site-….streamlit.app`.
