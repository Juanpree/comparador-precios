document.addEventListener("DOMContentLoaded", function () {
    const formulario = document.querySelector(".formulario");
    const inputImagen = document.querySelector("#imagen");
    const zonaPegado = document.querySelector("#zonaPegado");
    const previewContainer = document.querySelector("#previewContainer");
    const previewImagen = document.querySelector("#previewImagen");
    const inputConsulta = document.querySelector("#consulta");

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
        const hayImagen = inputImagen.files.length > 0;
        const hayTexto = inputConsulta.value.trim() !== "";

        if (!hayImagen && !hayTexto) {
            event.preventDefault();
            alert("Tenés que subir una imagen, pegar una imagen o escribir una búsqueda.");
        }
    });

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

    // Filtros dinámicos sin volver a consultar la API
    const panelFiltros = document.querySelector(".filtros-dinamicos");
    const inputNuevoFiltro = document.querySelector("#nuevoFiltro");
    const btnAgregarFiltro = document.querySelector("#btnAgregarFiltro");
    const chipsFiltros = document.querySelector("#chipsFiltros");
    const contadorFiltros = document.querySelector("#contadorFiltros");
    const tarjetasProductos = document.querySelectorAll(".producto-card");

    let filtrosActivos = [];

    function normalizarTexto(texto) {
        return texto
            .toString()
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(",", ".")
            .trim();
    }

    function renderizarFiltros() {
        if (!chipsFiltros) return;

        chipsFiltros.innerHTML = "";

        filtrosActivos.forEach(function (filtro, index) {
            const chip = document.createElement("button");
            chip.type = "button";
            chip.className = "chip-filtro";
            chip.innerHTML = `${filtro} <span>×</span>`;

            chip.addEventListener("click", function () {
                filtrosActivos.splice(index, 1);
                aplicarFiltros();
            });

            chipsFiltros.appendChild(chip);
        });
    }

    function aplicarFiltros() {
        let visibles = 0;

        tarjetasProductos.forEach(function (tarjeta) {
            const textoTarjeta = normalizarTexto(tarjeta.dataset.search || "");

            const coincide = filtrosActivos.every(function (filtro) {
                return textoTarjeta.includes(normalizarTexto(filtro));
            });

            if (coincide) {
                tarjeta.style.display = "";
                visibles++;
            } else {
                tarjeta.style.display = "none";
            }
        });

        renderizarFiltros();

        if (contadorFiltros) {
            if (filtrosActivos.length === 0) {
                contadorFiltros.textContent = "Sin filtros activos.";
            } else {
                contadorFiltros.textContent = `Mostrando ${visibles} resultado(s) con los filtros aplicados.`;
            }
        }
    }

    function agregarFiltroDesdeInput() {
        if (!inputNuevoFiltro) return;

        const texto = inputNuevoFiltro.value.trim();

        if (texto === "") return;

        const palabras = texto.split(/\s+/);

        palabras.forEach(function (palabra) {
            const filtroNormalizado = normalizarTexto(palabra);

            const yaExiste = filtrosActivos.some(function (filtro) {
                return normalizarTexto(filtro) === filtroNormalizado;
            });

            if (!yaExiste) {
                filtrosActivos.push(palabra);
            }
        });

        inputNuevoFiltro.value = "";
        aplicarFiltros();
    }

    if (btnAgregarFiltro) {
        btnAgregarFiltro.addEventListener("click", agregarFiltroDesdeInput);
    }

    if (inputNuevoFiltro) {
        inputNuevoFiltro.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                event.preventDefault();
                agregarFiltroDesdeInput();
            }
        });
    }

    if (panelFiltros) {
        const consultaInicial = panelFiltros.dataset.consultaInicial || "";

        if (consultaInicial.trim() !== "") {
            filtrosActivos = consultaInicial.trim().split(/\s+/);
        }

        aplicarFiltros();
    }
});