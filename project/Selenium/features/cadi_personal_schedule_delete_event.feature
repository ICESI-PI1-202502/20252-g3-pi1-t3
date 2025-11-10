Feature: CADI - Eliminar evento en Horario (personal)

  Scenario: Eliminar "Accesorios & Tejidos" y ver toast de confirmación
    Given I am on the login page
    When I login with username "1112343789" and password "Daniel_123"
    And I open the sidebar menu
    And I go to the personal schedule page from the menu
    And I open the personal schedule event "Accesorios & Tejidos"
    And I delete the opened personal schedule event with confirmation
    Then I should see the personal schedule deletion toast for "Accesorios & Tejidos"
