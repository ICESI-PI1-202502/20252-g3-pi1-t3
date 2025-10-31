Feature: Registro de usuario

  Scenario: CF-A3 - Registro de usuario con datos válidos
    Given I am on the register page
    When I register with cedula "1122334455", nombre "Juan Pérez", email "usuario@correo.com" and password "nuevaClave"
    Then I should see a success message "Usuario registrado con éxito. Ahora puede iniciar sesión."

  Scenario: CF-A4 - Error de registro por campo faltante
    Given I am on the register page
    When I register with cedula "1234567890", nombre "Ana Gómez", email "usuario@correo.com" and password ""
    Then I should see a required field error
