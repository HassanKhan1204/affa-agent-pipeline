# AFFA CRM UI — production-style container: build the static React app with
# Vite, then serve the compiled output with nginx. No Node.js in the final
# image — just static files.
#
# Build:  docker build -t affa-ui .
# Run:    docker run --rm -p 8080:80 affa-ui
#         (or: docker compose up ui)

FROM node:20-alpine AS build
WORKDIR /app

# Install dependencies first so this layer is cached across source changes.
COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
