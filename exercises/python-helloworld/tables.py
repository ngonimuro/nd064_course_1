from flask_table import Table, Col, LinkCol

class Results(Table):
    model_id = Col('Id', show=False)
    model_code = Col('Code')
    model_year = Col('Year')
    model_name_za = Col('Model')
    make_name = Col('Make')
    body_type = Col('Body')
    created=Col('Created')
    modified=Col('Modified')
    view = LinkCol('View','view_model',url_kwargs=dict(id='model_id'))
    edit = LinkCol('Edit', 'edit_view', url_kwargs=dict(id='model_id'))
    delete = LinkCol('Delete ', 'delete_user', url_kwargs=dict(id='model_id'))
    