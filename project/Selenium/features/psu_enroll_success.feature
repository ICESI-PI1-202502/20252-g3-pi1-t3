Feature: PSU - Inscripción exitosa en un proyecto con cupos

  Scenario: Abrir Detalles por título y inscribirme
    Given I am on the login page
    When I login with username "23871289" and password "Pablito_200"
    And I open the sidebar menu
    And I go to PSU projects from the menu
    And I open PSU project details for "AyudaMarionetasConscientes"
    And I enroll in the PSU project
    Then I should see a PSU enrollment success alert
