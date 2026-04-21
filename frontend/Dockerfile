FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL
ENV DISABLE_HOT_RELOAD=true
ENV REACT_APP_ENABLE_VISUAL_EDITS=false
ENV ENABLE_HEALTH_CHECK=false

RUN npm run build
RUN npm install -g serve

CMD serve -s build -l tcp://0.0.0.0:${PORT:-3000}
