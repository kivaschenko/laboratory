def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')

    # substances
    config.add_route('substances', '/substances')
    config.add_route('substances_edit', '/substances/edit')
    config.add_route('add_substance', '/add_substance')
    config.add_route('delete_substance', '/substance/{subs_id}/delete')

    # normatives and solutions
    config.add_route('new_normative', '/new-normative')
    config.add_route('new_norm_next', '/new-norm-next/{name}/{output}/{data}')
    config.add_route('normative_list', '/normatives')
    config.add_route('solutions', '/solutions')
    config.add_route('create_solution', '/create_solution/{normative}')
    config.add_route('aggregate_solution', '/aggregate-solution')

    # recipe and analysis
    config.add_route('new_recipe', '/new-recipe')
    config.add_route('new_recipe_next',
                     '/new-recipe-next/{name}/{solutions}/{substances}')
    config.add_route('recipes', '/recipes')
    config.add_route('recipe_details', '/resipe-details/{id_recipe}')
    config.add_route('analysis_done', '/analysis-done')
    config.add_route('add_analysis', '/add-analysis/{id_recipe}')

    # stock
    config.add_route('stock', '/stock')
    config.add_route('buy_substance', '/buy-substance')
    config.add_route('stock_history', '/stock-history')
    config.add_route('inventory', '/inventory')

    # statistic
    config.add_route('statistic', '/statistic')
