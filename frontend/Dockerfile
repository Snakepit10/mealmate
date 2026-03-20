# Stage 1: build
FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Vite bake env vars at build time
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_WS_BASE=${VITE_WS_BASE}

RUN npm run build

# Stage 2: serve con nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 80
