Feature: PSU - Creación de proyecto social con fechas inconsistentes

  Scenario: Intentar crear proyecto con fecha de inicio posterior a la fecha fin
    Given I am on the login page
    When I login with username "5544" and password "5544"
    And I open the sidebar menu
    And I go to PSU projects (admin) from the menu
    And I open the PSU create project form
    And I fill the PSU project with name "PSU - Fechas inconsistentes", capacity 50 and description:
      """
      Proyecto de prueba para validar fechas: inicio posterior al fin.
      """
    And I set the PSU project dates start "2025-11-09" end "2022-11-09" and submit
    Then I should see a PSU date error alert
