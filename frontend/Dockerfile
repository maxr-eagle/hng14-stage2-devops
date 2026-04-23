FROM node:20-alpine AS builder

WORKDIR /build

COPY package*.json .

RUN npm ci --only=production

FROM node:20-alpine

ENV NODE_ENV=production

WORKDIR /app

COPY --from=builder /build/node_modules ./node_modules

COPY app.js .
COPY views/ ./views/
COPY package.json .

RUN addgroup -S appgroup && \
    adduser -S appuser -G appgroup

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:3000/ || exit 1

CMD ["node", "app.js"]
