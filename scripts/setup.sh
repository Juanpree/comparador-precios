#!/bin/bash

echo "Creando entorno virtual..."
python3 -m venv .venv

echo "Activando entorno virtual..."
source .venv/bin/activate

echo "Instalando dependencias..."
pip install -r requirements.txt

if [ ! -f .env ]; then
    echo "Creando archivo .env desde .env.example..."
    cp .env.example .env
    echo "Completá tus claves en el archivo .env"
fi

echo "Listo. Para correr el proyecto:"
echo "source .venv/bin/activate"
echo "python3 app.py"