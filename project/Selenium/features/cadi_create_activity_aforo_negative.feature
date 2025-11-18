Feature: CADI - Validación de aforo negativo al crear actividad

  Scenario: Error al crear actividad con aforo -10 (min=1) en Deportes de Conjunto
    Given I am on the login page
    When I login with username "5544" and password "5544"
    And I open CADI management from the home card
    And I open the CADI category "Deportes de Conjunto"
    And I click "Agregar actividad" in the CADI list
    And I try to create a CADI activity with name "Prueba Aforo Negativo" type "Deportes de Conjunto" negative capacity -10 and requires "No"
    Then I should see a min-capacity warning on the CADI activity form