from flask_table import Table, Col, LinkCol

class Classify(Table):
    body_id = Col('Id', show=False)
    body_type = Col('Body')
    doors = Col('Doors')
    created = Col('Created')
    modified = Col('Modified')
    edit = LinkCol('Edit','edit_view',url_kwargs=dict(id='body_id'))
    delete = LinkCol('Delete','delete_body',url_kwargs=dict(id='body_id'))