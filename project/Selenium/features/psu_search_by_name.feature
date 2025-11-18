Feature: PSU - Búsqueda de proyectos sociales por nombre

  Scenario: Buscar proyecto "AyudaMarionetasConscientes" con query "Ayuda"
    Given I am on the login page
    When I login with username "1112343789" and password "contraseña"
    And I open the sidebar menu
    And I go to PSU projects from the menu
    And I search PSU projects by text "Ayuda"
    Then I should see a PSU project titled "AyudaMarionetasConscientes"
