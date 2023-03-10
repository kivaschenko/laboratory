import json
import decimal
import colander
import deform
import datetime
from math import pi

import pandas as pd
from bokeh.palettes import viridis, inferno
from bokeh.plotting import figure
from bokeh.transform import cumsum, dodge
from bokeh.models import ColumnDataSource
from bokeh.embed import components
from deform.exception import ValidationFailure

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPForbidden,
    HTTPNotFound
)
from sqlalchemy import text, desc
from sqlalchemy.exc import DBAPIError

from .. import models


#===================
# HOME
@view_config(route_name='home', renderer='../templates/home.jinja2')
def my_view(request):
    try:
        query = request.dbsession.query(models.Substance)
        one = query.filter(
            models.Substance.name == "Вода H2O").first()
        one = one.__dict__
    except DBAPIError:
        return Response(db_err_msg, content_type='text/plain', status=500)
    return {'one': one, 'project': 'програма для обліку реактивів'}


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

#===============
# SUBSTANCES
@view_config(route_name='add_substance', permission='create',
             renderer='../templates/add_substance.jinja2')
def new_substance(request):
    message = ''
    csrf_token = request.session.get_csrf_token()
    def validate_csrf(node, value):
        if value != csrf_token:
            raise ValueError("Bad CSRF token")
    class CSRFSchema(colander.Schema):
        csrf = colander.SchemaNode(colander.String(), default=csrf_token,
             validator=validate_csrf, widget=deform.widget.HiddenWidget())
    class SubstanceSchema(CSRFSchema):
        measure_types = (
            ('г', 'грам'),
            ('мл', 'міллілітр'),
            ('шт', 'штука'),
        )
        name = colander.SchemaNode(colander.String(), title="Назва реактиву")
        measurement = colander.SchemaNode(colander.String(),
                    widget=deform.widget.SelectWidget(values=measure_types),
                    title="Одиниця виміру")
    schema = SubstanceSchema().bind(request=request)
    button = deform.form.Button(name='submit', title="Створити", type='submit')
    form = deform.Form(schema, buttons=(button,), autocomplete='off')
    if request.method == 'POST' and 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            certain_name = appstruct['name']
            check_query = request.dbsession.query(models.Substance).\
                        filter(models.Substance.name==certain_name).all()
            if len(check_query) > 0:
                return {'message': 'Така назва вже існує!', 'form': form}
            new_substance = models.Substance(
                name=appstruct['name'],
                measurement=appstruct['measurement']
            )
            request.dbsession.add(new_substance)
            next_url = request.route_url('substances')
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {'form': e.render(), 'message': message}
    return {'message': message, 'form': form.render()}


@view_config(route_name='delete_substance', permission='edit')
def delete_substance(request):
    subs_id = request.matchdict['subs_id']
    subs = request.dbsession.query(models.Substance).get(subs_id)
    request.dbsession.delete(subs)
    next_url = request.route_url('substances')
    return HTTPFound(location=next_url)


@view_config(route_name='substances', renderer='../templates/substances.jinja2',
             permission='read')
def substances_list(request):
    query = request.dbsession.query(models.Substance)\
                   .order_by(models.Substance.name).all()
    subs_list = []
    if len(query) > 0:
        subs_list = [q.__dict__ for q in query]
    return {"subs_list":subs_list}


@view_config(route_name='substances_edit', permission='edit',
             renderer='../templates/substances_edit.jinja2')
def substances_edit(request):
    query = request.dbsession.query(models.Substance)\
                   .order_by(models.Substance.name).all()
    subs_list = []
    if len(query) > 0:
        subs_list = [q.__dict__ for q in query]
    return {"subs_list":subs_list}

#========================
# STOCK
@view_config(route_name='buy_substance', permission='create',
             renderer='../templates/buy_substance.jinja2')
def input_substance(request):
    message = ''
    csrf_token = request.session.get_csrf_token()
    def validate_csrf(node, value):
        if value != csrf_token:
            raise ValueError("Bad CSRF token")
    class CSRFSchema(colander.Schema):
        csrf = colander.SchemaNode(colander.String(), default=csrf_token,
             validator=validate_csrf, widget=deform.widget.HiddenWidget())
    subs_query = request.dbsession.query(models.Substance).all()
    subs_list = []
    if len(subs_query) > 0:
        subs_list = [q.__dict__ for q in subs_query]
    else:
        message = 'Каталог реактивів пустий! Неможливо створити форму прихода.'
        return {'message': message}
    choices = [
        (subs['name'], subs['name'] + ', ' + subs['measurement']) for subs in subs_list
        ]
    class BuySchema(CSRFSchema):
        substance_name = colander.SchemaNode(colander.String(),
            title='Реактив (речовина, індикатор)',
            widget=deform.widget.SelectWidget(values=choices))
        amount = colander.SchemaNode(colander.Decimal(), default=0.001,
            validator=colander.Range(
                min=-decimal.Decimal("1000000.000"),
                max=decimal.Decimal("1000000.000")
            ),
            title="Кількість",
            description='Вибреріть реактив (речовину, індикатор)',
            widget=deform.widget.TextInputWidget(
                attributes={
                    "type": "numeric",
                    "inputmode": "decimal",
                    "step": "0.001",
                    "min": "-1000000.000",
                    "max": "1000000.000"
                }
            )
        )
        price = colander.SchemaNode(colander.Decimal(), default=0.01,
            validator=colander.Range(min=0, max=decimal.Decimal("9999.99")),
            title="Ціна, грн.",
            widget=deform.widget.TextInputWidget(
                attributes={
                    "type": "numeric",
                    "inputmode": "decimal",
                    "step": "0.01",
                    "min": "0",
                    "max": "9999.99"
                }))
        notes = colander.SchemaNode(colander.String(),
            title="Примітка",
            default=' ',
            missing='',
            validator=colander.Length(max=600),
            widget=deform.widget.TextAreaWidget(rows=5, cols=60),
            description="Необов'язково, до 600 символів з пробілами",)
    schema = BuySchema().bind(request=request)
    button = deform.form.Button(name='submit', type='submit',
        title="Оприходувати на склад")
    form = deform.Form(schema, buttons=(button,))
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            substance_name = appstruct['substance_name']
            certain_substance = request.dbsession.query(models.Substance)\
                .filter(models.Substance.name==substance_name).first()
            measurement = certain_substance.measurement
            amount = float(appstruct['amount'])
            price = float(appstruct['price'])
            total_cost = round(price * amount, 2)
            notes = 'Приход на склад. ' + str(appstruct['notes'])
            last_remainder = 0
            subs_ = request.dbsession.query(models.Stock.remainder).\
                       filter(models.Stock.substance_name==substance_name).\
                       order_by(desc(models.Stock.creation_date)).first()
            if subs_ is not None:
                last_remainder += subs_[0].__float__()
            new_stock = models.Stock(
                substance_name=substance_name,
                measurement=measurement,
                amount=amount,
                remainder=last_remainder + amount,
                price=price,
                total_cost=total_cost,
                notes=notes
            )
            request.dbsession.add(new_stock)
            next_url = request.route_url('stock_history')
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {'form': e.render(),}
    return {'form': form.render(), 'message': message}


@view_config(route_name='stock_history', permission='create',
             renderer='../templates/stock_history.jinja2')
def stock_all_parties(request):
    message = ''
    query = request.dbsession.query(models.Stock)\
            .order_by(models.Stock.creation_date.desc()).all()
    history = []
    if len(query) == 0:
        message = 'Немає приходів і розходів. Історія складу пуста.'
    history = [q.__dict__ for q in query]
    for item in history:
        item['creation_date'] = item['creation_date'].strftime('%Y-%m-%d %H:%M')
    return {'message': message, 'history': history}


@view_config(route_name='stock', renderer='.//templates/stock.jinja2',
             permission='create')
def get_aggregate_stock(request):
    message = ''
    stock_list = []
    textual_sql = """
        SELECT stock.substance_name AS substance_name,
        stock.measurement AS measurement,
        SUM (stock.amount) AS total_amount,
        AVG (stock.price) AS avg_price,
        SUM (stock.amount) * AVG (stock.price) AS sum_cost
        FROM stock
        GROUP BY stock.substance_name,  stock.measurement"""
    try:
        query = request.dbsession.execute(textual_sql).fetchall()
        stock_list = [q for q in query]
        stock_ = []
        for q in stock_list:
            temp_dict = {}
            temp_dict['substance_name'] = q['substance_name']
            temp_dict['measurement'] = q['measurement']
            temp_dict['total_amount'] = q['total_amount'].__float__()
            temp_dict['avg_price'] = q['avg_price'].__float__()
            temp_dict['sum_cost'] = q['sum_cost']
            stock_.append(temp_dict)
    except DBAPIError:
        message = db_err_msg
    return {'stock_list': stock_, 'message': message}


# @view_config(route_name='inventory', renderer='../templates/inventory.jinja2',
#              permission='create')
# def make_inventory(request):
#     message = ''
#     textual_sql = '''
#         SELECT stock.substance_name AS name,
#             stock.measurement AS measurement,
#             SUM (stock.amount) AS amount
#         FROM stock
#         GROUP BY name, measurement ORDER BY name'''
#     class InventorySchema(colander.Schema):
#         notes = colander.SchemaNode(colander.String(),
#             title="Примітка",
#             missing='', default='Проведено інвентаризацію залишків по складу',
#             validator=colander.Length(max=600),
#             widget=deform.widget.TextAreaWidget(rows=5, cols=60),
#             description="Необов'язково, до 600 символів з пробілами",)
#         def after_bind(self, schema, kwargs):
#             subs_list = request.dbsession.execute(textual_sql).fetchall()
#             # subs_list = [sq.__dict__ for sq in query]
#             for subs in subs_list:
#                 self[subs['name']] = colander.SchemaNode(colander.Decimal(),
#                     title=subs["name"] + ', ' + subs["measurement"],
#                     default=subs['amount'].__float__(),
#                     description='введіть реальну кількість, якщо вона інша',
#                     validator=colander.Range(
#                         min=-decimal.Decimal("999999.999"),
#                         max=decimal.Decimal("999999.999")
#                         ),
#                     widget=deform.widget.TextInputWidget(
#                         attributes={
#                             "type": "number",
#                             "inputmode": "decimal",
#                             "step": "0.001",
#                             "min": "0",
#                             "max": "999999.999"
#                         })
#                     )
#     schema = InventorySchema().bind(request=request)
#     button = deform.form.Button(name='submit', type='submit', title="Зробити")
#     form = deform.Form(schema, buttons=(button,))
#     if 'submit' in request.POST:
#         controls = request.POST.items()
#         try:
#             appstruct = form.validate(controls)
#         except ValidationFailure as e:
#             return {'message':'Помилки у формі вводу даних', 'form': e}
#     return {'form':form, 'message':message}


#=======================
# SOLUTIONS
@view_config(route_name='aggregate_solution', permission='create',
             renderer='../templates/aggregate_solution.jinja2')
def agregate_solution_remainder(request):
    message = ''
    solutions = []
    textual_sql = """
        SELECT solutions.normative AS normative,
        solutions.measurement AS measurement,
        SUM (solutions.amount) AS total_amount,
        AVG (solutions.price) AS avg_price,
        SUM (solutions.amount) * AVG (solutions.price) AS sum_cost
        FROM solutions
        GROUP BY solutions.normative, solutions.measurement"""
    try:
        query = request.dbsession.execute(textual_sql).fetchall()
        solutions = [q for q in query]
        solutions_cleaned = []
        for sol in solutions:
            temp_dict = {}
            temp_dict['normative'] = sol['normative']
            temp_dict['measurement'] = sol['measurement']
            temp_dict['total_amount'] = sol['total_amount'].__float__()
            temp_dict['avg_price'] = sol['avg_price'].__float__()
            temp_dict['sum_cost'] = sol['sum_cost']
            solutions_cleaned.append(temp_dict)
    except DBAPIError:
        message = db_err_msg
    return {'solutions': solutions_cleaned, 'message': message}


@view_config(route_name='solutions', renderer='../templates/solutions.jinja2',
             permission='create')
def list_solutions(request):
    query = request.dbsession.query(models.Solution).all()
          # filter(text("remainder > 0")).\
    solutions = []
    if len(query) > 0:
        solutions = [q.__dict__ for q in query]
    return {"solutions": solutions}


@view_config(route_name='create_solution', permission='create',
             renderer='../templates/create_solution.jinja2')
def make_new_solution(request):
    message = ''
    csrf_token = request.session.get_csrf_token()

    def validate_csrf(node, value):
        if value != csrf_token:
            raise ValueError("Bad CSRF token")
    class CSRFSchema(colander.Schema):
        csrf = colander.SchemaNode(colander.String(), default=csrf_token,
             validator=validate_csrf, widget=deform.widget.HiddenWidget())
    normative_name = request.matchdict['normative']
    current_normative = request.dbsession.query(models.Normative).\
        filter(models.Normative.name==normative_name).first()
    current_normative = current_normative.__dict__
    output = current_normative['output']
    data_dict = json.loads(current_normative['data'])
    class SolutionSchema(CSRFSchema):
        amount = colander.SchemaNode(colander.Integer(),
            title="Об'єм, вихід", default=int(output))
        measurement = colander.SchemaNode(colander.String(),
            validator=colander.OneOf([x[0] for x in (('мл','мл'), ('г','г'))]),
            widget=deform.widget.RadioChoiceWidget(
                values=(('мл', 'мл'), ('г', 'г')), inline=True),
            title="Одиниця виміру", )
        created_at = colander.SchemaNode(colander.Date(),
           validator=colander.Range(
           min=datetime.date(datetime.date.today().year, 1, 1),
           min_err=("${val} раніше чим дозволено мінімальну: ${min}"),),
           title="Дата виготовлення",
           default=datetime.date.today(),
           )
        due_date = colander.SchemaNode(colander.Date(),
           validator=colander.Range(
           min=datetime.date(datetime.date.today().year, 1, 1),
           min_err=("${val} раніше чим дозволено минимальну: ${min}"),),
           title="Дата придатності",
           default=datetime.date.today() + datetime.timedelta(days=15)
           )
        notes = colander.SchemaNode(colander.String(),
            title="Примітка",
            missing='', default='Створено новий розчин',
            validator=colander.Length(max=600),
            widget=deform.widget.TextAreaWidget(rows=5, cols=60),
            description="Необов'язково, до 600 символів з пробілами",)
    schema = SolutionSchema().bind(request=request)
    button = deform.form.Button(name='submit', type='submit', title="Зробити")
    form = deform.Form(schema, buttons=(button,))
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            created_at = appstruct['created_at']
            due_date = appstruct['due_date']
            notes = appstruct['notes']
            amount = appstruct['amount']
            measurement = appstruct['measurement']
            coef = 1
            if amount != output:
                coef = amount / output
            if isinstance(coef, decimal.Decimal):
                coef = float(coef)
            new_data = {
                key: -value * coef for key, value in data_dict.items()
            }
            substances_from_data = list(new_data.keys())
            query_stock = request.dbsession.query(models.Stock).\
                        filter(models.Stock.substance_name.in_(
                        substances_from_data)).all()
            if len(query_stock) == 0:
                message = f'На складі відсутні всі компоненти!'
                return {'form': form, 'message': message, 'normative': normative_name}
            else:
                substances_dicts = [qs.__dict__ for qs in query_stock]
                df = pd.DataFrame.from_records(substances_dicts)
            # check keys in df:
            needing_substances = set(new_data.keys())
            given_substances = df['substance_name'].unique().tolist()
            given_substances = set(given_substances)
            missing = needing_substances - given_substances
            if len(missing) > 0:
                missing_string = ' '.join(missing)
                message = f'Відсутні залишки: {missing_string}'
                return {'form': form, 'message': message, 'normative': normative_name}
            new_records = []
            for key, value in new_data.items():
                df_key = df[df.substance_name==key]
                subs_measurement = df_key['measurement'].values[0]
                sum_remainder = df_key['amount'].sum()
                sum_remainder = sum_remainder.__float__()
                new_remainder = sum_remainder + value
                subs_price = df_key['total_cost'].sum() / df_key['amount'].sum()
                subs_price = subs_price.__float__()
                subs_total_cost = subs_price * value
                subs_notes = f'Створено розчин {normative_name}'
                new_stock = models.Stock(
                    substance_name=key,
                    measurement=subs_measurement,
                    amount=value,
                    remainder=new_remainder,
                    price=subs_price,
                    total_cost=subs_total_cost,
                    notes=subs_notes,
                    normative=normative_name
                )
                new_records.append(new_stock)
                # define cost for each substance in this solution:
                new_data[key] = subs_total_cost
            for record in new_records:
                request.dbsession.add(record)
            # count price and cost of the new solution
            solution_cost = 0
            for cost in new_data.values():
                solution_cost += -cost
            solution_price = round(solution_cost / amount, 2)
            last_remainder = 0
            get_remainder = request.dbsession.query(models.Solution.remainder).\
                          filter(models.Solution.normative==normative_name).\
                          order_by(desc(models.Solution.created_at)).first()
            if get_remainder is not None:
                last_remainder += get_remainder[0].__float__()
            # add to solution model
            new_solution = models.Solution(
                normative=normative_name,
                measurement=measurement,
                amount=amount,
                remainder=last_remainder + amount,
                price=solution_price,
                total_cost=solution_cost,
                created_at=created_at,
                due_date=due_date,
                notes=notes
            )
            request.dbsession.add(new_solution)
            next_url = request.route_url('solutions')
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {'form': e, 'normative': normative_name}
    return {'form': form, 'normative': normative_name}


#=======================
# NORMATIVES

@view_config(route_name='normative_list', permission='read',
             renderer='../templates/normative_list.jinja2')
def get_all_normatives(request):
    message = ''
    normative_query = request.dbsession.query(models.Normative).order_by(
                    models.Normative.id).all()
    normative_list = []
    if len(normative_query) > 0:
        normative_list = [nq.__dict__ for nq in normative_query]
        for norm in normative_list:
            norm['data'] = json.loads(norm['data'])
    else:
        message = 'Немає нормативів у списку.'
    return dict(
        message=message,
        normative_list=normative_list
        )


@view_config(route_name='new_normative', permission='create',
             renderer='../templates/new_normative.jinja2')
def new_normative(request):
    message = ''
    csrf_token = request.session.get_csrf_token()

    def validate_csrf(node, value):
        if value != csrf_token:
            raise ValueError("Bad CSRF token")
    class CSRFSchema(colander.Schema):
        csrf = colander.SchemaNode(colander.String(), default=csrf_token,
             validator=validate_csrf, widget=deform.widget.HiddenWidget())
    subs_query = request.dbsession.query(models.Substance).all()
    subs_list = []
    if len(subs_query) > 0:
        subs_list = [q.__dict__ for q in subs_query]
    else:
        message = 'Каталог реактивів пустий! Неможливо створити рецепт.'
        return {'message': message}
    choices = ( (subs['id'], subs['name']) for subs in subs_list )
    class NormativeSchema(CSRFSchema):
        name = colander.SchemaNode(colander.String(), title="Назва розчину")
        output = colander.SchemaNode(
            colander.Integer(),
            title="Об'єм вихід в мл",
            description='Ціле число, наприклад 1000')
        data = colander.SchemaNode(
            colander.Set(), title="відмітити необхідні речовини",
            widget=deform.widget.CheckboxChoiceWidget(values=choices))
    schema = NormativeSchema().bind(request=request)
    button = deform.form.Button(name='submit', title="Далі", type='submit')
    form = deform.Form(schema, buttons=(button,), autocomplete='off')
    if request.method == 'POST' and 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            certain_name = appstruct['name']
            check_query = request.dbsession.query(models.Normative).\
                        filter(models.Normative.name==certain_name).all()
            if len(check_query) > 0:
                return {'message': 'Така назва вже існує!', 'form': form}
            next_url = request.route_url('new_norm_next', **appstruct)
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {'form': e, 'message': message}
    return {'form': form, 'message': message}


@view_config(route_name='new_norm_next', permission='create',
             renderer='../templates/new_norm_next.jinja2')
def new_norm_next(request):
    message = ''
    csrf_token = request.session.get_csrf_token()

    def validate_csrf(node, value):
        if value != csrf_token:
            raise ValueError("Bad CSRF token")
    class CSRFSchema(colander.Schema):
        csrf = colander.SchemaNode(colander.String(), default=csrf_token,
             validator=validate_csrf, widget=deform.widget.HiddenWidget())
    name_solution = request.matchdict['name']
    output_ = request.matchdict['output']
    class NextFormSchema(CSRFSchema):
        name = colander.SchemaNode(colander.String(), title="Назва розчину",
             default=name_solution)
        output = colander.SchemaNode(colander.Integer(),
               title="Об'єм вихід в мл",
               default=int(output_))
        def after_bind(self, schema, kwargs):
            req = kwargs['request']
            data = req.matchdict['data']
            data = data.lstrip("{'").rstrip("'}").split("', '")
            list_subs_id = [int(d) for d in data]
            subs_query = request.dbsession.query(models.Substance)\
                       .filter(models.Substance.id.in_(list_subs_id)).all()
            subs_list = [sq.__dict__ for sq in subs_query]
            for subs in subs_list:
                self[subs['name']] = colander.SchemaNode(colander.Decimal(),
                    title=subs["name"] + ', '+subs["measurement"],
                    default=0.001,
                    validator=colander.Range(min=0,
                            max=decimal.Decimal("999999.999")),
                    widget=deform.widget.TextInputWidget(
                        attributes={
                            "type": "number",
                            "inputmode": "decimal",
                            "step": "0.001",
                            "min": "0",
                            "max": "999999.999"
                        })
                    )
    schema = NextFormSchema().bind(request=request)
    button = deform.form.Button(name='submit', title="Створити рецепт",
                                type='submit')
    form = deform.Form(schema, buttons=(button,))
    # appstruct = {'name': name_solution, 'output': output_}
    if request.method == 'POST' and 'submit' in request.POST:
        controls = request.POST.items()
        try:
            deserialized = form.validate(controls)
            new_name = deserialized.pop('name')
            new_output = deserialized.pop('output')
            new_data = {k: float(v) for k, v in deserialized.items()}
            new_data = json.dumps(new_data)
            new_normative = models.Normative(
                name=new_name,
                output=new_output,
                data=new_data
                )
            request.dbsession.add(new_normative)
            next_url = request.route_url('normative_list')
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {'form': e,}
    return {'name': name_solution, 'form': form, 'message': message}


#==================
# RECIPES
@view_config(route_name="recipes", renderer='../templates/recipes.jinja2',
             permission='read')
def all_recipes(request):
    message = ''
    query = request.dbsession.query(models.Recipe.id, models.Recipe.name)\
            .order_by(models.Recipe.name).all()
    if len(query) == 0:
        message = 'Немає доданих рецептів аналізів.'
    return {'recipes': query, 'message': message}


@view_config(route_name='recipe_details', permission='read',
             renderer='../templates/recipe_details.jinja2')
def recipe_details(request):
    id_recipe = request.matchdict['id_recipe']
    try:
        query = request.dbsession.query(models.Recipe).get(id_recipe)
        recipe = query.__dict__
        recipe['substances'] = json.loads(recipe['substances'])
        recipe['solutions'] = json.loads(recipe['solutions'])
        return dict(
            recipe=recipe
        )
    except DBAPIError:
        return Response(db_err_msg, content_type='text/plain', status=500)
    return {'recipe': recipe}


@view_config(route_name='new_recipe', permission='create',
             renderer='../templates/new_recipe.jinja2')
def new_recipe(request):
    message = ''
    csrf_token = request.session.get_csrf_token()
    def validate_csrf(node, value):
        if value != csrf_token:
            raise ValueError("Bad CSRF token")
    class CSRFSchema(colander.Schema):
        csrf = colander.SchemaNode(colander.String(), default=csrf_token,
             validator=validate_csrf, widget=deform.widget.HiddenWidget())
    subs_query = request.dbsession.query(models.Substance).all()
    subs_list = []
    if len(subs_query) > 0:
        subs_list = [q.__dict__ for q in subs_query]
    else:
        message = 'Каталог реактивів пустий! Неможливо створити рецепт.'
        return {'message': message}
    substance_choices = [(subs['id'], subs['name']) for subs in subs_list]
    solution_query = request.dbsession.query(models.Normative).all()
    solutions = []
    if len(solution_query) > 0:
        solutions = [q.__dict__ for q in solution_query]
    else:
        message = 'Немає жодного розчину в базі даних! Створіть хоч би один.'
        return {'message': message}
    solution_choices = [(item['id'], item['name']) for item in solutions]
    class RecipeSchema(CSRFSchema):
        name = colander.SchemaNode(colander.String(), title='Назва аналізу',
            description='введіть унікальну назву аналізу')
        substances = colander.SchemaNode(colander.Set(), title='Речовини',
            description='виберіть необхідні речовини',
            widget=deform.widget.CheckboxChoiceWidget(values=substance_choices))
        solutions = colander.SchemaNode(colander.Set(), title='Розчини',
            description='виберіть потрібні розчини',
            widget=deform.widget.CheckboxChoiceWidget(values=solution_choices))
    schema = RecipeSchema().bind(request=request)
    button = deform.form.Button(name='submit', title='Далі', type='submit')
    form = deform.Form(schema, buttons=(button,), autocomplete='off')
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            certain_name = appstruct['name']
            check_query = request.dbsession.query(models.Recipe.name).\
                        filter(models.Recipe.name==certain_name).all()
            if len(check_query) > 0:
                return {'message': 'Така назва аналізу вже існує!',
                        'form': form.render()}
            next_url = request.route_url('new_recipe_next', **appstruct)
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {'form': e.render(), 'message': message}
    return {'form': form.render(), 'message': message}


@view_config(route_name='new_recipe_next', permission='create',
             renderer='../templates/new_recipe_next.jinja2')
def new_recipe_next(request):
    message = ''
    csrf_token = request.session.get_csrf_token()
    def validate_csrf(node, value):
        if value != csrf_token:
            raise ValueError("Bad CSRF token")
    class CSRFSchema(colander.Schema):
        csrf = colander.SchemaNode(colander.String(), default=csrf_token,
             validator=validate_csrf, widget=deform.widget.HiddenWidget())
    name_analysis = request.matchdict['name']
    class NextRecipeSchema(CSRFSchema):
        name = colander.SchemaNode(colander.String(), title='Назва аналізу',
             default=name_analysis)
        def after_bind(self, schema, kwargs):
            req = kwargs['request']
            substances = req.matchdict['substances']
            substances = substances.lstrip("{'").rstrip("'}").split("', '")
            list_subs_id = [int(d) for d in substances]
            subs_query = request.dbsession.query(models.Substance)\
                       .filter(models.Substance.id.in_(list_subs_id)).all()
            subs_list = [sq.__dict__ for sq in subs_query]
            for subs in subs_list:
                self[subs['name']] = colander.SchemaNode(
                    colander.Decimal(),
                    title=subs["name"] + ', ' + subs["measurement"],
                    default=0.001,
                    validator=colander.Range(min=0, max=decimal.Decimal("999999.999")),
                    widget=deform.widget.TextInputWidget(attributes={
                        "type": "number",
                        "inputmode": "decimal",
                        "step": "0.001",
                        "min": "0",
                        "max": "999999.999"
                    })
                )
            solutions = req.matchdict['solutions']
            solutions = solutions.lstrip("{'").rstrip("'}").split("', '")
            list_solut_id = [int(d) for d in solutions]
            solut_query = request.dbsession.query(models.Normative)\
                        .filter(models.Normative.id.in_(list_solut_id)).all()
            solut_list = [st.__dict__ for st in solut_query]
            for solut in solut_list:
                self[solut['name']] = colander.SchemaNode(
                    colander.Decimal(),
                    title=solut['name'] + ', мл',
                    default=0.001,
                    validator=colander.Range(min=0, max=decimal.Decimal("999999.999")),
                    widget=deform.widget.TextInputWidget(attributes={
                        "type": "number",
                        "inputmode": "decimal",
                        "step": "0.001",
                        "min": "0",
                        "max": "999999.999"
                    })
                )
    schema = NextRecipeSchema().bind(request=request)
    button = deform.form.Button(name='submit', title='Створити новий аналіз', type='submit')
    form = deform.Form(schema, buttons=(button,))
    # appstruct = {'name': name_analysis}
    subst_names = [s[0] for s in request.dbsession.query(models.Substance.name).all()]
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            deserialized = form.validate(controls)
            new_name = deserialized.pop('name')
            deserialized_keys = [i for i in deserialized.keys()]
            subst_here = set(subst_names) & set(deserialized_keys)
            substances = {}
            solutions = {}
            pop_csrf = deserialized.pop('csrf')
            for key, value in deserialized.items():
                if key in subst_here:
                    substances[key] = float(value)
                else:
                    solutions[key] = float(value)
            substances = json.dumps(substances)
            solutions = json.dumps(solutions)
            new_recipe = models.Recipe(
                                name=new_name,
                                substances=substances,
                                solutions=solutions
                                )
            request.dbsession.add(new_recipe)
            next_url = request.route_url('recipes')
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {'form': e.render(), 'message': 'Перевірте поля форми'}
    return {'message': message, 'form':form.render(), 'name':name_analysis}


#==============================
# ANALYSIS
@view_config(route_name='add_analysis', permission='create',
             renderer='../templates/add_analysis.jinja2')
def add_done_analysis(request):
    message = ''
    csrf_token = request.session.get_csrf_token()

    def validate_csrf(node, value):
        if value != csrf_token:
            raise ValueError("Bad CSRF token")
    class CSRFSchema(colander.Schema):
        csrf = colander.SchemaNode(colander.String(), default=csrf_token,
             validator=validate_csrf, widget=deform.widget.HiddenWidget())
    id_recipe = request.matchdict['id_recipe']
    recipe = request.dbsession.query(models.Recipe).get(id_recipe)
    recipe_name = recipe.name
    substances = json.loads(recipe.substances)
    solutions = json.loads(recipe.solutions)
    class AddAnalysisSchema(CSRFSchema):
        done_date = colander.SchemaNode(colander.Date(),
            title="Дата виконання", validator=colander.Range(
            min=datetime.date(datetime.date.today().year, 1, 1),
            min_err=("${val} раніше чим дозволено мінімальну: ${min}"),),
            default=datetime.date.today())
        quantity = colander.SchemaNode(colander.Integer(),
            title="кількість виконаних досліджень", default=1)
    schema = AddAnalysisSchema().bind(request=request)
    button = deform.form.Button(name='submit', type='submit', title='Записати')
    form = deform.Form(schema, buttons=(button,))
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            done_date = appstruct['done_date']
            quantity = appstruct['quantity']
            subsbstances_quantity = {
                key: -value * quantity for key, value in substances.items()
            }
            substances_names = list(substances.keys())
            # check remainders
            query_stock = request.dbsession.query(models.Stock).\
                        filter(models.Stock.substance_name.in_(
                        substances_names)).all()
            if len(query_stock) == 0:
                message = f'На складі відсутні речовини!'
                return {'form': form, 'message': message, 'recipe': recipe}
            else:
                query_stock_dicts = [qs.__dict__ for qs in query_stock]
                df = pd.DataFrame.from_records(query_stock_dicts)
            got_substances = df['substance_name'].unique().tolist()
            missing = set(substances_names) - set(got_substances)
            if len(missing) > 0:
                missing_string = ' '.join(missing)
                message = f'Відсутні залишки: {missing_string}'
                return {'form': form, 'message': message, 'recipe': recipe}
            # list for collect instances of class Stock: to_insert_into_stock
            insert_into_stock = []
            substances_cost = {}
            for key, value in subsbstances_quantity.items():
                df_key = df[df.substance_name==key]
                subs_measurement = df_key['measurement'].values[0]
                sum_remainder = df_key['amount'].sum()
                sum_remainder = sum_remainder.__float__()
                new_remainder = sum_remainder + value
                avg_price = df_key['total_cost'].sum() / df_key['amount'].sum()
                avg_price = avg_price.__float__()
                subs_total_cost = avg_price * value
                subs_notes = f'Аналіз {recipe_name} в кількості: {quantity}'
                new_stock = models.Stock(
                    substance_name=key,
                    measurement=subs_measurement,
                    amount=value,
                    remainder=new_remainder,
                    price=avg_price,
                    total_cost=subs_total_cost,
                    notes=subs_notes,
                    recipe=recipe_name
                )
                insert_into_stock.append(new_stock)
                substances_cost[key] = subs_total_cost
            solutions_quantity = {
                key: -value * quantity for key, value in solutions.items()
            }
            solutions_names = [*solutions.keys()]
            query_solutions = request.dbsession.query(models.Solution).\
                            filter(models.Solution.normative.in_(
                            solutions_names)).all()
            if len(query_solutions) == 0:
                message = f'Немає готових розчинів для цього аналізу.'
                return {'form': form, 'message': message, 'recipe': recipe}
            else:
                query_solutions_dicts = [qs.__dict__ for qs in query_solutions]
                df2 = pd.DataFrame.from_records(query_solutions_dicts)
            got_solutions = df2['normative'].unique().tolist()
            missing = set(solutions_names) - set(got_solutions)
            if len(missing) > 0:
                missing_string = ' '.join(missing)
                message = f'Відсутні залишки: {missing_string}'
                return {'form': form, 'message': message, 'recipe': recipe}
            insert_into_solutions = []
            solutions_cost = {}
            for key, value in solutions_quantity.items():
                df2_key = df2[df2.normative==key]
                sol_measurement = df2_key['measurement'].values[0]
                sol_remainder = df2_key['amount'].sum()
                sol_remainder = sol_remainder.__float__()
                new_remainder = sol_remainder + value
                avg_price = df2_key['total_cost'].sum() / df2_key['amount'].sum()
                avg_price = avg_price.__float__()
                sol_total_cost = avg_price * value
                sol_notes = f'Аналіз {recipe_name} в кількості: {quantity}'
                new_solution = models.Solution(
                    normative=key,
                    measurement=sol_measurement,
                    amount=value,
                    remainder=new_remainder,
                    price=avg_price,
                    total_cost=sol_total_cost,
                    created_at=datetime.date.today(),
                    notes=sol_notes,
                    recipe=recipe_name
                )
                insert_into_solutions.append(new_solution)
                solutions_cost[key] = sol_total_cost
            total_substances_cost = [v for v in substances_cost.values()]
            total_substances_cost = sum(total_substances_cost) * -1
            total_solutions_cost = [v for v in solutions_cost.values()]
            total_solutions_cost = sum(total_solutions_cost) * -1
            this_analysis = models.Analysis(
                recipe_name=recipe_name,
                quantity=quantity,
                done_date=done_date,
                total_cost=total_substances_cost + total_solutions_cost,
                substances_cost=json.dumps(substances_cost),
                solutions_cost=json.dumps(solutions_cost)
            )
            request.dbsession.add(this_analysis)
            for stock in insert_into_stock:
                request.dbsession.add(stock)
            for sol in insert_into_solutions:
                request.dbsession.add(sol)
            next_url = request.route_url('analysis_done')
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {'form': e, 'message': message, 'recipe': recipe}
    return {'message': message, 'recipe': recipe, 'form': form}


@view_config(route_name='analysis_done', permission='create',
             renderer='../templates/analysis_done.jinja2')
def analysis_history(request):
    message = ''
    analysises = []
    try:
        query = request.dbsession.query(models.Analysis).all()
        analysises = [q.__dict__ for q in query]
    except DBAPIError:
        message = db_err_msg
    return {'analysises': analysises, 'massage': message}

#===========================
# STATISTIC
@view_config(route_name='statistic', permission='create',
             renderer='../templates/statistic_form.jinja2')
def statistic_form(request):
    message = ''
    csrf_token = request.session.get_csrf_token()

    def validate_csrf(node, value):
        if value != csrf_token:
            raise ValueError("Bad CSRF token")
    class CSRFSchema(colander.Schema):
        csrf = colander.SchemaNode(colander.String(), default=csrf_token,
             validator=validate_csrf, widget=deform.widget.HiddenWidget())
    substances = []
    pie_script = ''
    pie_div = ''
    today = datetime.date.today()
    class StatisticSchema(CSRFSchema):
        begin_date = colander.SchemaNode(colander.Date(), title="Початок періоду",
                   default=today, description='Включає день з 00:00')
        end_date = colander.SchemaNode(colander.Date(), title='Кінець періоду',
                 default=today, description='Не включає цей день')
    schema = StatisticSchema().bind(request=request)
    button = deform.form.Button(type='submit', name='submit', title='Вибрати')
    form = deform.Form(schema, buttons=(button,))
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            start = appstruct['begin_date']
            end = appstruct['end_date']
            subs_query = request.dbsession.query(
                models.Stock.substance_name,
                models.Stock.measurement,
                models.Stock.amount,
                models.Stock.total_cost).filter(
                models.Stock.amount < 0).filter(
                models.Stock.creation_date >= start).filter(
                models.Stock.creation_date < end).all()
            if len(subs_query) == 0:
                return {'form': form, 'message': f'Немає даних за період: {start} - {end}'}
            else:
                df_subs = pd.DataFrame.from_records(subs_query, coerce_float=True,
                    columns=['subs_name', 'measurement', 'amount', 'costs'])
                df_subs['amount'] = df_subs['amount'] * -1
                df_subs['costs'] = df_subs['costs'] * -1
                df_subs = df_subs.groupby(['subs_name', 'measurement']).sum()
                df_subs.reset_index(inplace=True)
                subs_total_cost = df_subs['costs'].sum()
                # plot pie chart
                df_subs['angle'] = df_subs['costs']/df_subs['costs'].sum() * 2*pi
                num_colors = df_subs.shape[0]
                df_subs['color'] = viridis(num_colors)
                source = ColumnDataSource(data=df_subs)
                pieplot = figure(
                    plot_height=400, sizing_mode="scale_both",
                    title='Частки витрат речовин, грн.', toolbar_location=None,
                    tools='hover', tooltips="@subs_name: @costs" + " грн.",
                    x_range=(-0.5, 1.0)
                )
                pieplot.wedge(x=0, y=1, radius=0.4, line_color="white",
                               start_angle=cumsum('angle', include_zero=True),
                               end_angle=cumsum('angle'), fill_color='color',
                               legend_field='subs_name', source=source)
                pieplot.axis.axis_label=None
                pieplot.axis.visible=False
                pieplot.grid.grid_line_color=None
                pie_script, pie_div = components(pieplot)
                # analysis horizontal bar and table
                analysis_sql = '''SELECT analysis.recipe_name AS analysis,
                    SUM (analysis.quantity) AS numbers,
                    SUM (analysis.total_cost) AS cost
                    FROM analysis
                    WHERE analysis.done_date BETWEEN :x AND :y
                    GROUP BY analysis.recipe_name ORDER BY numbers DESC'''
                analysis_q = request.dbsession.execute(analysis_sql, {'x': start, 'y': end}).fetchall()
                df_an = pd.DataFrame.from_records(analysis_q, coerce_float=True,
                      columns=['analysis', 'numbers', 'cost'])
                total_analysis = df_an['numbers'].sum()
                sum_cost_analysis = df_an['cost'].sum()
                source_num = ColumnDataSource(data=df_an)
                plot_an = figure(
                    y_range=df_an['analysis'].tolist(),
                    x_range=(0, df_an['numbers'].max()),
                    plot_height=250, sizing_mode="scale_both",
                    title='Кількість виконаних аналізів', toolbar_location=None,
                    tools='hover', tooltips="@analysis: @numbers раз, @cost грн."
                    )
                plot_an.hbar(y=dodge('analysis', 0.0, range=plot_an.y_range),
                             right='numbers', height=.8, alpha=.5,
                             source=source_num, color='green')
                plot_an.y_range.range_padding = 0.1
                plot_an.axis.minor_tick_line_color = None
                ticks = [i for i in range(0, df_an['numbers'].max() + 1, 1)]
                plot_an.xaxis[0].ticker = ticks
                an_script , an_div = components(plot_an)
                return {'form': form,
                        'message': f'Дані періоду: {start} - {end}',
                        'substances': df_subs.to_dict('records'),
                        'piescript': pie_script,
                        'piediv': pie_div,
                        'subs_total': subs_total_cost,
                        'analysis': analysis_q,
                        'barscript': an_script,
                        'bardiv': an_div,
                        'total_analysis': total_analysis,
                        'sum_cost_analysis': sum_cost_analysis}
        except ValidationFailure as e:
            return {'form': e, 'message': 'Помилки у формі', 'substances': substances}
    return {'form': form, 'message': message}
