Feature: Analítica - Filtro de tipo de Actividad existente

  Scenario: Filtrar por "Artes Escénicas" en Análisis de comportamiento estudiantil
    Given I am on the login page
    When I login with username "1110287840" and password "123"
    And I open the sidebar menu
    And I go to analytics & reports from the menu
    And I open the behavior analysis page
    And I filter behavior by activity type "Artes Escénicas" and search
    Then I should see at least one row with activity type "Artes Escénicas"
