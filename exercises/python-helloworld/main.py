from flask.helpers import send_from_directory
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

@app.route('/view_model/<int:id>')
def view_model(id):
    conn = None
    cursor = None
    try:
        _sql = """SELECT a.model_code, a.model_year, a.model_name_za, a.model_name_kr,
                b.ev_1,
                c.body_type, c.doors
                FROM model as a 
                INNER JOIN images as b on a.model_name_za = b.model_name_za
                INNER JOIN body as c on c.body_id = a.key_body
                WHERE a.model_id = %s"""
        conn=mysql.connect()
        cursor=conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(_sql,id)
        model_data = cursor.fetchall()
        for model in model_data:
            print(model['ev_1'])
        return render_template('view_model_detail.html',model_data = model_data)

    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close
@app.route('/return_image/<filename>')
def return_image(filename):
    return send_from_directory("/uploads/",filename)

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
            count = 1
            columns = ""
            image_names = ""
            values_string = ""
            conn = mysql.connect()
            cursor = conn.cursor()
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    sql_images = "INSERT INTO images( model_name_za, ev_1) VALUES(%s, %s)"
                    cursor.execute(sql_images,[_modelName, filename])
                    conn.commit()
                    # columns = columns + " ev_" + str(count) + ","
                    # image_names =  image_names+ " "+ filename + ","
                    # values_string += "%s,"
                    
                print(file)
                flash('Upload Successful!')           
                # count += 1
            
            # values_string = values_string.rstrip(values_string[-1])
            # columns = columns.rstrip(columns[-1])
            # image_names = image_names.rstrip(image_names[-1])
            # sql_images = "INSERT INTO images( model_name_za, " + columns + ") VALUES(%s,"+ values_string +")"
            # data_images = (_modelName, filename)
            # cursor.execute(sql_images,data_images)
            
            sql = "INSERT INTO model( model_code, model_year, model_name_za, key_make, key_body) VALUES(%s,%s,%s,%s,%s)"
            data = (_modelCode, _year, _modelName, _selectMake, _selectBody)
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

@app.route('/view_engines')
def view_engines():
    conn = None
    cursor = None
    try:
        conn = mysql.connect()
        cursor=conn.cursor(pymysql.cursors.DictCursor)
        _sql = """SELECT series, engine_number, name, key_fuel, key_turbo, key_cylinder, key_valves, cam, cvvt, injectors, power, created, modified 
                FROM engine
        """
        cursor.execute(_sql)
        engine_data = cursor.fetchall()
        if engine_data:            
            return render_template("view_engines.html",engine_data=engine_data)
        else:
            flash('No Engines Have Been Created in the system yet')
            return redirect('/new_engine')
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

@app.route('/new_engine')
def new_engine():
    conn = None
    cursor = None
    valves = [6,8,12,16,24,48]
    injectors = [4,6,8]
    try:
        _sql_fuel="SELECT fuel_type_id, fuel_name FROM fuel_types"
        _sql_cylinders="SELECT cylinder_id, number FROM engine_cylinders"
        _sql_cam="SELECT cam_type_id, cam_type FROM cam_type"
        _sql_cvvt="SELECT cvvt_id, cvvt_type FROM cvvt"
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(_sql_fuel)
        fuel_types=cursor.fetchall()
        cursor.execute(_sql_cylinders)
        cylinders=cursor.fetchall()
        cursor.execute(_sql_cam)
        cam_types=cursor.fetchall()
        cursor.execute(_sql_cvvt)
        vvt=cursor.fetchall()
        if fuel_types and cylinders and cam_types and vvt:
            return render_template(
                                    'form_new_engine.html', 
                                    fuel_types=fuel_types,
                                    cylinders=cylinders,
                                    valves=valves,
                                    cam_types=cam_types,
                                    vvt=vvt
                                )
        else:
            return "Some Data Is Missing"
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

@app.route('/new_fuel_types')
def new_fuel_types():
    flash('New Fuel Type has been created')
    return render_template("form_new_fuel_types.html")

@app.route('/save_fuel_type', methods=['POST'])
def save_fuel_type():
    conn = None
    cursor = None
    fuel = request.form['inputFuelType']
    try:
        if fuel and request.method == 'POST':
            _sql = "INSERT INTO fuel_types(fuel_name) Values(%s)"
            fuel_=fuel.upper()
            _data = (fuel_,) 
            conn = mysql.connect()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(_sql, _data)
            conn.commit()
            flash('New Fuel Type Added')
            return redirect('/new_fuel_types')
        else:
            flash('Fuel Type Not Created !!')
            return redirect('/new_fuel_types')
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

#Add a new number of cylinders that can be used to describe an engine e.g 1 - 2 - 4 - 6 etc
@app.route('/new_cylinders_numbers')
def new_cylinders_numbers():
    flash('New Cylinder Numbers Have Been Added To The System')
    return render_template("form_new_cylinders.html")

#Save the number of cylinders to the database table engine_cylinders
@app.route('/save_cylinders', methods=['POST'])
def save_cylinders():
    conn = None
    cursor = None
    cylinders = request.form['inputCylinders']
    try:
        if cylinders and request.method == 'POST':
            _sql = "INSERT INTO engine_cylinders(number) Values(%s)"
            _data = (cylinders) 
            conn = mysql.connect()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(_sql, _data)
            conn.commit()
            flash('New Cylinders Added')
            return redirect('/new_cylinders_numbers')
        else:
            flash('New Cylinders NOT Added Created !!')
            return redirect('/new_cylinders_numbers')
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

#Add a new number of cylinders that can be used to describe an engine e.g 1 - 2 - 4 - 6 etc
@app.route('/new_cam_types')
def new_cam_types():
    flash('New Cylinder Numbers Have Been Added To The System')
    return render_template("form_new_cam.html")

#Save the number of cylinders to the database table engine_cylinders
@app.route('/save_cam_type', methods=['POST'])
def save_cam_type():
    conn = None
    cursor = None
    cam = request.form['inputCam']
    try:
        if cam and request.method == 'POST':
            _sql = "INSERT INTO cam_type(cam_type) Values(%s)"
            _data = (cam.upper(),) 
            conn = mysql.connect()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(_sql, _data)
            conn.commit()
            flash('New Cylinders Added')
            return redirect('/new_cam_types')
        else:
            flash('New Cylinders NOT Added Created !!')
            return redirect('/new_cam_types')
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

#Add a new number of cylinders that can be used to describe an engine e.g 1 - 2 - 4 - 6 etc
@app.route('/new_cvvt')
def new_cvvt():
    flash('New CVVT Have Been Added To The System')
    return render_template("form_new_cvvt.html")

#Save the number of cylinders to the database table engine_cylinders
@app.route('/save_cvvt', methods=['POST'])
def save_cvvt():
    conn = None
    cursor = None
    cvvt = request.form['inputCvvt']
    try:
        if cvvt and request.method == 'POST':
            _sql = "INSERT INTO cvvt(cvvt_type) Values(%s)"
            _data = (cvvt.upper(),) 
            conn = mysql.connect()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(_sql, _data)
            conn.commit()
            flash('New CVVT Added')
            return redirect('/new_cvvt')
        else:
            flash('New Cylinders NOT Added Created !!')
            return redirect('/new_cvvt')
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
