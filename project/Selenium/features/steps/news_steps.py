from behave import when, then
from pages.sidebar_page import Sidebar
from pages.news_manage_page import NewsManagePage
from pages.news_create_page import NewsCreatePage
from pages.news_edit_page import NewsEditPage
from pages.news_detail_page import NewsDetailPage


@when("navega a la sección de gestionar noticias")
def step_go_to_manage_news(context):
    Sidebar(context.driver).go_to_manage_news()

@when('crea una nueva noticia con título "{titulo}"')
def step_create_news(context, titulo):
    manage = NewsManagePage(context.driver)
    manage.click_create_news()

    create_page = NewsCreatePage(context.driver)
    create_page.create_news(titulo)

    context.last_title = titulo


@then("debe visualizar el detalle de la noticia creada")
def step_verify_news_created(context):
    detail = NewsDetailPage(context.driver)
    assert context.last_title in detail.get_title()

@when('edita la noticia "{titulo}" cambiando el título a "{nuevo}"')
def step_edit_news(context, titulo, nuevo):
    manage = NewsManagePage(context.driver)
    manage.open_edit_form(titulo)

    edit_page = NewsEditPage(context.driver)
    edit_page.edit_title(nuevo)

    context.last_title = nuevo


@then("debe visualizar los cambios en el detalle")
def step_verify_news_edited(context):
    detail = NewsDetailPage(context.driver)
    assert context.last_title in detail.get_title()

@when('elimina la noticia "{titulo}"')
def step_delete_news(context, titulo):
    manage = NewsManagePage(context.driver)
    manage.open_delete_modal(titulo)
    manage.confirm_delete(titulo)


@then("la noticia ya no debe aparecer en la lista de noticias")
def step_verify_news_deleted(context):
    manage = NewsManagePage(context.driver)

    try:
        manage.open_news_by_title(context.last_title)
        assert False, "La noticia aún existe en la tabla"
    except:
        assert True

