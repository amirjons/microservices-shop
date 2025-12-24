FROM node:18-alpine

WORKDIR /app

# Устанавливаем зависимости для сборки
RUN apk add --no-cache python3 make g++

# Копируем package.json и устанавливаем зависимости
COPY package.json ./
RUN npm install --no-audit --progress=false

# Копируем весь код и собираем
COPY . .
RUN npm run build

# Устанавливаем serve для статики
RUN npm install -g serve

EXPOSE 3000

# Запускаем сервер
CMD ["serve", "-s", "build", "-l", "3000"]