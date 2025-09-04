"""
Основной скрипт создания и запуска приложения
"""

import uvicorn

from fastapi import FastAPI


app = FastAPI()


def main():
    """Запуск сервера"""
    uvicorn.run(app)


if __name__ == '__main__':
    main()
