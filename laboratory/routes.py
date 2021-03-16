def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/', factory='laboratory.security.LabFactory')

    # substances
    config.add_route('substances', '/substances', factory='laboratory.security.LabFactory')
    config.add_route('substances_edit', '/substances/edit', factory='laboratory.security.LabFactory')
    config.add_route('add_substance', '/add_substance', factory='laboratory.security.LabFactory')
    config.add_route('delete_substance', '/substance/{subs_id}/delete', factory='laboratory.security.LabFactory')

    # normatives and solutions
    config.add_route('new_normative', '/new-normative', factory='laboratory.security.LabFactory')
    config.add_route('new_norm_next', '/new-norm-next/{name}/{type}/{output}/{as_subst}/{data}/{solutions}', factory='laboratory.security.LabFactory')
    config.add_route('normative_list', '/normatives', factory='laboratory.security.LabFactory')
    config.add_route('delete_normative', '/delete-normative/{norm_id}', factory='laboratory.security.LabFactory')
    config.add_route('solutions', '/solutions', factory='laboratory.security.LabFactory')
    config.add_route('create_solution', '/create_solution/{normative}', factory='laboratory.security.LabFactory')
    config.add_route('aggregate_solution', '/aggregate-solution', factory='laboratory.security.LabFactory')

    # recipe and analysis
    config.add_route('new_recipe', '/new-recipe', factory='laboratory.security.LabFactory')
    config.add_route('new_recipe_next', '/new-recipe-next/{name}/{solutions}/{substances}', factory='laboratory.security.LabFactory',)
    config.add_route('recipes', '/recipes', factory='laboratory.security.LabFactory')
    config.add_route('recipe_details', '/resipe-details/{id_recipe}', factory='laboratory.security.LabFactory')
    config.add_route('analysis_done', '/analysis-done', factory='laboratory.security.LabFactory')
    config.add_route('add_analysis', '/add-analysis/{id_recipe}', factory='laboratory.security.LabFactory')

    # stock
    config.add_route('stock', '/stock', factory='laboratory.security.LabFactory')
    config.add_route('buy_substance', '/buy-substance', factory='laboratory.security.LabFactory')
    config.add_route('stock_history', '/stock-history', factory='laboratory.security.LabFactory')
    # config.add_route('inventory', '/inventory')

    # statistic
    config.add_route('statistic', '/statistic', factory='laboratory.security.LabFactory')

    # authentication
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('change_passw', '/change-passw')
