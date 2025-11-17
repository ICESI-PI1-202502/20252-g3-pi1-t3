Feature: CADI - Validación al crear actividad (campos vacíos)

  Scenario: Error al crear actividad dejando el nombre vacío
    Given I am on the login page
    When I login with username "1110287840" and password "123"
    And I open CADI management from the home card
    And I open the CADI category "Deportes de Conjunto"
    And I click "Agregar actividad" in the CADI list
    And I try to create the CADI activity with the form empty
    Then I should see a native required warning on the CADI activity creation form
