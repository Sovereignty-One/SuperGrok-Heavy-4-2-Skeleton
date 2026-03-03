FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production
COPY server.js ./
EXPOSE 9898
CMD ["node", "server.js"]
