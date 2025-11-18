Feature: CADI - Horario (personal)

  Scenario: Abrir evento "Accesorios & Tejidos" y ver detalle Título en el modal
    Given I am on the login page
    When I login with username "1112343789" and password "contraseña"
    And I open the sidebar menu
    And I go to the personal schedule page from the menu
    And I open the personal schedule event "Accesorios & Tejidos"
    Then I should see the personal schedule modal title detail "Accesorios & Tejidos"
