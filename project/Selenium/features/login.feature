Feature: Login functionality

  Scenario: CF-A1.1 - Login exitoso
    Given I am on the login page
    When I login with username "123" and password "123"
    Then I should see the user calendar

  Scenario: CF-A1.2 - Contraseña incorrecta
    Given I am on the login page
    When I login with username "123" and password "456"
    Then I should see an incorrect password message

  Scenario: CF-A1.3 - Usuario no registrado
    Given I am on the login page
    When I login with username "6673" and password "clave123"
    Then I should see a user not found message

  Scenario: CF-A5 - Login como administrador
    Given I am on the login page
    When I login with username "1113624957" and password "00"
    Then I should see the admin panel
