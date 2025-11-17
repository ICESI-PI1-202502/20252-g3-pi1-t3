Feature: Join team form validation

  Scenario: Error al unirse sin seleccionar equipo
    Given I am on the login page
    When I login with username "488192423" and password "Daniel_2005"
    And I go to tournaments from the menu
    And I open tournament details for "Torneo Interno de Tenis de Mesa"
    And I open the join team form
    And I submit the empty join team form
    Then I should see required warnings on the join team form
