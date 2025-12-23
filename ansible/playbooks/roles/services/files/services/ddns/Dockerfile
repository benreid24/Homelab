FROM node:22-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build TypeScript
RUN npm run build

# Run the script every 5 minutes
CMD ["sh", "-c", "while true; do npm start; sleep 300; done"]
