FROM node:25.2.1-alpine@sha256:f4769ca6eeb6ebbd15eb9c8233afed856e437b75f486f7fccaa81d7c8ad56007 AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build
FROM nginxinc/nginx-unprivileged:1.29.1-alpine@sha256:27985295bdb22a1ef8f712863210bd5877c0f3006494a593e86b3fe0fa55467e
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
