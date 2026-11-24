
document.addEventListener("DOMContentLoaded", async () => {

    // -----------------------------------------
    // ELEMENTOS Y ESTADO
    // -----------------------------------------

    const messageBox = document.getElementById("app-message");

    let familiar = null;
    let adultos = [];
    let medicamentos = [];
    let actividadActual = "confirmaciones";
    let adultoActividadId = null;

    const $ = (id) => document.getElementById(id);

    function mostrarMensaje(mensaje, tipo = "error") {
        messageBox.textContent = mensaje;
        messageBox.className = `app-message ${tipo}`;

        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    function limpiarMensaje() {
        messageBox.textContent = "";
        messageBox.className = "app-message";
    }

    function mostrarFecha() {
        $("current-date").textContent = new Intl.DateTimeFormat("es-PE", {
            weekday: "long",
            day: "numeric",
            month: "long",
            year: "numeric"
        }).format(new Date());
    }

    function formatearFecha(fecha) {
        if (!fecha) return "Fecha no disponible";

        const date = new Date(fecha);

        if (Number.isNaN(date.getTime())) return "Fecha no disponible";

        return new Intl.DateTimeFormat("es-PE", {
            day: "2-digit",
            month: "short",
            hour: "2-digit",
            minute: "2-digit"
        }).format(date);
    }

    function crearElemento(tag, className, texto = "") {
        const elemento = document.createElement(tag);
        elemento.className = className;
        elemento.textContent = texto;
        return elemento;
    }

    function obtenerDetalleMedicamento(registro) {
        if (!registro.medicamento_id) {
            return "Sin medicamento asociado";
        }

        const medicamento = medicamentos.find(
            item => Number(item.id) === Number(registro.medicamento_id)
        );

        if (!medicamento) {
            return `Medicamento #${registro.medicamento_id}`;
        }

        return `${medicamento.nombre} (${medicamento.dosis})`;
    }

    function esAlertaPendiente(alerta) {
        return String(alerta.estado || "pendiente").toLowerCase() !== "atendida";
    }

    // -----------------------------------------
    // AUTENTICACIÓN
    // -----------------------------------------

    if (!sessionStorage.getItem("access_token")) {
        window.location.replace("login.html");
        return;
    }

    $("logout-button").addEventListener("click", () => {
        cerrarSesion();
        window.location.replace("login.html");
    });

    // -----------------------------------------
    // NAVEGACIÓN
    // -----------------------------------------

    const titulos = {
        inicio: "Inicio",
        adultos: "Adultos mayores",
        medicamentos: "Medicamentos",
        actividad: "Actividad"
    };

    function cambiarVista(vista) {
        const seccion = $(`view-${vista}`);

        if (!seccion) return;

        document.querySelectorAll(".view").forEach(elemento => {
            elemento.classList.remove("active");
        });

        seccion.classList.add("active");

        document.querySelectorAll(".nav-item").forEach(boton => {
            boton.classList.toggle(
                "active",
                boton.dataset.view === vista
            );
        });

        $("page-title").textContent = titulos[vista];

        cerrarMenuMovil();
        limpiarMensaje();
    }

    document.querySelectorAll("[data-view]").forEach(boton => {
        boton.addEventListener("click", () => {
            cambiarVista(boton.dataset.view);
        });
    });

    // Menú móvil
    const sidebar = $("sidebar");
    const overlay = $("mobile-overlay");

    $("mobile-menu-button").addEventListener("click", () => {
        sidebar.classList.add("open");
        overlay.classList.add("active");
    });

    function cerrarMenuMovil() {
        sidebar.classList.remove("open");
        overlay.classList.remove("active");
    }

    overlay.addEventListener("click", cerrarMenuMovil);

    // -----------------------------------------
    // CARGA DEL PERFIL
    // -----------------------------------------

    async function cargarPerfil() {
        familiar = await obtenerPerfil();

        const nombre = familiar.nombre || "Familiar";

        $("welcome-title").textContent = `Bienvenido, ${nombre}`;
        $("sidebar-user-name").textContent = nombre;
        $("user-avatar").textContent = nombre.charAt(0).toUpperCase();
    }

    // -----------------------------------------
    // ADULTOS MAYORES
    // -----------------------------------------

    async function cargarAdultos() {
        adultos = await apiRequest("/adultos/", {
            auth: true
        });

        renderizarAdultos();
        actualizarSelectoresAdultos();

        $("stat-adults").textContent = adultos.length;
        $("adult-count").textContent = `${adultos.length} registrados`;
    }

    function renderizarAdultos() {
        const homeList = $("home-adults-list");
        const fullList = $("adults-list");

        homeList.replaceChildren();
        fullList.replaceChildren();

        if (!adultos.length) {
            const mensaje = "Todavía no tienes adultos mayores registrados.";

            homeList.appendChild(crearElemento("div", "empty-state", mensaje));
            fullList.appendChild(crearElemento("div", "empty-state", mensaje));

            return;
        }

        adultos.forEach(adulto => {
            const inicial = (adulto.nombre || "A").charAt(0).toUpperCase();

            const crearTarjeta = () => {
                const item = crearElemento("div", "adult-item");
                const main = crearElemento("div", "adult-item-main");

                const avatar = crearElemento("div", "adult-avatar", inicial);

                const info = crearElemento("div", "item-information");
                info.appendChild(crearElemento("strong", "", adulto.nombre));
                info.appendChild(crearElemento("span", "", adulto.telefono));

                main.append(avatar, info);

                item.append(
                    main,
                    crearElemento("span", "item-tag", "Registrado")
                );

                return item;
            };

            homeList.appendChild(crearTarjeta());
            fullList.appendChild(crearTarjeta());
        });
    }

    function actualizarSelectoresAdultos() {
        const selectores = [$("med-adult"), $("activity-adult")];

        selectores.forEach(select => {
            const valorAnterior = select.value;

            select.replaceChildren();

            const opcionInicial = document.createElement("option");
            opcionInicial.value = "";
            opcionInicial.textContent = "Selecciona un adulto";
            select.appendChild(opcionInicial);

            adultos.forEach(adulto => {
                const opcion = document.createElement("option");
                opcion.value = adulto.id;
                opcion.textContent = adulto.nombre;
                select.appendChild(opcion);
            });

            if (adultos.some(a => String(a.id) === valorAnterior)) {
                select.value = valorAnterior;
            }
        });
    }

    $("adult-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        limpiarMensaje();

        const button = $("adult-submit");

        const datos = {
            nombre: $("adult-name").value.trim(),
            telefono: $("adult-phone").value.trim()
        };

        if (!datos.nombre || !datos.telefono) {
            mostrarMensaje("Completa los datos del adulto mayor.");
            return;
        }

        button.disabled = true;
        button.textContent = "Registrando...";

        try {
            await apiRequest("/adultos/", {
                method: "POST",
                body: datos,
                auth: true
            });

            $("adult-form").reset();

            await cargarAdultos();

            mostrarMensaje("Adulto mayor registrado correctamente.", "success");

        } catch (error) {
            mostrarMensaje(error.message);
        } finally {
            button.disabled = false;
            button.textContent = "Registrar adulto";
        }
    });

    // -----------------------------------------
    // MEDICAMENTOS
    // -----------------------------------------

    async function cargarMedicamentos(adultoId = null) {
        medicamentos = [];

        const adultosConsulta = adultoId
            ? adultos.filter(a => String(a.id) === String(adultoId))
            : adultos;

        const resultados = await Promise.allSettled(
            adultosConsulta.map(adulto =>
                apiRequest(`/medicamentos/adulto/${adulto.id}`, {
                    auth: true
                })
            )
        );

        resultados.forEach((resultado, index) => {
            if (resultado.status === "fulfilled") {
                const lista = resultado.value;

                if (Array.isArray(lista)) {
                    lista.forEach(medicamento => {
                        medicamentos.push({
                            ...medicamento,
                            adulto_nombre: adultosConsulta[index].nombre
                        });
                    });
                }
            } else {
                console.error(
                    "No se pudieron cargar los medicamentos:",
                    resultado.reason
                );
            }
        });

        $("stat-medications").textContent = medicamentos.length;

        renderizarMedicamentos();
    }

    function renderizarMedicamentos() {
        const container = $("medications-list");
        container.replaceChildren();

        if (!adultos.length) {
            container.appendChild(
                crearElemento("div", "empty-state", "Primero registra un adulto mayor.")
            );
            return;
        }

        if (!medicamentos.length) {
            container.appendChild(
                crearElemento("div", "empty-state", "No hay medicamentos registrados.")
            );
            return;
        }

        medicamentos.forEach(medicamento => {
            const item = crearElemento("div", "medication-item");
            const main = crearElemento("div", "medication-item-main");

            const icon = crearElemento("div", "adult-avatar", "+");

            const info = crearElemento("div", "item-information");
            info.appendChild(
                crearElemento("strong", "", medicamento.nombre)
            );
            info.appendChild(
                crearElemento(
                    "span",
                    "",
                    `${medicamento.dosis} · ${medicamento.adulto_nombre}`
                )
            );

            main.append(icon, info);

            item.append(
                main,
                crearElemento("span", "item-tag", medicamento.horario)
            );

            container.appendChild(item);
        });
    }

    $("medication-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        limpiarMensaje();

        const button = $("medication-submit");

        const adultoId = $("med-adult").value;

        if (!adultoId) {
            mostrarMensaje("Selecciona un adulto mayor.");
            return;
        }

        const datos = {
            nombre: $("med-name").value.trim(),
            dosis: $("med-dose").value.trim(),
            horario: $("med-time").value,
            adulto_id: Number(adultoId)
        };

        if (!datos.nombre || !datos.dosis || !datos.horario) {
            mostrarMensaje("Completa todos los datos del medicamento.");
            return;
        }

        button.disabled = true;
        button.textContent = "Registrando...";

        try {
            await apiRequest("/medicamentos/", {
                method: "POST",
                body: datos,
                auth: true
            });

            $("medication-form").reset();

            await cargarMedicamentos();

            mostrarMensaje("Medicamento registrado correctamente.", "success");

        } catch (error) {
            mostrarMensaje(error.message);
        } finally {
            button.disabled = false;
            button.textContent = "Registrar medicamento";
        }
    });

    // -----------------------------------------
    // ACTIVIDAD
    // -----------------------------------------

    async function cargarActividad(tipo, adultoId) {
        const rutas = {
            confirmaciones: `/confirmaciones/adulto/${adultoId}`,
            alertas: `/alertas/adulto/${adultoId}`,
            recordatorios: `/recordatorios/adulto/${adultoId}`
        };

        const resultado = await apiRequest(rutas[tipo], {
            auth: true
        });

        return Array.isArray(resultado) ? resultado : [];
    }

    function renderizarActividad(lista, tipo, container) {
        container.replaceChildren();

        if (!lista.length) {
            container.appendChild(
                crearElemento("div", "empty-state", "No hay registros disponibles en esta categoría.")
            );
            return;
        }

        lista.forEach(registro => {
            const item = crearElemento("div", "activity-item");
            const marker = crearElemento("div", "activity-marker");
            const copy = crearElemento("div", "activity-copy");

            let titulo = "";
            let detalle = "";

            const fecha = registro.fecha ||
                registro.fecha_programada ||
                registro.fecha_creacion;

            if (tipo === "confirmaciones") {
                titulo = registro.estado || "Confirmación";
                const medicamento = obtenerDetalleMedicamento(registro);
                detalle = `${medicamento} · ${registro.mensaje || "Sin mensaje"}`;

            } else if (tipo === "alertas") {
                titulo = registro.tipo || "Alerta";
                detalle = registro.mensaje || "Sin descripción";
                marker.style.background = "var(--red)";

            } else {
                titulo = "Recordatorio";
                detalle = registro.mensaje || "Sin mensaje";
            }

            copy.appendChild(crearElemento("strong", "", titulo));
            copy.appendChild(crearElemento("span", "", detalle));

            const right = crearElemento(
                "div",
                "activity-date",
                formatearFecha(fecha)
            );

            item.append(marker, copy, right);

            // Estado y botón de atención de alertas
            if (tipo === "alertas") {

                if (esAlertaPendiente(registro)) {
                    const boton = crearElemento(
                        "button",
                        "alert-action-button",
                        "Marcar como atendida"
                    );

                    boton.type = "button";

                    boton.addEventListener("click", async () => {
                        boton.disabled = true;
                        boton.textContent = "Actualizando...";

                        try {
                            await apiRequest(
                                `/alertas/${registro.id}/atender`,
                                {
                                    method: "PATCH",
                                    auth: true
                                }
                            );

                            await consultarActividad();
                            await cargarResumenActividad();

                            mostrarMensaje(
                                "Alerta marcada como atendida.",
                                "success"
                            );

                        } catch (error) {
                            mostrarMensaje(error.message);

                            boton.disabled = false;
                            boton.textContent = "Marcar como atendida";
                        }
                    });

                    item.appendChild(boton);

                } else {
                    const estado = crearElemento(
                        "span",
                        "status-tag confirmed",
                        "Atendida"
                    );

                    item.appendChild(estado);
                }
            }

            container.appendChild(item);
        });
    }

    async function consultarActividad() {
        const adultoId = $("activity-adult").value;
        const container = $("activity-results");

        container.replaceChildren();

        if (!adultoId) {
            container.appendChild(
                crearElemento("div", "empty-state", "Selecciona un adulto mayor.")
            );
            return;
        }

        adultoActividadId = adultoId;

        container.appendChild(
            crearElemento("div", "loading-state", "Consultando actividad...")
        );

        try {
            const lista = await cargarActividad(actividadActual, adultoId);

            renderizarActividad(lista, actividadActual, container);

        } catch (error) {
            container.replaceChildren();
            container.appendChild(
                crearElemento("div", "empty-state", error.message)
            );
        }
    }

    $("load-activity").addEventListener("click", consultarActividad);

    document.querySelectorAll("[data-activity]").forEach(button => {
        button.addEventListener("click", () => {
            actividadActual = button.dataset.activity;

            document.querySelectorAll(".activity-tab").forEach(tab => {
                tab.classList.toggle("active", tab === button);
            });

            if (adultoActividadId) {
                $("activity-adult").value = adultoActividadId;
                consultarActividad();
            }
        });
    });

    // -----------------------------------------
    // RESUMEN DEL INICIO
    // -----------------------------------------

    async function cargarResumenActividad() {
        const container = $("home-activity-list");
        container.replaceChildren();

        if (!adultos.length) {
            container.appendChild(
                crearElemento("div", "empty-state", "Registra un adulto para consultar su actividad.")
            );
            $("stat-alerts").textContent = "0";
            return;
        }

        const consultas = adultos.map(async adulto => {
            const [confirmaciones, alertas, recordatorios] = await Promise.all([
                cargarActividad("confirmaciones", adulto.id),
                cargarActividad("alertas", adulto.id),
                cargarActividad("recordatorios", adulto.id)
            ]);

            return [
                ...confirmaciones.map(item => ({
                    ...item,
                    tipoActividad: "confirmaciones",
                    adultoNombre: adulto.nombre
                })),
                ...alertas.map(item => ({
                    ...item,
                    tipoActividad: "alertas",
                    adultoNombre: adulto.nombre
                })),
                ...recordatorios.map(item => ({
                    ...item,
                    tipoActividad: "recordatorios",
                    adultoNombre: adulto.nombre
                }))
            ];
        });

        const resultados = await Promise.allSettled(consultas);

        const registros = [];
        let totalAlertas = 0;

        resultados.forEach(resultado => {
            if (resultado.status === "fulfilled") {

                const actividadVisible = resultado.value.filter(item => {
                    return item.tipoActividad !== "alertas" ||
                        esAlertaPendiente(item);
                });

                registros.push(...actividadVisible);

                totalAlertas += actividadVisible.filter(
                    item => item.tipoActividad === "alertas"
                ).length;
            }
        });

        $("stat-alerts").textContent = totalAlertas;

        registros.sort((a, b) => {
            const fechaA = new Date(
                a.fecha || a.fecha_programada || a.fecha_creacion || 0
            ).getTime();

            const fechaB = new Date(
                b.fecha || b.fecha_programada || b.fecha_creacion || 0
            ).getTime();

            return fechaB - fechaA;
        });

        if (!registros.length) {
            container.appendChild(
                crearElemento("div", "empty-state", "Todavía no hay actividad registrada.")
            );
            return;
        }

        registros.slice(0, 5).forEach(registro => {
            const tipo = registro.tipoActividad;

            const titulo = tipo === "alertas"
                ? registro.tipo || "Alerta"
                : tipo === "confirmaciones"
                    ? registro.estado || "Confirmación"
                    : "Recordatorio";

            let detalle;

            if (tipo === "confirmaciones") {
                const medicamento = obtenerDetalleMedicamento(registro);

                detalle = `${registro.adultoNombre} · ${medicamento} · ${registro.mensaje || "Sin mensaje"}`;
            } else {
                detalle = `${registro.adultoNombre}: ${registro.mensaje || "Sin descripción"}`;
            }

            const item = crearElemento("div", "activity-item");
            const marker = crearElemento("div", "activity-marker");

            if (tipo === "alertas") {
                marker.style.background = "var(--red)";
            }

            const copy = crearElemento("div", "activity-copy");
            copy.appendChild(crearElemento("strong", "", titulo));
            copy.appendChild(crearElemento("span", "", detalle));

            item.append(
                marker,
                copy,
                crearElemento(
                    "div",
                    "activity-date",
                    formatearFecha(
                        registro.fecha ||
                        registro.fecha_programada ||
                        registro.fecha_creacion
                    )
                )
            );

            container.appendChild(item);
        });
    }

    // -----------------------------------------
    // INICIALIZACIÓN
    // -----------------------------------------

    mostrarFecha();

    try {
        await cargarPerfil();
        await cargarAdultos();

        await cargarMedicamentos();
        await cargarResumenActividad();

    } catch (error) {
        console.error(error);

        if (
            error.message.toLowerCase().includes("sesión") ||
            error.message.toLowerCase().includes("token") ||
            error.message.toLowerCase().includes("autentic")
        ) {
            cerrarSesion();
            window.location.replace("login.html");
            return;
        }

        mostrarMensaje(
            `No se pudo cargar el panel: ${error.message}`
        );
    }

});
