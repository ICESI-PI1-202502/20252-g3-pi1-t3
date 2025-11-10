Feature: Join existing team in a tournament

  Scenario: Unirse exitosamente a un equipo existente
    Given I am on the login page
    When I login with username "488192423" and password "Daniel_2005"
    And I go to tournaments from the menu
    And I open tournament details for "Torneo Interno de Tenis de Mesa"
    And I join the team "Equipo - Daniel Martinez"
    And I open my team management
    Then I should see the manage team header for "Equipo - Daniel Martinez"
