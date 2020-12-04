import json
import decimal
import colander
import deform
import datetime
import pandas as pd
from deform.exception import ValidationFailure
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
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
@view_config(route_name='add_substance',
             renderer='../templates/add_substance.jinja2')
def new_substance(request):
    message = ''
    measure_types = (
        ('г', 'грам'),
        ('мл', 'міллілітр'),
        ('шт', 'штука')
    )
    class SubstanceSchema(colander.Schema):
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
            new_substance = models.Substance(
                name=appstruct['name'],
                measurement=appstruct['measurement']
            )
            request.dbsession.add(new_substance)
            next_url = request.route_url('substances')
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {'form': e, 'message': message}
    return {'message': message, 'form': form}


@view_config(route_name='delete_substance')
def delete_substance(request):
    subs_id = request.matchdict['subs_id']
    subs = request.dbsession.query(models.Substance).get(subs_id)
    request.dbsession.delete(subs)
    next_url = request.route_url('substances')
    return HTTPFound(location=next_url)


@view_config(route_name='substances', renderer='../templates/substances.jinja2')
def substances_list(request):
    query = request.dbsession.query(models.Substance)\
                   .order_by(models.Substance.name).all()
    subs_list = []
    if len(query) > 0:
        subs_list = [q.__dict__ for q in query]
    return {"subs_list":subs_list}


@view_config(route_name='substances_edit',
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
@view_config(route_name='buy_substance',
             renderer='../templates/buy_substance.jinja2')
def input_substance(request):
    message = ''
    subs_query = request.dbsession.query(models.Substance).all()
    subs_list = []
    if len(subs_query) > 0:
        subs_list = [q.__dict__ for q in subs_query]
    else:
        message = 'Каталог реактивів пустий! Неможливо створити рецепт.'
        return {'message': message}
    choices = (
        (subs['name'], subs['name'] + ' , ' + subs['measurement'])
        for subs in subs_list
    )
    class BuySchema(colander.Schema):
        substance_name = colander.SchemaNode(colander.String(),
            title='Реактив (речовина, індикатор)',
            widget=deform.widget.SelectWidget(values=choices))
        amount = colander.SchemaNode(colander.Decimal(), default=0.01,
            validator=colander.Range(min=0, max=decimal.Decimal("100000.00")),
            title="Кількість",
            description='Вибреріть реактив (речовину, індикатор)',
            widget=deform.widget.TextInputWidget(
                attributes={
                    "type": "numeric",
                    "inputmode": "decimal",
                    "step": "0.01",
                    "min": "0",
                    "max": "100000.00"
                }))
        price = colander.SchemaNode(colander.Decimal(), default=0.01,
            validator=colander.Range(min=0, max=decimal.Decimal("9999.99")),
            title=" Ціна, грн.",
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
            print('subs_ -->', subs_)
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
            return dict(
                form=e.render()
            )
    return dict(
        form=form.render(),
        message=message
    )


@view_config(route_name='stock_history',
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
    return dict(
        message=message,
        history=history
    )



@view_config(route_name='stock', renderer='.//templates/stock.jinja2')
def get_aggregate_stock(request):
    message = ''
    stock_list = []
    textual_sql = """SELECT stock.substance_name AS substance_name,
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
            temp_dict['sum_cost'] = q['sum_cost'].__floor__()
            stock_.append(temp_dict)
    except DBAPIError:
        message = db_err_msg
    return {'stock_list': stock_, 'message': message}


#=======================
# SOLUTIONS

@view_config(route_name='solutions', renderer='../templates/solutions.jinja2')
def list_solutions(request):
    query = request.dbsession.query(models.Solution).\
          filter(text("remainder > 0")).all()
    solutions = []
    if len(query) > 0:
        solutions = [q.__dict__ for q in query]
    return {"solutions": solutions}


@view_config(route_name='create_solution',
             renderer='../templates/create_solution.jinja2')
def make_new_solution(request):
    message = ''
    normative_name = request.matchdict['normative']
    current_normative = request.dbsession.query(models.Normative).\
        filter(models.Normative.name==normative_name).first()
    current_normative = current_normative.__dict__
    output = current_normative['output']
    data_dict = json.loads(current_normative['data'])
    class SolutionSchema(colander.Schema):
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
                return {'form': form.render(appstruct), 'message': message,
                        'normative': normative_name}
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
                return {'form': form.render(appstruct), 'message': message}
            new_records = []
            for key, value in new_data.items():
                df_key = df[df.substance_name==key]
                subs_measurement = df_key['measurement'].values[0]
                sum_remainder = df_key['amount'].sum()
                sum_remainder = sum_remainder.__float__()
                new_remainder = sum_remainder + value
                subs_price = ((df_key['price'] * df_key['remainder'])) / df_key['remainder'].sum()
                subs_price = subs_price.values[0].__float__()
                subs_total_cost = subs_price * value
                subs_notes = f'Створено розчин {normative_name}'
                new_stock = models.Stock(
                    substance_name=key,
                    measurement=subs_measurement,
                    amount=value,
                    remainder=new_remainder,
                    price=subs_price,
                    total_cost=subs_total_cost,
                    notes=subs_notes
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
            # add to solution model
            new_solution = models.Solution(
                normative=normative_name,
                measurement=measurement,
                amount=amount,
                remainder=amount,
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
            return {'form': e.render(), 'normative': normative_name}
    return {'form': form.render(), 'normative': normative_name}


#=======================
# NORMATIVES

@view_config(route_name='normative_list',
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

@view_config(route_name='new_normative',
             renderer='../templates/new_normative.jinja2')
def new_normative(request):
    message = ''
    subs_query = request.dbsession.query(models.Substance).all()
    subs_list = []
    if len(subs_query) > 0:
        subs_list = [q.__dict__ for q in subs_query]
    else:
        message = 'Каталог реактивів пустий! Неможливо створити рецепт.'
        return {'message': message}
    choices = ( (subs['id'], subs['name']) for subs in subs_list )
    class NormativeSchema(colander.Schema):
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
            next_url = request.route_url('new_norm_next', **appstruct)
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {'form': e, 'message': message}
    return {'form': form, 'message': message}


@view_config(route_name='new_norm_next',
             renderer='../templates/new_norm_next.jinja2')
def new_norm_next(request):
    message = ''
    name_solution = request.matchdict['name']
    output_ = request.matchdict['output']
    class NextFormSchema(colander.Schema):
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
                    default=0.01,
                    validator=colander.Range(min=0,
                            max=decimal.Decimal("999.99")),
                    widget=deform.widget.TextInputWidget(
                        attributes={
                            "type": "number",
                            "inputmode": "decimal",
                            "step": "0.01",
                            "min": "0",
                            "max": "999.99"
                        })
                    )
    schema = NextFormSchema().bind(request=request)
    button = deform.form.Button(name='submit', title="Створити рецепт",
                                type='submit')
    form = deform.Form(schema, buttons=(button,))
    appstruct = {'name': name_solution, 'output': output_}
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
            return dict(
                form=e.render()
                )
    return dict(
        name=name_solution,
        form=form.render(appstruct),
        message=message
    )


#==================
# RECIPES
@view_config(route_name="recipes", renderer='../templates/recipes.jinja2')
def all_recipes(request):
    message = ''
    query = request.dbsession.query(models.Recipe.id, models.Recipe.name)\
            .order_by(models.Recipe.name).all()
    if len(query) == 0:
        message = 'Немає доданих рецептів аналізів.'
    return dict(
        recipes=query,
        message=message
    )


@view_config(route_name='recipe_details',
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


@view_config(route_name='new_recipe', renderer='../templates/new_recipe.jinja2')
def new_recipe(request):
    message = ''
    subs_query = request.dbsession.query(models.Substance).all()
    subs_list = []
    if len(subs_query) > 0:
        subs_list = [q.__dict__ for q in subs_query]
    else:
        message = 'Каталог реактивів пустий! Неможливо створити рецепт.'
        return {'message': message}
    substance_choices = ( (subs['id'], subs['name']) for subs in subs_list )
    solution_query = request.dbsession.query(models.Normative).all()
    solutions = []
    if len(solution_query) > 0:
        solutions = [q.__dict__ for q in solution_query]
    else:
        message = 'Немає жодного розчину в базі даних! Створіть хоч би один.'
        return {'message': message}
    solution_choices = ( (item['id'], item['name']) for item in solutions )
    class RecipeSchema(colander.Schema):
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
            next_url = request.route_url('new_recipe_next', **appstruct)
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {'form': e, 'message': message}
    return {'form': form, 'message': message}


@view_config(route_name='new_recipe_next',
             renderer='../templates/new_recipe_next.jinja2')
def new_recipe_next(request):
    message = ''
    name_analysis = request.matchdict['name']
    class NextRecipeSchema(colander.Schema):
        name = colander.SchemaNode(colander.String(), title='Назва аналізу')
        def after_bind(self, schema, kwargs):
            req = kwargs['request']
            substances = req.matchdict['substances']
            substances = substances.lstrip("{'").rstrip("'}").split("', '")
            list_subs_id = [int(d) for d in substances]
            subs_query = request.dbsession.query(models.Substance)\
                       .filter(models.Substance.id.in_(list_subs_id)).all()
            subs_list = [sq.__dict__ for sq in subs_query]
            for subs in subs_list:
                self[subs['name'] + ', '+subs["measurement"]] = \
                    colander.SchemaNode(
                        colander.Decimal(),
                        title=subs["name"] + ', '+subs["measurement"],
                        default=0.01,
                        validator=colander.Range(min=0,
                                max=decimal.Decimal("999.99")),
                        widget=deform.widget.TextInputWidget(
                            attributes={
                                "type": "number",
                                "inputmode": "decimal",
                                "step": "0.01",
                                "min": "0",
                                "max": "999.99"
                            })
                        )
            solutions = req.matchdict['solutions']
            solutions = solutions.lstrip("{'").rstrip("'}").split("', '")
            list_solut_id = [int(d) for d in solutions]
            solut_query = request.dbsession.query(models.Normative)\
                        .filter(models.Normative.id.in_(list_solut_id)).all()
            solut_list = [st.__dict__ for st in solut_query]
            for solut in solut_list:
                self[solut['name'] + ', мл'] = colander.SchemaNode(
                    colander.Integer(),
                    title=solut['name'] + ', мл',
                    validator=colander.Range(1,10000)
                )
    schema = NextRecipeSchema().bind(request=request)
    button = deform.form.Button(name='submit', title='Створити новий аналіз',
                                type='submit')
    form = deform.Form(schema, buttons=(button,))
    appstruct = {'name': name_analysis}
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            deserialized = form.validate(controls)
            new_name = deserialized.pop('name')
            substances = {}
            solutions = {}
            for key, value in deserialized.items():
                if isinstance(value, decimal.Decimal):
                    substances[key] = float(value)
                if isinstance(value, int):
                    solutions[key] = value
            substances = json.dumps(substances)
            solutions = json.dumps(solutions)
            new_recipe = models.Recipe(
                name=new_name,
                substances=substances,
                solutions=solutions
            )
            recipe = request.dbsession.add(new_recipe)
            next_url = request.route_url('recipes')
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {'form': e.render()}
    return dict(
        message=message,
        form=form.render(appstruct),
        name=name_analysis
    )

#==============================
# ANALYSIS
@view_config(route_name='add_analysis',
             renderer='../templates/add_analysis.jinja2')
def add_done_analysis(request):
    message = ''
    id_recipe = request.matchdict['id_recipe']
    recipe = request.dbsession.query(models.Recipe).get(id_recipe)
    recipe_name = recipe.name
    substances = json.loads(recipe.substances)
    solutions = json.loads(recipe.solutions)
    class AddAnalysisSchema(colander.Schema):
        done_date = colander.SchemaNode(colander.Date(),
            title="Дата виконання", validator=colander.Range(
            min=datetime.date(datetime.date.today().year, 1, 1),
            min_err=("${val} раніше чим дозволено мінімальну: ${min}"),),
            )
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

        except ValidationFailure as e:
            return {'form': e.render(), 'message': message, 'recipe': recipe}
    return {'message': message, 'recipe': recipe, 'form': form.render()}
