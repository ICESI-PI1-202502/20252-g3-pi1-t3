Feature: CADI - Creación exitosa de actividad por administrador

  Scenario: Crear actividad "Tiro con arco" en Deportes Individuales
    Given I am on the login page
    When I login with username "1113624957" and password "00"
    And I open CADI management from the home card
    And I open the CADI category "Deportes Individuales"
    And I click "Agregar actividad" in the CADI list
    And I create a CADI activity named "Tiro con arco" of type "Deportes Individuales" with capacity 10, requires "No" and description:
      """
      Día: Miércoles
      Horario: 17:00–19:00
      Espacio: 204 -G
      Profesor: Yorlenny Arango
      Día: Jueves
      Horario: 11:30–13:30
      Espacio: 204 - G
      Profesor: Julián Andrés
      """
    Then I should see the CADI activity titled "Tiro con arco" in the list
