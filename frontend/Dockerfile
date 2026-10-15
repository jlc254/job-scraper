FROM node:22-alpine

WORKDIR /app

# Install from the lockfile so local and container dependencies stay in sync.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ENV NODE_ENV=development
ENV HOSTNAME=0.0.0.0

EXPOSE 3000

CMD ["npm", "run", "dev"]
