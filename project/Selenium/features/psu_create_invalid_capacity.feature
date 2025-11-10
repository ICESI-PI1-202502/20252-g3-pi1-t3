Feature: PSU - Creación de proyecto social con aforo inválido

  Scenario: Intentar crear proyecto con aforo -1 (min=0)
    Given I am on the login page
    When I login with username "1113624957" and password "00"
    And I open the sidebar menu
    And I go to PSU projects (admin) from the menu
    And I open the PSU create project form
    And I try to create a PSU project named "PSU - Aforo inválido" with negative capacity -1
    Then I should see a min-capacity warning on the PSU project form
