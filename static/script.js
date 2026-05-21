document.addEventListener("DOMContentLoaded", function () {
    const formulario = document.querySelector(".formulario");
    const inputImagen = document.querySelector("#imagen");
    const zonaPegado = document.querySelector("#zonaPegado");
    const previewContainer = document.querySelector("#previewContainer");
    const previewImagen = document.querySelector("#previewImagen");

    function mostrarPreview(archivo) {
        const lector = new FileReader();

        lector.onload = function (evento) {
            previewImagen.src = evento.target.result;
            previewContainer.style.display = "block";
        };

        lector.readAsDataURL(archivo);
    }

    function cargarArchivoEnInput(archivo) {
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(archivo);
        inputImagen.files = dataTransfer.files;

        mostrarPreview(archivo);
    }

    document.addEventListener("paste", function (event) {
        const items = event.clipboardData.items;

        for (let i = 0; i < items.length; i++) {
            const item = items[i];

            if (item.type.startsWith("image/")) {
                const archivo = item.getAsFile();

                if (archivo) {
                    cargarArchivoEnInput(archivo);
                    zonaPegado.classList.add("imagen-cargada");
                    zonaPegado.innerHTML = `
                        <p><strong>Imagen pegada correctamente.</strong></p>
                        <p>Ahora podés buscar precios.</p>
                    `;
                }

                return;
            }
        }

        alert("No se detectó ninguna imagen en el portapapeles.");
    });

    inputImagen.addEventListener("change", function () {
        if (inputImagen.files.length > 0) {
            mostrarPreview(inputImagen.files[0]);
            zonaPegado.classList.add("imagen-cargada");
            zonaPegado.innerHTML = `
                <p><strong>Imagen seleccionada correctamente.</strong></p>
                <p>Ahora podés buscar precios.</p>
            `;
        }
    });

    formulario.addEventListener("submit", function (event) {
        if (inputImagen.files.length === 0) {
            event.preventDefault();
            alert("Tenés que subir o pegar una imagen.");
        }
    });

    // Tabs de resultados: Mercado Libre / Todo el menú
    const botonesTabs = document.querySelectorAll(".tab-btn");
    const contenidosTabs = document.querySelectorAll(".tab-contenido");

    botonesTabs.forEach(function (boton) {
        boton.addEventListener("click", function () {
            const tabSeleccionada = boton.dataset.tab;

            botonesTabs.forEach(function (btn) {
                btn.classList.remove("activo");
            });

            contenidosTabs.forEach(function (contenido) {
                contenido.classList.remove("activo");
            });

            boton.classList.add("activo");

            const contenidoActivo = document.querySelector("#tab-" + tabSeleccionada);

            if (contenidoActivo) {
                contenidoActivo.classList.add("activo");
            }
        });
    });
});