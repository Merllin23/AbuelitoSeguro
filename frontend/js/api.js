
const API_BASE_URL = "http://127.0.0.1:8000";

/**
 * Función central para realizar peticiones al backend.
 */
async function apiRequest(endpoint, {
    method = "GET",
    body = null,
    auth = false
} = {}) {

    const headers = {};

    // Agregar token JWT cuando el endpoint requiere autenticación.
    if (auth) {
        const token = sessionStorage.getItem("access_token");

        if (!token) {
            throw new Error("Tu sesión ha expirado. Inicia sesión nuevamente.");
        }

        headers["Authorization"] = `Bearer ${token}`;
    }

    const options = {
        method,
        headers
    };

    // Permitir enviar JSON o FormData.
    if (body !== null) {
        if (body instanceof FormData) {
            options.body = body;
        } else {
            headers["Content-Type"] = "application/json";
            options.body = JSON.stringify(body);
        }
    }

    let response;

    try {
        response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    } catch (error) {
        throw new Error(
            "No se pudo conectar con el servidor. Verifica que FastAPI esté ejecutándose."
        );
    }

    // Leer la respuesta sin asumir que siempre contiene JSON.
    const responseText = await response.text();

    let data = null;

    if (responseText) {
        try {
            data = JSON.parse(responseText);
        } catch {
            data = responseText;
        }
    }

    if (!response.ok) {
        let message = "Ocurrió un error al procesar la solicitud.";

        if (typeof data === "string") {
            message = data;
        } else if (data?.detail) {
            if (Array.isArray(data.detail)) {
                message = data.detail
                    .map(error => error.msg || "Dato inválido")
                    .join(". ");
            } else {
                message = data.detail;
            }
        }

        throw new Error(message);
    }

    return data;
}

/**
 * Registrar un nuevo familiar.
 */
async function registrarFamiliar(datos) {
    return apiRequest("/familiares/registro", {
        method: "POST",
        body: datos
    });
}

/**
 * Iniciar sesión de un familiar.
 */
async function iniciarSesion(datos) {
    return apiRequest("/familiares/login", {
        method: "POST",
        body: datos
    });
}

/**
 * Obtener los datos del familiar autenticado.
 */
async function obtenerPerfil() {
    return apiRequest("/familiares/me", {
        auth: true
    });
}

/**
 * Guardar el token de autenticación.
 */
function guardarSesion(token) {
    sessionStorage.setItem("access_token", token);
}

/**
 * Cerrar la sesión actual.
 */
function cerrarSesion() {
    sessionStorage.removeItem("access_token");
}
