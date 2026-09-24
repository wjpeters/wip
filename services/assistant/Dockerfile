FROM node:25.2.1-alpine@sha256:f4769ca6eeb6ebbd15eb9c8233afed856e437b75f486f7fccaa81d7c8ad56007
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY . .
RUN mkdir -p /app/empty /home/node/.codex && chown -R node:node /home/node/.codex && /app/node_modules/.bin/codex --version
ENV PATH="/app/node_modules/.bin:${PATH}"
USER node
EXPOSE 8090
CMD ["node", "server.mjs"]
