Feature: Horario - Visualización del horario personal (draft)

  Scenario: Ver el botón "Semana" en la vista de Horario
    Given I am on the login page
    When I login with username "1112343789" and password "contraseña"
    And I open the sidebar menu
    And I go to the schedule page from the menu
    Then I should see the "Semana" button
