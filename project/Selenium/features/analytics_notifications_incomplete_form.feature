Feature: Analítica - Envío de formulario incompleto de configuración de notificaciones

  Scenario: Guardar con umbral y días en 0 debe disparar validación nativa (min=1)
    Given I am on the login page
    When I login with username "1110287840" and password "123"
    And I open the sidebar menu
    And I go to analytics & reports from the menu
    And I go to recommendations from analytics menu
    And I open notifications config
    And I save notifications config with zeros
    Then I should see a native min-1 warning in notifications config
