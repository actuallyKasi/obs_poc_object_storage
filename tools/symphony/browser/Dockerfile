FROM node:22.22.0-bookworm-slim@sha256:dd9d21971ec4395903fa6143c2b9267d048ae01ca6d3ea96f16cb30df6187d94
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts && ./node_modules/.bin/playwright install --with-deps chromium && npm cache clean --force
ENTRYPOINT ["node", "/app/node_modules/@playwright/mcp/cli.js"]
