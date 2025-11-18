Feature: CADI - Validación al editar actividad (campos vacíos)

  Scenario: Error al editar actividad dejando el nombre vacío
    Given I am on the login page
    When I login with username "5544" and password "5544"
    And I open CADI management from the home card
    And I open the CADI category "Deportes Individuales"
    And I click edit on CADI activity "Natación (Avanzado)"
    And I clear the CADI activity name and try to update
    Then I should see a native required warning on the CADI activity form
