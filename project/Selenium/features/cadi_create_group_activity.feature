Feature: CADI - Creación de actividad grupal por administrador

  Scenario: Crear actividad "Voleibol Mixto (Profesional)" en Deportes de Conjunto
    Given I am on the login page
    When I login with username "1113624957" and password "00"
    And I open CADI management from the home card
    And I open the CADI category "Deportes de Conjunto"
    And I click "Agregar actividad" in the CADI list
    And I create a CADI activity named "Voleibol Mixto (Profesional)" of type "Deportes de Conjunto" with capacity 10, requires "No" and description:
      """
      Día: Martes
      Horario: 18:00–20:00
      Espacio: Coliseo 1
      Profesor: Equipo CADI

      Día: Jueves
      Horario: 18:00–20:00
      Espacio: Coliseo 1
      Profesor: Equipo CADI
      """
    Then I should see the CADI activity titled "Voleibol Mixto (Formativo)" in the list
