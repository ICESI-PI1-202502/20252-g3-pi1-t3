const cedulaInput = document.getElementById("cedula");
    const passwordField = document.getElementById("passwordField");

    cedulaInput.addEventListener("input", function () {
        if (cedulaInput.value.trim() !== "") {
            passwordField.classList.remove("hidden");  // mostrar
        } else {
            passwordField.classList.add("hidden");     // ocultar
        }
    });

    var loginButton = document.getElementById("loginButton");
    if (loginButton) {
        loginButton.addEventListener("click", function () {
            this.closest("form").submit(); // envía el formulario padre
        });
    }

    var fieldContainer = document.getElementById("fieldContainer");
    if (fieldContainer) {
        fieldContainer.addEventListener("click", function (e) {
            // Add your code here JAVA SCRIPT NOpoasoaSOIosiaoiOS HELP DAMARALS
        });
    }

    var registrarseText = document.getElementById("registrarseText");
    if (registrarseText) {
        registrarseText.addEventListener("click", function (e) {
            window.location.href = "{% url 'register' %}";
        });
    }

    (function () {
        const toggle = document.getElementById('togglePassword');
        const pwd = document.getElementById('password');
        const eye = toggle.querySelector('.icon-eye');
        const eyeOff = toggle.querySelector('.icon-eye-off');

        if (!toggle || !pwd) return;

        // initial state: hidden
        toggle.setAttribute('data-visible', 'false');

        toggle.addEventListener('click', function () {
            const start = pwd.selectionStart;
            const end = pwd.selectionEnd;

            const isVisible = toggle.getAttribute('data-visible') === 'true';
            if (isVisible) {
                // ocultar contraseña
                pwd.type = 'password';
                toggle.setAttribute('data-visible', 'false');
                toggle.setAttribute('aria-label', 'Mostrar contraseña');
                toggle.title = 'Mostrar contraseña';

                // cambiar íconos
                eye.style.display = 'inline';
                eyeOff.style.display = 'none';
            } else {
                // mostrar contraseña
                pwd.type = 'text';
                toggle.setAttribute('data-visible', 'true');
                toggle.setAttribute('aria-label', 'Ocultar contraseña');
                toggle.title = 'Ocultar contraseña';

                // cambiar íconos
                eye.style.display = 'none';
                eyeOff.style.display = 'inline';
            }

            // restaurar caret
            try {
                pwd.setSelectionRange(start, end);
                pwd.focus({ preventScroll: true });
            } catch (err) {
                pwd.focus();
            }
        });
    })();