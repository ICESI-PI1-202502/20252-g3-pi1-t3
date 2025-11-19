Feature: Register a match in a tournament

  Scenario: Creación exitosa de un partido
    Given I am on the login page
    When I login with username "1110287840" and password "123"
    And I go to tournaments from the menu
    And I open tournament details for "Torneo Interno de Tenis de Mesa"
    And I open the match creation form
    And I register a match: team A "Equipo - Daniel Martinez", team B "Equipo - Óscar Triviño", start "2026-03-30 13:30", end "2026-03-30 14:00", place "Coliseo 2"
    Then I should see the match "Equipo - Daniel Martinez vs Equipo - Óscar Triviño" with place "Coliseo 2"
