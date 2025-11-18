Feature: Team form validation

  Scenario: Intentar crear equipo sin completar campos requeridos
    Given I am on the login page
    When I login with username "5544" and password "5544"
    And I go to tournaments from the menu
    And I open tournament details for "Torneo Interno de Tenis de Mesa"
    And I open the team creation form
    And I submit the empty team form
    Then I should see required warnings on the team form
