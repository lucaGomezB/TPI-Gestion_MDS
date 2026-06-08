# =============================================================================
# Stage 1 — Build: compile the React SPA with Vite
# =============================================================================
FROM node:22-alpine AS build

WORKDIR /app

# Install dependencies first (leverages Docker layer caching)
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# =============================================================================
# Stage 2 — Serve: Nginx serving the built static files
# =============================================================================
FROM nginx:alpine AS serve

# Custom Nginx config with SPA fallback and API proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built artifacts from the build stage
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
