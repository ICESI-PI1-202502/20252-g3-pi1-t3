Feature: CADI - Horario unificado BU

  Scenario: Abrir evento y ver el título en el modal
    Given I am on the login page
    When I login with username "488192423" and password "Daniel_2005"
    And I open the sidebar menu
    And I go to the unified schedule page from the menu
    And I open the unified schedule event "Fútbol Masculino (Avanzado)"
    Then I should see the unified schedule modal title "Fútbol Masculino (Avanzado)"
