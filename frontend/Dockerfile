# Frontend Dockerfile — Next.js with Node 20
FROM node:20-alpine

WORKDIR /app

# Install dependencies first (cached layer)
COPY package.json package-lock.json* ./
RUN npm install

# Copy application code
COPY . .

# Expose port 3000
EXPOSE 3000

# Set hostname to 0.0.0.0 so the container is accessible from outside
ENV HOSTNAME="0.0.0.0"

# Default command — dev mode with host binding for Docker
CMD ["npx", "next", "dev", "--hostname", "0.0.0.0", "--port", "3000"]
