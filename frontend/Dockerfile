# Image de dev simple (hot-reload) — suffisant pour une démo hackathon.
FROM node:20-alpine

WORKDIR /app

# Dépendances d'abord (cache Docker)
COPY package.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
