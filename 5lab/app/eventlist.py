from flask import render_template, url_for, request, redirect, flash, Blueprint, g, redirect, send_file
from flask_login import login_required, current_user
from functools import wraps
from app import db
from check_rights import CheckRights
import math
import csv
from io import StringIO, BytesIO


bp_eventlist = Blueprint('eventlist', __name__, url_prefix='/eventlist')
PER_PAGE =10
#FIELDS = ["id", "first_name", "last_name", "path", "created_at"]

@bp_eventlist.route('/show-all')
@login_required
def show():
    page=int(request.args.get('page',1))
    cursor = db.connection().cursor(named_tuple=True)

    if current_user.is_admin():
        query = '''SELECT visit_logs.id, users3.first_name, users3.last_name, visit_logs.path, visit_logs.created_at 
        FROM visit_logs LEFT JOIN users3 ON visit_logs.user_id = users3.id ORDER BY visit_logs.created_at DESC LIMIT %s OFFSET %s '''
        cursor.execute(query, (PER_PAGE,(page -1)*PER_PAGE))
    else:
        query = '''SELECT visit_logs.id, users3.first_name, users3.last_name, visit_logs.path, visit_logs.created_at 
        FROM visit_logs LEFT JOIN users3 ON visit_logs.user_id = users3.id WHERE visit_logs.user_id = %s 
        ORDER BY visit_logs.created_at DESC LIMIT %s OFFSET %s '''
        cursor.execute(query,(current_user.id, PER_PAGE,(page -1)*PER_PAGE))
    events = cursor.fetchall()
    cursor.close()
    count=get_count_page()
    return render_template('visits/event.html', events = events, count=count, page=page)


def get_count_page():
    cursor = db.connection().cursor(named_tuple=True)
    if current_user.is_admin():
        query = 'SELECT COUNT(*) as count FROM visit_logs'
        cursor.execute(query)
    else:
        query = 'SELECT COUNT(*) as count FROM visit_logs WHERE user_id = %s'
        cursor.execute(query, (current_user.id,))
    count = math.ceil((cursor.fetchone().count/PER_PAGE) + 1)
    cursor.close()
    return count


@bp_eventlist.route('/show-path')
@login_required
def show_path():
    cursor = db.connection().cursor(named_tuple=True)
    query = 'SELECT COUNT(*) as count_path, path FROM visit_logs GROUP BY path'
    cursor.execute(query)
    events = cursor.fetchall()
    cursor.close()
    return render_template('visits/event_path.html', events = events)

@bp_eventlist.route('/show-path-user')
@login_required
def show_path_user():
    cursor = db.connection().cursor(named_tuple=True)
    if current_user.is_admin():
        query = '''SELECT COUNT(*) as count, users3.first_name, users3.last_name 
            FROM visit_logs LEFT JOIN users3 on visit_logs.user_id = users3.id
            GROUP BY users3.first_name, users3.last_name ORDER BY count DESC'''
        cursor.execute(query)
    else:
        query = '''SELECT COUNT(*) as count, users3.first_name, users3.last_name 
            FROM visit_logs LEFT JOIN users3 on visit_logs.user_id = users3.id WHERE visit_logs.user_id = %s
            GROUP BY users3.first_name, users3.last_name ORDER BY count DESC'''
        cursor.execute(query, (current_user.id,))
    events = cursor.fetchall()
    cursor.close()
    return render_template('visits/event_path_user.html', events = events)

@bp_eventlist.route('/show-path-site')
@login_required
def show_path_site():
    cursor = db.connection().cursor(named_tuple=True)
    query = '''SELECT COUNT(*) as count, path FROM visit_logs WHERE user_id = %s GROUP BY path ORDER BY count DESC'''
    cursor.execute(query, (current_user.id,))
    events = cursor.fetchall()
    cursor.close()
    return render_template('visits/event_path_site.html', events = events)
"""
@bp_eventlist.route("/csvsave")
def save_to_csv():
    cursor = db.connection().cursor(named_tuple=True)
    query = 'SELECT * FROM visit_logs'
    #query = '''SELECT visit_logs.id, CONCAT(users3.first_name, ' ', users3.last_name) AS name, visit_logs.path, visit_logs.created_at
    #FROM visit_logs LEFT JOIN users3 ON visit_logs.user_id = users3.id'''
    cursor.execute(query)
    logs = cursor.fetchall()

    # data = StringIO()
    # w = csv.writer(data)
    csv_data = ",".join(FIELDS) + "\n"
    for item in logs:
        csv_data += ",".join([str(getattr(item, field, '')) for field in FIELDS]) + "\n"
    file = BytesIO()
    file.write(csv_data.encode("UTF-8"))
    file.seek(0)
    return send_file(file, download_name="logs.csv")"""

@bp_eventlist.route("/csvsave-visits")
def save_to_csv_visits():
    cursor = db.connection().cursor(named_tuple=True)

    if current_user.is_admin():
        query = '''SELECT visit_logs.id, CONCAT(users3.first_name, ' ', users3.last_name) AS name, visit_logs.path, visit_logs.created_at
        FROM visit_logs LEFT JOIN users3 ON visit_logs.user_id = users3.id'''
        cursor.execute(query)
    else:
        query = '''SELECT visit_logs.id, CONCAT(users3.first_name, ' ', users3.last_name) AS name, visit_logs.path, visit_logs.created_at
        FROM visit_logs LEFT JOIN users3 ON visit_logs.user_id = users3.id WHERE visit_logs.user_id = %s'''
        cursor.execute(query, (current_user.id,))
    logs = cursor.fetchall()

    FIELDS = ["id", "name", "path", "created_at"]
    csv_data = ",".join(FIELDS) + "\n"
    for item in logs:
        csv_data += ",".join([str(getattr(item, field, '')) for field in FIELDS]) + "\n"
    file = BytesIO()
    file.write(csv_data.encode("UTF-8"))
    file.seek(0)
    return send_file(file, download_name="logs.csv")

@bp_eventlist.route("/csvsave-users")
def save_to_csv_users():
    cursor = db.connection().cursor(named_tuple=True)
    if current_user.is_admin():
        query = '''SELECT users3.id, CONCAT(users3.first_name, ' ', users3.last_name) AS name, COUNT(*) as page_count
        FROM visit_logs LEFT JOIN users3 ON visit_logs.user_id = users3.id GROUP BY users3.id'''
        cursor.execute(query)
    else:
        query = '''SELECT users3.id, CONCAT(users3.first_name, ' ', users3.last_name) AS name, COUNT(*) as page_count
        FROM visit_logs LEFT JOIN users3 ON visit_logs.user_id = users3.id where visit_logs.user_id = %s GROUP BY users3.id'''
        cursor.execute(query, (current_user.id,))
    logs = cursor.fetchall()

    FIELDS = ["id", "name", "page_count"]
    csv_data = ",".join(FIELDS) + "\n"
    for item in logs:
        csv_data += ",".join([str(getattr(item, field, '')) for field in FIELDS]) + "\n"
    file = BytesIO()
    file.write(csv_data.encode("UTF-8"))
    file.seek(0)
    return send_file(file, download_name="logs.csv")

@bp_eventlist.route("/csvsave-pages")
def save_to_csv_pages():
    cursor = db.connection().cursor(named_tuple=True)
    query = '''SELECT MIN(id) as id, path, COUNT(*) as visit_count FROM visit_logs WHERE user_id = %s GROUP BY path'''
    cursor.execute(query, (current_user.id,))
    logs = cursor.fetchall()

    FIELDS = ["id", "path", "visit_count"]
    csv_data = ",".join(FIELDS) + "\n"
    for item in logs:
        csv_data += ",".join([str(getattr(item, field, '')) for field in FIELDS]) + "\n"
    file = BytesIO()
    file.write(csv_data.encode("UTF-8"))
    file.seek(0)
    return send_file(file, download_name="logs.csv")
