Feature: Analítica - Filtro por semestre

  Scenario: Filtrar semestre 2 y agrupar por Facultad en Comparaciones
    Given I am on the login page
    When I login with username "5544" and password "5544"
    And I open the sidebar menu
    And I go to analytics & reports from the menu
    And I open the comparisons & statistics page
    And I filter by semester 2 grouped by Facultad and update
    Then I should see the results heading for semester 2 grouped by Facultad
