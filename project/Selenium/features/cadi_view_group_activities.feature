Feature: CADI - Visualización de actividades grupales disponibles

  Scenario: Ver "Baloncesto (Nivel Avanzado)" en Deportes de Conjunto
    Given I am on the login page
    When I login with username "1113624957" and password "00"
    And I open CADI management from the home card
    And I open the CADI category "Deportes de Conjunto"
    Then I should see the CADI activity titled "Baloncesto (Nivel Avanzado)" in the list
