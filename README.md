# Comparador de Precios por Imagen

Aplicación web desarrollada con Flask que permite subir o pegar una imagen de un producto y buscar resultados similares en internet.

La app utiliza Cloudinary para subir temporalmente la imagen y SerpApi con Google Lens para obtener productos, precios y links relacionados.

---

## Funcionalidades

- Subir una imagen desde la computadora.
- Pegar una imagen con `Cmd + V` o `Ctrl + V`.
- Buscar productos similares por imagen.
- Mostrar resultados separados en pestañas:
  - Mercado Libre
  - Otras páginas en pesos argentinos
- Mostrar nombre del producto, fuente, precio, imagen y link.
- Filtrar resultados en dólares dentro de la sección de otras páginas.
- Destacar resultados de `Carol Argentina Oficial`.

---

## Tecnologías utilizadas

- Python
- Flask
- HTML
- CSS
- JavaScript
- Cloudinary
- SerpApi

---

## Estructura del proyecto

txt
comparador-precios/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
│
├── static/
│   ├── style.css
│   └── script.js
│
├── templates/
│   └── index.html
│
├── uploads/
│   └── .gitkeep
│
└── scripts/
    └── setup.sh
    
---

## Instalación rápida

Clonar el repositorio:

git clone https://github.com/Juanpree/comparador-precios.git
cd comparador-precios

Ejecutar el script de instalación:
./scripts/setup.sh

El script se encarga de:

Crear el entorno virtual .venv
Instalar las dependencias desde requirements.txt
Crear el archivo .env desde .env.example, si todavía no existe

Después de ejecutar el script, solo queda completar el archivo .env con tus claves reales.

---

## Instalación manual

También se puede instalar manualmente sin usar el script:

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

--- 

## Uso de IA

Este proyecto fue desarrollado con asistencia de herramientas de inteligencia artificial para apoyo en:

Estructura del proyecto
Generación y corrección de código
Depuración de errores
Documentación
Organización del flujo de trabajo

La implementación final, configuración de APIs, pruebas y ajustes funcionales fueron realizados manualmente.
