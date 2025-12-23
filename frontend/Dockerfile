# Frontend Dockerfile
FROM node:20-alpine

WORKDIR /app

# Install dependencies (incorporating lock file for consistency)
COPY package.json package-lock.json* ./

RUN npm install

# Copy source code
COPY . .

# Build the Next.js app? 
# For dev environment, we usually just run dev. 
# For production we would run build. 
# The user asked for implementation to start, usually implies dev for now.
# But let's keep it flexible.

EXPOSE 3000

CMD ["npm", "run", "dev"]
