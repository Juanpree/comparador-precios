from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import requests
import os

load_dotenv()

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


def extension_permitida(nombre_archivo):
    return "." in nombre_archivo and nombre_archivo.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def subir_imagen_a_cloudinary(ruta_imagen):
    resultado = cloudinary.uploader.upload(ruta_imagen)
    return resultado["secure_url"]


def buscar_con_google_lens_url(url_imagen):
    url = "https://serpapi.com/search"

    parametros = {
        "engine": "google_lens",
        "url": url_imagen,
        "type": "products",
        "hl": "es",
        "country": "ar",
        "api_key": SERPAPI_KEY
    }

    respuesta = requests.get(url, params=parametros, timeout=30)
    respuesta.raise_for_status()

    datos = respuesta.json()

    resultados = []

    # SerpApi puede devolver resultados en distintas claves según el tipo de búsqueda.
    posibles_claves = [
        "visual_matches",
        "products",
        "shopping_results",
        "exact_matches"
    ]

    for clave in posibles_claves:
        if clave in datos and isinstance(datos[clave], list):
            for item in datos[clave]:

                precio = item.get("price")

                precio_texto = None
                precio_numero = None
                moneda = None

                if isinstance(precio, dict):
                    precio_texto = (
                        precio.get("value")
                        or precio.get("text")
                        or precio.get("amount")
                    )

                    precio_numero = (
                        precio.get("extracted_value")
                        or precio.get("amount")
                    )

                    moneda = precio.get("currency")

                elif isinstance(precio, str):
                    precio_texto = precio

                # Otros posibles campos donde puede venir el precio
                if not precio_texto:
                    precio_texto = (
                        item.get("price_text")
                        or item.get("extracted_price")
                        or item.get("displayed_price")
                    )

                # Si extracted_price viene como número
                if not precio_numero:
                    precio_numero = item.get("extracted_price")

                resultados.append({
                    "titulo": item.get("title", "Sin título"),
                    "fuente": item.get("source", "Fuente no disponible"),
                    "link": item.get("link"),
                    "precio": precio_texto,
                    "precio_numero": precio_numero,
                    "moneda": moneda,
                    "stock": item.get("in_stock"),
                    "imagen": item.get("thumbnail") or item.get("image")
                })

    # Dejamos primero los resultados que sí tienen precio
    resultados_con_precio = [r for r in resultados if r["precio"]]
    resultados_sin_precio = [r for r in resultados if not r["precio"]]

    resultados_con_precio.sort(
        key=lambda r: r["precio_numero"] if r["precio_numero"] is not None else float("inf")
    )

    return resultados_con_precio + resultados_sin_precio

def buscar_en_mercadolibre_por_titulo(titulo, limite=4):
    """
    Busca productos en Mercado Libre usando el título detectado por Lens.
    Devuelve resultados con precio real cuando la API pública responde.
    """
    url = "https://api.mercadolibre.com/sites/MLA/search"

    parametros = {
        "q": titulo,
        "limit": limite
    }

    try:
        respuesta = requests.get(url, params=parametros, timeout=15)

        if respuesta.status_code != 200:
            print("Mercado Libre API no respondió OK:", respuesta.status_code, respuesta.text)
            return []

        datos = respuesta.json()
        resultados = []

        for item in datos.get("results", []):
            precio = item.get("price")

            resultados.append({
                "titulo": item.get("title", "Sin título"),
                "fuente": "Mercado Libre",
                "link": item.get("permalink"),
                "precio": f"${precio}" if precio is not None else None,
                "precio_numero": precio,
                "moneda": item.get("currency_id"),
                "stock": None,
                "imagen": item.get("thumbnail")
            })

        return resultados

    except Exception as error:
        print("Error buscando en Mercado Libre:", error)
        return []

@app.route("/", methods=["GET", "POST"])
def index():
    resultados = []
    imagen_url = None
    mensaje = ""

    if request.method == "POST":
        archivo = request.files.get("imagen")

        if not archivo or archivo.filename == "":
            mensaje = "Tenés que subir o pegar una imagen."
        elif not extension_permitida(archivo.filename):
            mensaje = "Formato no permitido. Usá PNG, JPG, JPEG o WEBP."
        else:
            nombre_seguro = secure_filename(archivo.filename)
            ruta_archivo = os.path.join(app.config["UPLOAD_FOLDER"], nombre_seguro)
            archivo.save(ruta_archivo)

            try:
                imagen_url = subir_imagen_a_cloudinary(ruta_archivo)
                resultados = buscar_con_google_lens_url(imagen_url)

                if len(resultados) == 0:
                    mensaje = "No se encontraron resultados para esa imagen."

            except requests.exceptions.RequestException as error:
                mensaje = f"Error consultando la búsqueda visual: {error}"

            except Exception as error:
                mensaje = f"Ocurrió un error: {error}"

    resultados_mercadolibre = []
    resultados_otros = []

    for item in resultados:
        link = item.get("link") or ""
        fuente = item.get("fuente") or ""

        link_lower = link.lower()
        fuente_lower = fuente.lower()

        es_mercadolibre = (
            "mercadolibre" in link_lower
            or "mercado libre" in fuente_lower
            or "mercado libre" in link_lower
            or "mercadolibre.com" in link_lower
            or "mercadolibre.com.ar" in link_lower
        )

        if es_mercadolibre:
            resultados_mercadolibre.append(item)
        else:
            precio = str(item.get("precio") or "")
            moneda = str(item.get("moneda") or "")

            precio_upper = precio.upper()
            moneda_upper = moneda.upper()

            es_dolares = (
                "US$" in precio_upper
                or "USD" in precio_upper
                or moneda_upper == "USD"
            )

            es_pesos = (
                "ARS" in precio_upper
                or moneda_upper == "ARS"
                or ("$" in precio_upper and not es_dolares)
            )

            if es_pesos and not es_dolares:
                resultados_otros.append(item)

    resultados_mercadolibre.sort(
        key=lambda r: r["precio_numero"] if r.get("precio_numero") is not None else float("inf")
    )

    resultados_otros.sort(
        key=lambda r: (
            0 if "carol argentina oficial" in str(r.get("fuente") or "").lower() else 1,
            r["precio_numero"] if r.get("precio_numero") is not None else float("inf")
        )
    )

    return render_template(
        "index.html",
        resultados_mercadolibre=resultados_mercadolibre,
        resultados_otros=resultados_otros,
        imagen_url=imagen_url,
        mensaje=mensaje
    )

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
