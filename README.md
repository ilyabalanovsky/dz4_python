Запуск:
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload

Swagger доступен по адресу http://127.0.0.1:8000/docs
