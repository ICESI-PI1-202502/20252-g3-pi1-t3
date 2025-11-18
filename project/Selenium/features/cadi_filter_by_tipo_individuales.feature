Feature: CADI - Filtro por tipo de actividad (Deportes Individuales)

  Scenario: Ver resultados de "Deportes Individuales" y encontrar "Ajedrez"
    Given I am on the login page
    When I login with username "1112343789" and password "contraseña"
    And I open the sidebar menu
    And I go to the search page from the menu
    And I open the CADI search filters
    And I filter CADI by activity type "Deportes Individuales" and apply
    Then I should see "Ajedrez" among the CADI results
