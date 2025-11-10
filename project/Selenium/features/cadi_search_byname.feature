Feature: CADI - Búsqueda de actividades por nombre

  Scenario: Buscar "Ajedrez" desde el menú como usuario no admin
    Given I am on the login page
    When I login with username "1112343789" and password "Daniel_123"
    And I open the sidebar menu
    And I go to the search page from the menu
    And I search CADI activities by name "Ajedrez"
    Then I should see the search result titled "Ajedrez"
