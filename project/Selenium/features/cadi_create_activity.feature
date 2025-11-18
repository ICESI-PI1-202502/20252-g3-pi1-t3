Feature: CADI - Creación exitosa de actividad por administrador

  Scenario: Crear actividad "Ajedrez (Profesional)" en Deportes Individuales
    Given I am on the login page
    When I login with username "5544" and password "5544"
    And I open CADI management from the home card
    And I open the CADI category "Deportes Individuales"
    And I click "Agregar actividad" in the CADI list
    And I create a CADI activity named "Ajedrez (Novatos)" of type "Deportes Individuales" with capacity 10, requires "No" and description:
      """
      Día: viernes
      Horario: 17:00–19:00
      Espacio: 204 -G
      Profesor: Yorlenny Martinez
      Día: Jueves
      Horario: 11:30–13:30
      Espacio: 204 - G
      Profesor: Julián Andrés
      """
    Then I should see the CADI activity titled "Ajedrez (Novatos)" in the list
