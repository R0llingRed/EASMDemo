FROM node:20-alpine AS build

WORKDIR /app/web

COPY web/package*.json ./
RUN npm ci

COPY web/ ./

ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_API_KEY=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_API_KEY=${VITE_API_KEY}

RUN npm run build

FROM nginx:1.27-alpine

COPY docker/nginx-web.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/web/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
