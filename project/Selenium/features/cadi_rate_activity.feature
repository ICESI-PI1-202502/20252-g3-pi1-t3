Feature: CADI - Calificar actividad desde búsqueda

  Scenario: Calificar con 5 estrellas y ver mensaje de éxito
    Given I am on the login page
    When I login with username "23871289" and password "Pablito_200"
    And I open the sidebar menu
    And I go to the search page from the menu
    And I click the CADI "Calificar" button
    And I set the CADI rating to "5" stars and confirm
    Then I should see the CADI rating success message
