# Stage 1: Build React Mini App
FROM node:20-slim AS frontend
WORKDIR /build
COPY mini_app/package.json ./
RUN npm install
COPY mini_app/ .
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend /build/dist ./mini_app/dist

EXPOSE 8080
CMD ["python", "bot.py"]
