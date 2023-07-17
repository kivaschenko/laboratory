import datetime

import colander
import deform
from deform.exception import ValidationFailure

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPSeeOther

from .. import models

# ==========================
# DB MESSAGE
db_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to initialize your database tables with `alembic`.
    Check your README.txt for descriptions and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""


# ===================
# HOME
@view_config(route_name="home", renderer="../templates/home.jinja2")
def my_view(request):
    message = ""
    csrf_token = request.session.get_csrf_token()

    def validate_csrf(node, value):
        if value != csrf_token:
            raise ValueError("Bad CSRF token!")

    class CSRFSchema(colander.Schema):
        csrf = colander.SchemaNode(
            colander.String(),
            default=csrf_token,
            validator=validate_csrf,
            widget=deform.widget.HiddenWidget(),
        )

    substance_query = request.dbsession.query(models.Substance.name).all()
    subs_choices = [(x[0], x[0]) for x in substance_query]
    subs_choices.insert(0, ("-", "---  РЕЧОВИНИ, РЕАКТИВИ ---"))
    normative_query = request.dbsession.query(models.Normative.name).all()
    norm_choices = [(x[0], x[0]) for x in normative_query]
    norm_choices.insert(0, ("-", "---  РОЗЧИНИ  ---"))
    item_choices = subs_choices + norm_choices
    today = datetime.date.today()

    class FilterSchema(colander.Schema):
        choices_type = (("substance", "Речовина, реактив"), ("solution", "Розчин"))
        type_item = colander.SchemaNode(
            colander.String(),
            validator=colander.OneOf([x[0] for x in choices_type]),
            widget=deform.widget.RadioChoiceWidget(values=choices_type, inline=True),
            title="Тип компонента",
        )
        name_item = colander.SchemaNode(
            colander.String(),
            validator=colander.Length(min=3, max=255),
            widget=deform.widget.SelectWidget(values=item_choices),
            title="Назва компоненту",
            description="виберіть назву",
        )
        choices_direction = (("income", "приход"), ("outcome", "розход"))
        direction = colander.SchemaNode(
            colander.String(),
            validator=colander.OneOf([x[0] for x in choices_direction]),
            widget=deform.widget.RadioChoiceWidget(
                values=choices_direction, inline=True
            ),
            title="Напрямок руху",
        )
        start_date = colander.SchemaNode(
            colander.Date(),
            title="Початок періоду",
            default=today,
            description="Включає день з 00:00",
        )
        end_date = colander.SchemaNode(
            colander.Date(),
            title="Кінець періоду",
            default=today,
            description="Не включає цей день",
        )

    schema = FilterSchema().bind(request=request)
    form = deform.Form(schema, buttons=("submit",))
    if request.method == "POST" and "submit" in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            next_url = request.route_url("archive_filter", **appstruct)
            return HTTPSeeOther(next_url)
        except ValidationFailure as e:
            return {"form": e.render(), "message": message}
    return {"form": form.render(), "form": form.render()}


# ===================================
# FILTERING
@view_config(
    route_name="archive_filter",
    permission="create",
    renderer="../templates/archive_filter.jinja2",
)
def filter_archive(request):
    type_item = request.matchdict["type_item"]
    name_item = request.matchdict["name_item"]
    start_date = request.matchdict["start_date"]
    end_date = request.matchdict["end_date"]
    direction = request.matchdict["direction"]
    if type_item == "substance":
        if direction == "income":
            query = (
                request.dbsession.query(
                    models.Stock.creation_date,
                    models.Stock.amount,
                    models.Stock.price,
                    models.Stock.total_cost,
                    models.Stock.notes,
                )
                .filter(models.Stock.substance_name == name_item)
                .filter(models.Stock.creation_date >= start_date)
                .filter(models.Stock.creation_date <= end_date)
                .filter(models.Stock.amount > 0)
                .all()
            )
        else:
            query = (
                request.dbsession.query(
                    models.Stock.creation_date,
                    models.Stock.amount,
                    models.Stock.price,
                    models.Stock.total_cost,
                    models.Stock.notes,
                )
                .filter(models.Stock.substance_name == name_item)
                .filter(models.Stock.creation_date >= start_date)
                .filter(models.Stock.creation_date <= end_date)
                .filter(models.Stock.amount < 0)
                .all()
            )
    elif type_item == "solution":
        if direction == "income":
            query = (
                request.dbsession.query(
                    models.Solution.created_at,
                    models.Solution.amount,
                    models.Solution.price,
                    models.Solution.total_cost,
                    models.Solution.notes,
                )
                .filter(models.Solution.normative == name_item)
                .filter(models.Solution.created_at >= start_date)
                .filter(models.Solution.created_at <= end_date)
                .filter(models.Solution.amount > 0)
                .all()
            )
        else:
            query = (
                request.dbsession.query(
                    models.Solution.created_at,
                    models.Solution.amount,
                    models.Solution.price,
                    models.Solution.total_cost,
                    models.Solution.notes,
                )
                .filter(models.Solution.normative == name_item)
                .filter(models.Solution.created_at >= start_date)
                .filter(models.Solution.created_at <= end_date)
                .filter(models.Solution.amount < 0)
                .all()
            )
    item_list = []
    if len(query) > 0:
        item_list = [q for q in query]
    return {
        "name_item": name_item,
        "item_list": item_list,
        "start_date": start_date,
        "end_date": end_date,
    }
