# CAIP-Karnataka Frontend Dockerfile
# Runs the Vite dev server directly (not a static Nginx build) so the
# exposed port matches docker-compose's 5173:5173 mapping exactly, and
# so VITE_API_BASE_URL is picked up at container start without a
# separate rebuild step.
FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]
