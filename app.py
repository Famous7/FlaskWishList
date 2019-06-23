from flask import Flask, render_template, request, json, redirect, session
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


@app.route('/')
def main():
    return render_template('index.html')


@app.route('/userHome')
def user_home():
    if session.get('user'):
        return render_template('userHome.html')
    else:
        return render_template('error.html', error='Unauthorized Access')


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
                        'id': wish[0],
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
    try:
        _name = request.form['inputName']
        _email = request.form['inputEmail']
        _password = request.form['inputPassword']

        if _name and _email and _password:

            conn = mysql.connect()
            cursor = conn.cursor()

            _hash_password = generate_password_hash(_password)
            print(len(_hash_password))
            cursor.callproc('sp_createUser', (_name, _email, _hash_password))
            data = cursor.fetchall()

            if len(data) is 0:
                conn.commit()
                return json.dumps({'message': 'User created successfully !'})
            else:
                return json.dumps({'error': str(data[0])})
        else:
            return json.dumps({'html': '<span>Enter the required fields</span>'})

    except Exception as e:
        return json.dumps({'error': str(e)})
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    app.run()
