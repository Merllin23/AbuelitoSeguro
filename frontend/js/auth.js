
document.addEventListener("DOMContentLoaded", () => {

    // Elementos compartidos
    const authMessage = document.getElementById("auth-message");

    /**
     * Mostrar mensajes en pantalla.
     */
    function mostrarMensaje(mensaje, tipo = "error") {
        if (!authMessage) return;

        authMessage.textContent = mensaje;
        authMessage.className = `auth-message ${tipo}`;
    }

    /**
     * Limpiar mensajes.
     */
    function limpiarMensaje() {
        if (!authMessage) return;

        authMessage.textContent = "";
        authMessage.className = "auth-message";
    }

    /**
     * Mostrar u ocultar contraseña.
     */
    function configurarTogglePassword(inputId, buttonId) {
        const input = document.getElementById(inputId);
        const button = document.getElementById(buttonId);

        if (!input || !button) return;

        button.addEventListener("click", () => {
            const mostrar = input.type === "password";

            input.type = mostrar ? "text" : "password";
            button.textContent = mostrar ? "Ocultar" : "Mostrar";
            button.setAttribute("aria-pressed", String(mostrar));
            button.setAttribute(
                "aria-label",
                mostrar ? "Ocultar contraseña" : "Mostrar contraseña"
            );
        });
    }

    configurarTogglePassword("password", "toggle-password");
    configurarTogglePassword(
        "confirmar-password",
        "toggle-confirm-password"
    );

    // -----------------------------------------
    // INICIO DE SESIÓN
    // -----------------------------------------

    const loginForm = document.getElementById("login-form");

    if (loginForm) {
        const loginButton = document.getElementById("login-button");

        loginForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            limpiarMensaje();

            const correo = document.getElementById("email").value.trim();
            const password = document.getElementById("password").value;

            if (!correo || !password) {
                mostrarMensaje("Completa todos los campos.");
                return;
            }

            loginButton.disabled = true;
            loginButton.textContent = "Ingresando...";

            try {
                const respuesta = await iniciarSesion({
                    correo,
                    password
                });

                if (!respuesta.access_token) {
                    throw new Error(
                        "El servidor no devolvió un token de autenticación."
                    );
                }

                guardarSesion(respuesta.access_token);

                mostrarMensaje("Inicio de sesión correcto.", "success");

                // El panel se creará en la siguiente etapa.
                window.location.href = "index.html";

            } catch (error) {
                mostrarMensaje(error.message);
            } finally {
                loginButton.disabled = false;
                loginButton.textContent = "Iniciar sesión";
            }
        });
    }

    // -----------------------------------------
    // REGISTRO DE FAMILIAR
    // -----------------------------------------

    const registerForm = document.getElementById("register-form");

    if (registerForm) {
        const registerButton = document.getElementById("register-button");

        registerForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            limpiarMensaje();

            const nombre = document.getElementById("nombre").value.trim();
            const correo = document.getElementById("correo").value.trim();
            const telefono = document.getElementById("telefono").value.trim();
            const password = document.getElementById("password").value;
            const confirmarPassword = document.getElementById(
                "confirmar-password"
            ).value;

            if (!nombre || !correo || !telefono || !password || !confirmarPassword) {
                mostrarMensaje("Completa todos los campos.");
                return;
            }

            if (password.length < 8) {
                mostrarMensaje("La contraseña debe tener al menos 8 caracteres.");
                return;
            }

            if (password !== confirmarPassword) {
                mostrarMensaje("Las contraseñas no coinciden.");
                return;
            }

            registerButton.disabled = true;
            registerButton.textContent = "Creando cuenta...";

            try {
                await registrarFamiliar({
                    nombre,
                    correo,
                    telefono,
                    password
                });

                mostrarMensaje(
                    "Cuenta creada correctamente. Ahora puedes iniciar sesión.",
                    "success"
                );

                registerForm.reset();

                // Cambiar a login únicamente después de mostrar el resultado.
                const switchContainer = document.querySelector(".auth-switch");

                if (switchContainer) {
                    switchContainer.innerHTML =
                        'Ya tienes tu cuenta. <a href="login.html">Iniciar sesión</a>';
                }

            } catch (error) {
                mostrarMensaje(error.message);
            } finally {
                registerButton.disabled = false;
                registerButton.textContent = "Crear cuenta";
            }
        });
    }

});
