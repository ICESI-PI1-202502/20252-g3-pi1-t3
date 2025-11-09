Feature: Team creation in tournaments

  Scenario: Creación exitosa de un equipo
    Given I am on the login page
    When I login with username "1113624957" and password "00"
    And I go to tournaments from the menu
    And I open tournament details for "Torneo Interno de Tenis de Mesa"
    And I create a team named "Equipo - Daniel Martinez" with responsible "1105365296", discipline "Tenis de Mesa", min 1 and max 16
    Then I should see the team "Equipo - Daniel Martinez" in the tournament details