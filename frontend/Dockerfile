# syntax=docker/dockerfile:1.7
FROM node:20-alpine AS base
WORKDIR /app
COPY package.json ./
RUN npm install

# ---------- development image ----------
FROM base AS development
COPY . /app/
EXPOSE 5173
CMD ["npm", "run", "dev"]

# ---------- build image ----------
FROM base AS build
COPY . /app/
RUN npm run build

# ---------- production image (static files via nginx) ----------
FROM nginx:1.27-alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
