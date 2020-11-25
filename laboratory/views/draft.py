# def maybe_remove_date(node, kw):
#    if not kw.get('use_date'):
#        del node['date']

# class BlogPostSchema(colander.Schema):
#    title = colander.SchemaNode(
#        colander.String(),
#        title = 'Title',
#        description = 'Blog post title',
#        validator = colander.Length(min=5, max=100),
#        widget = deform.widget.TextInputWidget(),
#        )
#    date = colander.SchemaNode(
#        colander.Date(),
#        title = 'Date',
#        description = 'Date',
#        widget = deform.widget.DateInputWidget(),
#        )

# blog_schema = BlogPostSchema(after_bind=maybe_remove_date)
# blog_schema = blog_schema.bind(use_date=False)