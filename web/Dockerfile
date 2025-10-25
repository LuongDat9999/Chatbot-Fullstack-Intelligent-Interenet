FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose port (will be overridden by WEB_PORT env var)
EXPOSE 5180

# Run development server with WEB_PORT
CMD ["sh", "-lc", "npm run dev -- --host --port ${WEB_PORT:-5180}"]