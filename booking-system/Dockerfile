FROM python:3.10
LABEL authors="sardorbek.numonov"


# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

EXPOSE 8000

RUN chmod +x /app/migrate.sh

# Command to run the application using migrate.sh
CMD ["/app/migrate.sh"]