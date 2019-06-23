from flask import Flask, render_template, request, json, redirect, session, jsonify
from flaskext.mysql import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'Famous'

mysql = MySQL()

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'vnfdjqhk66'
app.config['MYSQL_DATABASE_DB'] = 'BucketList'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
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


@app.route('/updateWish', methods=['POST'])
def update_wish():
    try:
        if session.get('user'):
            _user = session.get('user')
            _title = request.form['title']
            _description = request.form['description']
            _wish_id = request.form['id']

            conn = mysql.connect()
            with conn.cursor() as cursor:
                cursor.callproc('sp_updateWish', (_title, _description, _wish_id, _user))
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


@app.route('/deleteWish', methods=['POST'])
def delete_wish():
    try:
        if session.get('user'):
            _id = request.form['id']
            _user = session.get('user')

            conn = mysql.connect()
            with conn.cursor() as cursor:
                cursor.callproc('sp_deleteWish', (_id, _user))
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


@app.route('/getWishById', methods=['POST'])
def get_wish_by_id():
    try:
        if session.get('user'):
            _id = request.form['id']
            _user = session.get('user')

            with mysql.connect().cursor() as cursor:
                cursor.callproc('sp_getWishById', (_id, _user))
                result = cursor.fetchall()

                wish = [{'Id': result[0][0], 'Title': result[0][1], 'Description': result[0][2]}]

                return json.dumps(wish)
        else:
            return render_template('error.html', error='Unauthorized Access')

    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/getWish')
def get_wish():
    try:
        if session.get('user'):
            _user = session.get('user')

            with mysql.connect().cursor() as cursor:
                cursor.callproc('sp_GetWishByUser', (_user,))
                wishes = cursor.fetchall()

                wishes_dict = []
                for wish in wishes:
                    wishes_dict.append({
                        'Id': wish[0],
                        'Title': wish[1],
                        'Description': wish[2],
                        'Date': wish[4]
                    })
                return json.dumps(wishes_dict)
        else:
            return render_template('error.html', error='Unauthorized Access')

    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/showAddWish')
def show_add_wish():
    return render_template('addWish.html')


@app.route('/addWish', methods=['POST'])
def add_wish():
    try:
        if session.get('user'):
            _title = request.form['inputTitle']
            _description = request.form['inputDescription']
            _user = session.get('user')

            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_addWish', (_title, _description, _user))
            data = cursor.fetchall()

            if len(data) == 0:
                conn.commit()
                return redirect('/userHome')
            else:
                return render_template('error.html', error='An error occurred!')

        else:
            return render_template('error.html', error='Unauthorized Access')

    except Exception as e:
        return render_template('error.html', error=str(e))
    finally:
        cursor.close()
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
    try:
        _username = request.form['inputEmail']
        _password = request.form['inputPassword']

        con = mysql.connect()
        cursor = con.cursor()

        cursor.callproc('sp_validateLogin', (_username,))

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
        cursor.close()
        con.close()


@app.route('/signUp', methods=['POST'])
def sign_up():
    _name = request.form['inputName']
    _email = request.form['inputEmail']
    _password = request.form['inputPassword']

    if _name and _email and _password:
        try:
            conn = mysql.connect()
        except Exception as e:
            return render_template('error.html', error=str(e))

        try:
            with conn.cursor() as cursor:
                _hash_password = generate_password_hash(_password)
                cursor.callproc('sp_createUser', (_name, _email, _hash_password))
                data = cursor.fetchall()

                if len(data) is 0:
                    conn.commit()
                    return redirect('/userHome.html')
                else:
                    return json.dumps({'error': str(data[0])})
        except Exception as e:
            return render_template('error.html', error=str(e))
        finally:
            conn.close()
    else:
        resp = jsonify('field error')
        resp.status_code = 400
        return resp


if __name__ == '__main__':
    app.run()
