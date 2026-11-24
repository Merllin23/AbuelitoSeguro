
const API_URL = "http://127.0.0.1:8000";
const ADULTO_ID = 1;

const secciones = document.querySelectorAll(".section");
const botones = document.querySelectorAll(".nav-item");

function cambiarSeccion(nombre) {
    secciones.forEach(section => {
        section.classList.toggle("active", section.id === nombre);
    });

    botones.forEach(button => {
        button.classList.toggle(
            "active",
            button.dataset.section === nombre
        );
    });

    const boton = [...botones].find(
        item => item.dataset.section === nombre
    );

    document.getElementById("page-title").textContent =
        boton.textContent.trim();

    cargarSeccion(nombre);
}

botones.forEach(button => {
    button.addEventListener("click", () => {
        cambiarSeccion(button.dataset.section);
    });
});

async function obtenerDatos(endpoint) {
    const respuesta = await fetch(`${API_URL}${endpoint}`);

    if (!respuesta.ok) {
        throw new Error(`Error HTTP: ${respuesta.status}`);
    }

    return await respuesta.json();
}

function mostrarError(id, mensaje) {
    document.getElementById(id).innerHTML =
        `<p class="empty">${mensaje}</p>`;
}

async function cargarDashboard() {
    try {
        const [adulto, medicamentos, confirmaciones, alertas] =
            await Promise.all([
                obtenerDatos(`/adultos/`),
                obtenerDatos(`/medicamentos/adulto/${ADULTO_ID}`),
                obtenerDatos(`/confirmaciones/adulto/${ADULTO_ID}`),
                obtenerDatos(`/alertas/adulto/${ADULTO_ID}`)
            ]);

        const datosAdulto = adulto.find(
            item => item.id === ADULTO_ID
        );

        if (!datosAdulto) {
            throw new Error("No se encontró el adulto mayor.");
        }

        document.getElementById("total-adultos").textContent = "1";
        document.getElementById("total-medicamentos").textContent =
            medicamentos.length;

        document.getElementById("total-confirmaciones").textContent =
            confirmaciones.length;

        document.getElementById("total-alertas").textContent =
            alertas.filter(item => item.estado === "pendiente").length;

        document.getElementById("familiar-nombre").textContent =
            datosAdulto.familiar_nombre;

        document.getElementById("resumen-adulto").innerHTML = `
            <div class="data-list">
                <div class="data-item">
                    <strong>Nombre:</strong> ${escaparHTML(datosAdulto.nombre)}
                </div>
                <div class="data-item">
                    <strong>Teléfono:</strong> ${escaparHTML(datosAdulto.telefono)}
                </div>
                <div class="data-item">
                    <strong>Familiar:</strong> ${escaparHTML(datosAdulto.familiar_nombre)}
                </div>
            </div>
        `;
    } catch (error) {
        console.error(error);
        mostrarError("resumen-adulto", "No se pudo cargar el resumen.");
    }
}

async function cargarAdulto() {
    try {
        const adultos = await obtenerDatos("/adultos/");
        const adulto = adultos.find(item => item.id === ADULTO_ID);

        if (!adulto) throw new Error("Adulto no encontrado.");

        document.getElementById("datos-adulto").innerHTML = `
            <div class="data-list">
                <div class="data-item"><strong>Nombre:</strong> ${escaparHTML(adulto.nombre)}</div>
                <div class="data-item"><strong>Teléfono:</strong> ${escaparHTML(adulto.telefono)}</div>
                <div class="data-item"><strong>Familiar:</strong> ${escaparHTML(adulto.familiar_nombre)}</div>
                <div class="data-item"><strong>Teléfono familiar:</strong> ${escaparHTML(adulto.familiar_telefono)}</div>
            </div>
        `;
    } catch (error) {
        console.error(error);
        mostrarError("datos-adulto", "No se pudieron cargar los datos.");
    }
}

async function cargarMedicamentos() {
    try {
        const datos = await obtenerDatos(
            `/medicamentos/adulto/${ADULTO_ID}`
        );

        document.getElementById("lista-medicamentos").innerHTML =
            datos.length
                ? `<div class="data-list">${datos.map(item => `
                    <div class="data-item">
                        <strong>${escaparHTML(item.nombre)}</strong><br>
                        Dosis: ${escaparHTML(item.dosis)}<br>
                        Horario: ${escaparHTML(item.horario)}
                    </div>
                `).join("")}</div>`
                : '<p class="empty">No hay medicamentos registrados.</p>';
    } catch (error) {
        console.error(error);
        mostrarError("lista-medicamentos", "No se pudieron cargar los medicamentos.");
    }
}

async function cargarConfirmaciones() {
    try {
        const datos = await obtenerDatos(
            `/confirmaciones/adulto/${ADULTO_ID}`
        );

        document.getElementById("lista-confirmaciones").innerHTML =
            datos.length
                ? `<div class="data-list">${datos.map(item => `
                    <div class="data-item">
                        <strong>${escaparHTML(item.mensaje)}</strong><br>
                        Estado: <span class="status">${escaparHTML(item.estado)}</span><br>
                        Fecha: ${formatearFecha(item.fecha)}
                    </div>
                `).join("")}</div>`
                : '<p class="empty">Todavía no hay confirmaciones.</p>';
    } catch (error) {
        console.error(error);
        mostrarError("lista-confirmaciones", "No se pudieron cargar las confirmaciones.");
    }
}

async function cargarAlertas() {
    try {
        const datos = await obtenerDatos(
            `/alertas/adulto/${ADULTO_ID}`
        );

        document.getElementById("lista-alertas").innerHTML =
            datos.length
                ? `<div class="data-list">${datos.map(item => `
                    <div class="data-item">
                        <strong>${escaparHTML(item.tipo)}</strong><br>
                        ${escaparHTML(item.mensaje)}<br>
                        Estado: <span class="status ${item.tipo === "prioritaria" ? "urgent" : "pending"}">${escaparHTML(item.estado)}</span><br>
                        Fecha: ${formatearFecha(item.fecha)}
                    </div>
                `).join("")}</div>`
                : '<p class="empty">No hay alertas registradas.</p>';
    } catch (error) {
        console.error(error);
        mostrarError("lista-alertas", "No se pudieron cargar las alertas.");
    }
}

async function cargarRecordatorios() {
    try {
        const datos = await obtenerDatos(
            `/recordatorios/adulto/${ADULTO_ID}`
        );

        document.getElementById("lista-recordatorios").innerHTML =
            datos.length
                ? `<div class="data-list">${datos.map(item => `
                    <div class="data-item">
                        <strong>${escaparHTML(item.mensaje)}</strong><br>
                        Estado: <span class="status">${escaparHTML(item.estado)}</span><br>
                        Programado: ${formatearFecha(item.fecha_programada)}
                    </div>
                `).join("")}</div>`
                : '<p class="empty">No hay recordatorios registrados.</p>';
    } catch (error) {
        console.error(error);
        mostrarError("lista-recordatorios", "No se pudieron cargar los recordatorios.");
    }
}

function escaparHTML(valor) {
    return String(valor ?? "").replace(/[&<>"']/g, caracter => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[caracter]);
}

function formatearFecha(fecha) {
    if (!fecha) return "No disponible";

    const valor = new Date(fecha);

    return Number.isNaN(valor.getTime())
        ? "No disponible"
        : valor.toLocaleString("es-PE");
}

async function cargarSeccion(nombre) {
    const funciones = {
        dashboard: cargarDashboard,
        adulto: cargarAdulto,
        medicamentos: cargarMedicamentos,
        confirmaciones: cargarConfirmaciones,
        alertas: cargarAlertas,
        recordatorios: cargarRecordatorios
    };

    await funciones[nombre]?.();
}

cargarDashboard();
