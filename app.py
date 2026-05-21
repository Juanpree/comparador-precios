from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import requests
import os
import unicodedata

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


def detectar_oferta(item):
    texto = (
        str(item.get("titulo") or "") + " " +
        str(item.get("fuente") or "") + " " +
        str(item.get("precio") or "") + " " +
        str(item.get("snippet") or "") + " " +
        str(item.get("precio_anterior") or "")
    ).lower()

    palabras_oferta = [
        "oferta",
        "promo",
        "promoción",
        "descuento",
        "rebaja",
        "sale",
        "hot sale",
        "cyber",
        "liquidación",
        "% off",
        "off"
    ]

    return any(palabra in texto for palabra in palabras_oferta)


def extraer_precio(item):
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

    if not precio_texto:
        precio_texto = (
            item.get("price_text")
            or item.get("extracted_price")
            or item.get("displayed_price")
        )

    if not precio_numero:
        precio_numero = item.get("extracted_price")

    precio_anterior = (
        item.get("old_price")
        or item.get("original_price")
        or item.get("extracted_old_price")
        or item.get("previous_price")
        or item.get("original_price_text")
    )

    return precio_texto, precio_numero, moneda, precio_anterior


def armar_resultado(item):
    precio_texto, precio_numero, moneda, precio_anterior = extraer_precio(item)

    resultado = {
        "titulo": item.get("title", "Sin título"),
        "fuente": item.get("source", "Fuente no disponible"),
        "link": item.get("link") or item.get("product_link"),
        "precio": precio_texto,
        "precio_numero": precio_numero,
        "moneda": moneda,
        "stock": item.get("in_stock"),
        "imagen": item.get("thumbnail") or item.get("image"),
        "snippet": item.get("snippet") or item.get("description") or "",
        "precio_anterior": precio_anterior
    }

    resultado["oferta"] = detectar_oferta(resultado) or bool(precio_anterior)

    return resultado


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

    posibles_claves = [
        "visual_matches",
        "products",
        "shopping_results",
        "exact_matches"
    ]

    for clave in posibles_claves:
        if clave in datos and isinstance(datos[clave], list):
            for item in datos[clave]:
                resultado = armar_resultado(item)
                resultados.append(resultado)

    resultados_con_precio = [r for r in resultados if r["precio"]]
    resultados_sin_precio = [r for r in resultados if not r["precio"]]

    resultados_con_precio.sort(
        key=lambda r: r["precio_numero"] if r.get("precio_numero") is not None else float("inf")
    )

    return resultados_con_precio + resultados_sin_precio


def buscar_en_mercadolibre_por_titulo(titulo, limite=4):
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

            resultado = {
                "titulo": item.get("title", "Sin título"),
                "fuente": "Mercado Libre",
                "link": item.get("permalink"),
                "precio": f"${precio}" if precio is not None else None,
                "precio_numero": precio,
                "moneda": item.get("currency_id"),
                "stock": None,
                "imagen": item.get("thumbnail"),
                "snippet": "",
                "precio_anterior": None
            }

            resultado["oferta"] = detectar_oferta(resultado)

            resultados.append(resultado)

        return resultados

    except Exception as error:
        print("Error buscando en Mercado Libre:", error)
        return []


def normalizar_texto(texto):
    texto = str(texto or "").lower()
    texto = texto.replace(",", ".")
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto


def coincide_con_filtro(item, consulta):
    consulta = normalizar_texto(consulta)

    if not consulta:
        return True

    texto_item = normalizar_texto(
        f"{item.get('titulo', '')} "
        f"{item.get('fuente', '')} "
        f"{item.get('precio', '')}"
    )

    palabras = consulta.split()

    for palabra in palabras:
        if palabra not in texto_item:
            return False

    return True


def buscar_por_texto(consulta):
    url = "https://serpapi.com/search"

    parametros = {
        "engine": "google_shopping",
        "q": consulta,
        "hl": "es",
        "gl": "ar",
        "api_key": SERPAPI_KEY
    }

    respuesta = requests.get(url, params=parametros, timeout=30)
    respuesta.raise_for_status()

    datos = respuesta.json()
    resultados = []

    posibles_claves = [
        "shopping_results",
        "products"
    ]

    for clave in posibles_claves:
        if clave in datos and isinstance(datos[clave], list):
            for item in datos[clave]:
                resultado = armar_resultado(item)
                resultados.append(resultado)

    return resultados


@app.route("/", methods=["GET", "POST"])
def index():
    resultados = []
    imagen_url = None
    mensaje = ""
    consulta = ""

    if request.method == "POST":
        archivo = request.files.get("imagen")
        consulta = request.form.get("consulta", "").strip()

        hay_imagen = archivo and archivo.filename != ""
        hay_consulta = consulta != ""

        if not hay_imagen and not hay_consulta:
            mensaje = "Tenés que subir una imagen, pegar una imagen o escribir una búsqueda."

        elif hay_imagen and not extension_permitida(archivo.filename):
            mensaje = "Formato no permitido. Usá PNG, JPG, JPEG o WEBP."

        else:
            try:
                if hay_imagen:
                    nombre_seguro = secure_filename(archivo.filename)
                    ruta_archivo = os.path.join(app.config["UPLOAD_FOLDER"], nombre_seguro)
                    archivo.save(ruta_archivo)

                    imagen_url = subir_imagen_a_cloudinary(ruta_archivo)
                    resultados = buscar_con_google_lens_url(imagen_url)


                else:
                    resultados = buscar_por_texto(consulta)

                if len(resultados) == 0:
                    mensaje = "No se encontraron resultados para esa búsqueda."

            except requests.exceptions.RequestException as error:
                mensaje = f"Error consultando la búsqueda: {error}"

            except Exception as error:
                mensaje = f"Ocurrió un error: {error}"

    resultados_mercadolibre = []
    resultados_otros = []

    for item in resultados:
        link = item.get("link") or ""
        fuente = item.get("fuente") or ""
        precio = str(item.get("precio") or "")
        moneda = str(item.get("moneda") or "")

        link_lower = link.lower()
        fuente_lower = fuente.lower()

        precio_upper = precio.upper()
        moneda_upper = moneda.upper()
        fuente_upper = fuente.upper()
        link_upper = link.upper()

        es_mercadolibre = (
            "mercadolibre" in link_lower
            or "mercado libre" in fuente_lower
            or "mercado libre" in link_lower
            or "mercadolibre.com" in link_lower
            or "mercadolibre.com.ar" in link_lower
        )

        es_dolares = (
            "US$" in precio_upper
            or "USD" in precio_upper
            or moneda_upper == "USD"
        )

        es_pesos_argentinos = (
            "ARS" in precio_upper
            or moneda_upper == "ARS"
        )

        es_mercadolibre_no_argentina = (
            "PERÚ" in fuente_upper
            or "PERU" in fuente_upper
            or "PEN" in precio_upper
            or moneda_upper == "PEN"
            or "MERCADOLIBRE.COM.PE" in link_upper
        )

        if es_mercadolibre:
            if not es_mercadolibre_no_argentina:
                resultados_mercadolibre.append(item)
        else:
            es_pesos = (
                es_pesos_argentinos
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
        mensaje=mensaje,
        consulta=consulta
    )


if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    app.run(debug=True)