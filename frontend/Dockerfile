# Stage 1   
FROM node:22-alpine AS build

WORKDIR /frontend

COPY ./package*.json /frontend/
RUN npm install

COPY . /frontend/
RUN npm run build

# Stage 2
FROM nginx:alpine

COPY --from=build /frontend/dist/ /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]