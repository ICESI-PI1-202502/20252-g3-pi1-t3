Feature: Analítica - Filtro de estado inexistente en gestión de asistencia

  Scenario: Registrar asistencia con identificadores inválidos debe mostrar alerta de errores
    Given I am on the login page
    When I login with username "1110287840" and password "123"
    And I open the sidebar menu
    And I go to attendance management from the analytics menu
    And I open the individual attendance register
    And I submit attendance for activity "Accesorios & Tejidos" with ids text "MALOMALO"
    Then I should see a warning alert indicating errors in attendance register
