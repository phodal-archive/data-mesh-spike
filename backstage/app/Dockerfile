# Backstage Dockerfile for ARM64 (Apple Silicon) support
# Multi-arch build using Node.js official image

FROM node:18-bookworm-slim AS packages

WORKDIR /app

# Copy package files
COPY package.json yarn.lock ./

# Install dependencies
RUN yarn install --frozen-lockfile --network-timeout 600000

# Build stage
FROM node:18-bookworm-slim

# Install OS dependencies required for Backstage
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    g++ \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy node_modules from packages stage
COPY --from=packages /app/node_modules ./node_modules

# Copy application files
COPY . .

# Set environment variables
ENV NODE_ENV=production

# Expose port
EXPOSE 7007

# Start the application
CMD ["node", "packages/backend/dist/index.cjs.js"]

