Feature: Analítica - Filtro de comparación con fechas inválidas

  Scenario: Periodo personalizado con inicio en 2029 y fin en 2025
    Given I am on the login page
    When I login with username "1110287840" and password "123"
    And I open the sidebar menu
    And I go to analytics & reports from the menu
    And I open the comparisons & statistics page
    And I set an invalid custom period (start 2029, end 2025) grouped by Facultad and apply
    Then I should see the info alert about selecting filters
