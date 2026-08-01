FROM node:24-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
COPY frontend/package.json ./frontend/package.json
COPY src-tauri/package.json ./src-tauri/package.json
RUN npm ci --workspace frontend --include-workspace-root

COPY frontend ./frontend

ARG VITE_API_BASE_URL=http://127.0.0.1:8765
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run frontend:build


FROM nginx:1.27-alpine AS runtime

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=5s --retries=6 --start-period=5s \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1/ || exit 1
