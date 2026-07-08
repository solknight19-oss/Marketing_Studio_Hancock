FROM python:3.11-slim
WORKDIR /app
COPY . /app
ENV HOST=0.0.0.0
ENV PORT=8765
EXPOSE 8765
CMD ["python3", "server.py"]
