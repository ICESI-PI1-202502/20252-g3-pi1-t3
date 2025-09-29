  var registerButton = document.getElementById("registerButton");
    if (registerButton) {
      registerButton.addEventListener("click", function () {
        this.closest("form").submit(); // envía el formulario padre
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
          pwd.type = 'password';
          toggle.setAttribute('data-visible', 'false');
          toggle.setAttribute('aria-label', 'Mostrar contraseña');
          toggle.title = 'Mostrar contraseña';
          eye.style.display = 'inline';
          eyeOff.style.display = 'none';
        } else {
          pwd.type = 'text';
          toggle.setAttribute('data-visible', 'true');
          toggle.setAttribute('aria-label', 'Ocultar contraseña');
          toggle.title = 'Ocultar contraseña';
          eye.style.display = 'none';
          eyeOff.style.display = 'inline';
        }

        try {
          pwd.setSelectionRange(start, end);
          pwd.focus({ preventScroll: true });
        } catch (err) {
          pwd.focus();
        }
      });
    })();