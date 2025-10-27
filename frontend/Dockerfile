# --- ETAPA 1: CONSTRUCCIÓN (BUILDER) ---
FROM node:18-alpine AS builder

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos solo los archivos de dependencias.
COPY package.json package-lock.json* ./

# Instalamos las dependencias
RUN npm install --legacy-peer-deps --unsafe-perm

# Copiamos el resto de los archivos fuente de Angular (src, angular.json, etc.)
COPY . .

# Construimos la aplicación de Angular.
# ¡EL CAMBIO CRÍTICO! Forzamos a ng a reconocer el proyecto 'frontend' 
# Construimos la aplicación de Angular.
# ¡EL CAMBIO FINAL! Usamos npm run build, que es el comando base en package.json,
# y le pasamos el límite de memoria (MAX_OLD_SPACE_SIZE) para asegurar el build.
RUN npm --max-old-space-size=4096 run build

# --- ETAPA 2: SERVIDOR (SERVING LIGERO) ---
FROM node:18-alpine 

# Configuramos el WORKDIR para el servidor final
WORKDIR /usr/share/frontend

# Instalamos el servidor simple de Node que soporta SPA
RUN npm install -g serve

# Copiamos los archivos estáticos COMPILADOS de la Etapa 1
COPY --from=builder /app/dist/final/ .

EXPOSE 8080 

# Iniciamos el servidor en el modo SPA (--single)
CMD ["serve", "-s", ".", "-l", "8080"]