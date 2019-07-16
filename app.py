from flask import Flask, render_template, request, json, redirect, session, jsonify
from flaskext.mysql import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os, uuid


app = Flask(__name__)
app.secret_key = 'Famous'

mysql = MySQL()

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'vnfdjqhk66'
app.config['MYSQL_DATABASE_DB'] = 'BucketList'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['UPLOAD_FOLDER'] = 'static/Uploads'

mysql.init_app(app)


@app.errorhandler(404)
def not_found(error=None):
    return render_template('error.html', error='Not Found(404) {0}'.format(request.url))


@app.route('/')
def main():
    return render_template('index.html')


@app.route('/userHome')
def user_home():
    if session.get('user'):
        return render_template('userHome.html')
    else:
        return render_template('error.html', error='Unauthorized Access')


@app.route('/updateWish/<int:wish_id>', methods=['PUT'])
def update_wish(wish_id):
    conn = mysql.connect()
    try:
        if session.get('user'):
            _user = session.get('user')
            _title = request.form['title']
            _description = request.form['description']
            _wish_id = wish_id
            _file_path = request.form['filePath']
            _is_private = request.form['isPrivate']
            _is_done = request.form['isDone']

            with conn.cursor() as cursor:
                sql = 'update tbl_wish set wish_title = %s, wish_description = %s, wish_file_path = %s, wish_private = %s, wish_accomplished = %s where wish_id = %s and wish_user_id = %s'
                cursor.execute(sql, (_title, _description, _file_path, _is_private, _is_done, _wish_id, _user))
                data = cursor.fetchall()

                if len(data) == 0:
                    conn.commit()
                    return json.dumps({'status': 'OK'})
                else:
                    return json.dumps({'status': 'ERROR'})
        else:
            return render_template('error.html', error='Unauthorized Access')

    except Exception as e:
        return render_template('error.html', error=str(e))
    finally:
        conn.close()


@app.route('/deleteWish/<int:wish_id>', methods=['DELETE'])
def delete_wish(wish_id):
    conn = mysql.connect()
    try:
        if session.get('user'):
            _id = wish_id
            _user = session.get('user')

            with conn.cursor() as cursor:
                sql = 'delete from tbl_wish where wish_id = %s and wish_user_id = %s'
                cursor.execute(sql, (_id, _user))
                result = cursor.fetchall()

                if len(result) is 0:
                    conn.commit()
                    return json.dumps({'status': 'OK'})
                else:
                    return json.dumps({'status': 'Error'})
        else:
            return render_template('error.html', error='Unauthorized Access')

    except Exception as e:
        return render_template('error.html', error=str(e))
    finally:
        conn.close()


@app.route('/getWishById/<int:wish_id>')
def get_wish_by_id(wish_id):
    try:
        if session.get('user'):
            _id = wish_id
            _user = session.get('user')

            with mysql.connect().cursor() as cursor:
                sql = 'select * from tbl_wish where wish_id = %s and wish_user_id = %s'
                cursor.execute(sql, (_id, _user))
                result = cursor.fetchall()

                wish = [{'Id': result[0][0], 'Title': result[0][1], 'Description': result[0][2],
                         'FilePath': result[0][5], 'Done': result[0][6], 'Private': result[0][7]}]

                return json.dumps(wish)
        else:
            return render_template('error.html', error='Unauthorized Access')

    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/getWish/<int:offset>')
def get_wish(offset):
    try:
        if session.get('user'):
            _user = session.get('user')
            _limit = int(request.args['itemPerPage'])
            _offset = offset

            with mysql.connect().cursor() as cursor:
                number_sql = '(select count(*), 1, 2, 3, 4, 5, 6, 7 from tbl_wish where wish_user_id = %s)'
                data_sql = '(select * from tbl_wish where wish_user_id = %s order by wish_date desc limit %s offset %s)'
                sql = ' union '.join([number_sql, data_sql])

                cursor.execute(sql, (_user, _user, _limit, _offset))
                wishes = cursor.fetchall()

                response = [{'total': wishes[0][0]}]
                wishes = wishes[1:]

                wishes_dict = []
                for wish in wishes:
                    wishes_dict.append({
                        'Id': wish[0],
                        'Title': wish[1],
                        'Description': wish[2],
                        'Date': wish[4]
                    })

                response.append(wishes_dict)
                return json.dumps(response)
        else:
            return render_template('error.html', error='Unauthorized Access')

    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/showAddWish')
def show_add_wish():
    return render_template('addWish.html')


@app.route('/addWish', methods=['POST'])
def add_wish():
    conn = mysql.connect()
    try:
        if session.get('user'):
            _title = request.form['inputTitle']
            _description = request.form['inputDescription']
            _user = session.get('user')
            _file_path = '' if request.form.get('filePath') is None \
                else request.form.get('filePath')
            _done = 0 if request.form.get('done') is None else 1
            _private = 0 if request.form.get('private') is None else 1

            with conn.cursor() as cursor:
                sql = 'insert into tbl_wish(wish_title, wish_description, wish_user_id, wish_file_path, wish_accomplished, wish_private) values(%s, %s, %s, %s, %s, %s)'
                cursor.execute(sql, (_title, _description, _user, _file_path, _done, _private))
                cursor.fetchone()
                conn.commit()

                return redirect('/userHome')
        else:
            return render_template('error.html', error='Unauthorized Access')

    except Exception as e:
        return render_template('error.html', error=str(e))
    finally:
        conn.close()


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')


@app.route('/showSignUp')
def show_sign_up():
    return render_template('signup.html')


@app.route('/showSignIn')
def show_sign_in():
    return render_template('signin.html')


@app.route('/validateLogin', methods=['POST'])
def validate_login():
    conn = mysql.connect()
    try:
        with conn.cursor() as cursor:
            _username = request.form['inputEmail']
            _password = request.form['inputPassword']
            sql = 'select * from tbl_user where user_username = %s'
            cursor.execute(sql, (_username,))

            data = cursor.fetchall()

            if len(data) > 0:
                if check_password_hash(str(data[0][3]), _password):
                    session['user'] = data[0][0]
                    return redirect('/userHome')
                else:
                    return render_template('error.html', error='Wrong Email address or Password.')
            else:
                render_template('error.html', error='Wrong Email address or Password.')

    except Exception as e:
        return render_template('error.html', error=str(e))

    finally:
        conn.close()


@app.route('/signUp', methods=['POST'])
def sign_up():
    _name = request.form['inputName']
    _email = request.form['inputEmail']
    _password = request.form['inputPassword']

    if _name and _email and _password:
        conn = mysql.connect()
        try:
            with conn.cursor() as cursor:
                _hash_password = generate_password_hash(_password)
                sql = 'select * from tbl_user where user_username = %s'
                cursor.execute(sql, (_email,))
                data = cursor.fetchall()

                if len(data) != 0:
                    resp = jsonify('{0} is already exist!!'.format(_email))
                    resp.status_code = 400
                    return resp

                sql = 'insert into tbl_user(user_name, user_username, user_password) values(%s, %s, %s)'
                cursor.execute(sql, (_name, _email, _hash_password))
                conn.commit()
                return redirect('/userHome.html')

        except Exception as e:
            return render_template('error.html', error=str(e))
        finally:
            conn.close()
    else:
        resp = jsonify('Enter the required field!!')
        resp.status_code = 40
        return resp


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        extension = os.path.splitext(file.filename)[1]
        f_name = str(uuid.uuid4()) + extension

        file.save(os.path.join(app.config['UPLOAD_FOLDER'], f_name))
        return json.dumps({'filename':f_name})


if __name__ == '__main__':
    app.run()
