FROM python:3.12

WORKDIR /app

COPY . .

RUN pip install fastapi uvicorn motor pydantic pydantic-mongo \
    "python-jose[cryptography]" bcrypt "redis[asyncio]"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]