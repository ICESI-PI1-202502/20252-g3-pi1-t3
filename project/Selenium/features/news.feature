Feature: Gestión de noticias

  Background:
    Given I am on the login page
    When I login with username "5544" and password "5544"
    And navega a la sección de gestionar noticias

  Scenario: Crear una noticia
    When crea una nueva noticia con título "Noticia de prueba"
    Then debe visualizar el detalle de la noticia creada

  Scenario: Editar una noticia existente
    When edita la noticia "Noticia de prueba" cambiando el título a "Noticia modificada"
    Then debe visualizar los cambios en el detalle

  Scenario: Eliminar una noticia
    When elimina la noticia "Noticia modificada"
    Then la noticia ya no debe aparecer en la lista de noticias
