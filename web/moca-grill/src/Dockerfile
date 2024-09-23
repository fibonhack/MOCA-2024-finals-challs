# build frontend
FROM node@sha256:7ce8b205d15e30fd395e5fa4000bcdf595fcff3f434fe75822e54e82a5f5cf82 as build-frontend

WORKDIR /app

COPY ./frontend/package.json ./
COPY ./frontend/package-lock.json ./
RUN npm install

COPY ./frontend/ ./
RUN npm run build

# Deploy everything
FROM nginx:latest

# Move backend
RUN apt-get update && apt-get install -y python3 python3-pip
WORKDIR /app
COPY ./backend/requirements.txt ./
RUN pip3 install --break-system-packages -r requirements.txt
COPY ./backend/ ./

WORKDIR /usr/share/nginx/html/
RUN rm -rf ./*

# move frontend in public directory
COPY --from=build-frontend /app/build ./
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY ./init.sh /app/init.sh

ENTRYPOINT [ "/app/init.sh" ]