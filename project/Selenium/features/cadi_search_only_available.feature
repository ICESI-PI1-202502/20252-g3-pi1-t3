Feature: CADI - Filtro "Solo con horarios disponibles"

  Scenario: Activar "Solo disponibles" y ver "Accesorios & Tejidos"
    Given I am on the login page
    When I login with username "23871289" and password "Pablito_200"
    And I open the sidebar menu
    And I go to the search page from the menu
    And I open the CADI search filters
    And I enable the "Only available" filter and apply
    And I wait 8 seconds
    Then I should see the search result titled "Accesorios & Tejidos"
