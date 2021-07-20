import pymysql
from typing import NoReturn
from app import app
from db_config import mysql
from tables import Results
from flask import flash, render_template, request, redirect, jsonify
from werkzeug.utils import secure_filename
import os
import urllib.request 


links = [
    {'name': 'Home', 'url': ''},
    {'name': 'View Models', 'url': '/models'},
    {'name': 'Create Models', 'url': '/create'}
]

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS  = set(['png', 'jpg', 'jpeg','gif'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    """KS Auto Parts Catalog"""

    return render_template('home.html',
                           title="Catalog",
                           description="Catalog System",
                           links=links
                           )


@app.route('/body')
def view_body():
    conn = None
    cursor = None
    sql = "SELECT * FROM body"
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql)
        body_data = cursor.fetchall()
        return render_template('body.html', body_data=body_data)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/new_classification')
def create_classification():
    return render_template(
        'form_new_body.html',
        title="Create New Body",
        description="Add new body type to the system",
        field_titles="New Body",
    )


@app.route('/save_classification', methods=['POST'])
def save_classification():
    conn = None
    cursor = None

    try:
        _type = request.form['bodyType']
        _doors = request.form['doors']

        if _type and _doors and request.method == 'POST':
            sql = "INSERT INTO body( body_type, doors) VALUES(%s, %s)"
            data = (_type, _doors)
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute(sql, data)
            conn.commit()
            return redirect('/classification')
        else:
            flash('Error while saving your data')
            return redirect('/new_classification')
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/models')
def models():
    conn = None
    cursor = None
    _select = """SELECT a.model_id, a.model_code, a.model_year, a.model_name_za, a.created, a.modified,  
                b.make_name,
                c.body_type
            """
    _from = " FROM model AS a"
    _join = " INNER JOIN  make AS b ON a.key_make = b.make_id"
    _join2 = " LEFT JOIN body AS c ON a.key_body = c.body_id"
    _order = " ORDER BY a.modified desc"
    _sql = _select + _from + _join + _join2 + _order

    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(_sql)
        rows = cursor.fetchall()
        table = Results(rows)
        table.border = True
        return render_template('models.html', table=table, links=links, rows=rows)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/edit/<int:id>')
def edit_view(id):
    conn = None
    cursor = None
    _select = "SELECT a.model_id,a.model_code,a.model_year,a.model_name_za,a.key_make "
    _from = " FROM model AS a "
    _join = " INNER JOIN make AS b ON a.key_make = b.make_id"
    _select2 = "SELECT make_id, make_name,make_abbreviation "
    _from2 = " FROM make"
    _sql = _select + _from + _join
    _sql2 = _select2 + _from2
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(_sql + " WHERE model_id=%s ", id)
        model_row = cursor.fetchone()
        cursor.execute(_sql2)
        make_data = cursor.fetchall()
        cursor.execute("Select body_id,body_type FROM body")
        body_data = cursor.fetchall()
        if model_row and make_data and body_data:
            return render_template('form_edit_model.html',
                                   model_row=model_row,
                                   make_data=make_data,
                                   body_data=body_data
                                   )
        else:
            return 'Record #{id} is missing'.format(id=id)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/new_model')
def create_new_model():
    conn = None
    cursor = None

    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("Select make_id,make_name,make_abbreviation FROM make")
        make_data = cursor.fetchall()
        cursor.execute("Select body_id,body_type FROM body")
        body_data = cursor.fetchall()

        if make_data and body_data:
            return render_template('form_new_model.html',
                                   title="Create New Model",
                                   description="Catalog System add a new model to the system",
                                   field_titles="New Model",
                                   make_data=make_data,
                                   body_data=body_data)
        else:
            return 'No Makes have been added to the system yet'
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/save_new_model', methods=['POST'])
def save_new_model():
    conn = None
    cursor = None

    try:
        _modelCode = request.form['inputModelCode']
        _year = request.form['inputModelYear']
        _modelName = request.form['inputModelName']
        _selectMake = request.form['selectMake']
        _selectBody = request.form['selectBody']
        files = request.files.getlist('files[]')        

        if _modelCode and _year and _modelName and _selectMake and _selectBody and request.method == 'POST':
            print(files)
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                print(file)
            flash('Upload Successful!')
            sql = "INSERT INTO model( model_code, model_year, model_name_za, image_link, key_make, key_body,) VALUES(%s,%s,%s,%s,%s)"
            data = (_modelCode, _year, _modelName, _selectMake, _selectBody)
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute(sql,data)
            conn.commit()
            flash('Model Created Successfully')
            return redirect('/models')
        else:
            return 'One Of The Fields Entered Was Not In The Correct Format !!'
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/save_update_model', methods=['POST'])
def save_update_model():
    conn = None
    cursor = None
    try:
        _code = request.form['inputModelCode']
        _year = request.form['inputModelYear']
        _model = request.form['inputModelName']
        _id = request.form['id']
        _make = request.form['inputSelectMake']
        _body = request.form['inputSelectBody']
        # validate the received values
        if _code and _year and _model and _id and _make and _body and request.method == 'POST':
            sql = "UPDATE model SET model_code=%s, model_year=%s, model_name_za=%s, key_make=%s, key_body=%s WHERE model_id=%s"
            data = (_code, _year, _model, _make, _body, _id)
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute(sql, data)
            conn.commit()
            flash("Model updated successfully!")
            return redirect('/models')
        else:
            return 'Error while updating user'
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/delete/<int:id>')
def delete_user(id):
    conn = None
    cursor = None
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM model WHERE model_id=%s", (id,))
        conn.commit()
        flash('Model deleted successfully!')
        return redirect('/models')
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    app.run(host='0.0.0.0')
