Feature: Team creation in tournaments

  Scenario: Creación exitosa de un equipo
    Given I am on the login page
    When I login with username "1110287840" and password "123"
    And I go to tournaments from the menu
    And I open tournament details for "Torneo Interno de Tenis de Mesa"
    And I create a team named "Equipo - Dayana Andrea" with responsible "1105365296", discipline "Tenis de Mesa", min 1 and max 16
    Then I should see the team "Equipo - Dayana Andrea" in the tournament details