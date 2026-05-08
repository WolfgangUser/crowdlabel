# ─── Stage 1: Build ───────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build


# ─── Stage 2: Serve with nginx ────────────────────────────────────────────────
FROM nginx:1.25-alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html

# nginx конфигурация для SPA (все маршруты → index.html)
RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { try_files $uri $uri/ /index.html; } \
    location /api/ { proxy_pass http://backend:8000; } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
