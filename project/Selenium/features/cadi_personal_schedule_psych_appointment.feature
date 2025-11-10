Feature: CADI - Mostrar cita psicológica automática en Horario (personal)

  Scenario: Ver cita psicológica creada automáticamente en vista Mes
    Given I am on the login page
    When I login with username "1112343789" and password "Daniel_123"
    And I open the sidebar menu
    And I go to the personal schedule page from the menu
    And I switch to month view in personal schedule
    And I open the personal schedule event "Cita psicológica"
    Then I should see the personal schedule modal title detail "Cita psicológica"
    And I should see the personal schedule modal source "Creado automáticamente"
