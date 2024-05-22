from django.shortcuts import render, redirect,HttpResponse,HttpResponseRedirect
from django.contrib.auth import authenticate,logout
from django.contrib.auth import login
from .forms import CustomCreationForm,ProjectForm,ConnectionDetailsForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User,Project,ConnectionDetails,ProjectTable, ProjectTableRow,ProjectTableColumn,TestResult
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import pytz
import requests
import keyring as kr
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponseForbidden
import matplotlib.pyplot as plt
import os
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from .utils import create_dag
import seaborn as sns
import pandas as pd
from django.conf import settings

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = CustomCreationForm()
    if request.method == "POST":
        form = CustomCreationForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            confirm_password = form.cleaned_data.get('password2')
            user = form.save(commit=False)
            user.username = username
            user.save()
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')

    return render(request, "register.html", {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            username = request.POST['email']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('projects')
            else:
                messages.error(request, "Invalid username or password")
                return redirect('login')
        else:
            return render(request, 'login.html')

        return render(request,'login.html')

@login_required
def logout_form(request):
    logout(request)
    return redirect('login')


def home(request):
    # print(request.email)
    print(request.user)
    public_projects = Project.objects.select_related('user').filter(visibility='public')
    print(public_projects)
    print(kr.get_password("GeeksforGeeks","dev"))
    return render(request, 'home.html', {'public_projects': public_projects})


def my_projects(request):
    user_projects = Project.objects.filter(user=request.user)
    return render(request, 'ind.html', {'projects': user_projects})
    
def project_details(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        test_results = TestResult.objects.filter(project_id=project_id)
        tables_info = []

        if project.visibility == "public":
            tables_info = [{'name': test_result.table_name,
                            'row_count': test_result.total_row,
                            'column_count': test_result.total_column} for test_result in test_results]
        elif project.visibility == "private" and project.user == request.user:
            tables_info = [{'name': test_result.table_name,
                            'row_count': test_result.total_row,
                            'column_count': test_result.total_column} for test_result in test_results]

        context = {
            'tables_info': tables_info,
            'project_id': project_id,
            'project': project
        }
        return render(request, 'project_details.html', context)
    except Project.DoesNotExist:
        return render(request, 'error.html', {'error_message': f'Project not found with this id {project_id}'})


def table_details(request, project_id, table_name):
    test_result = TestResult.objects.get(project_id=project_id, table_name=table_name)  # Get your TestResult instance

    # Extract outliers data
    outliers_data = test_result.outliers

    # Create a box plot
    plt.figure(figsize=(10, 6))
    plt.boxplot(outliers_data.values(), labels=outliers_data.keys())
    plt.xlabel('Field')
    plt.ylabel('Value')
    plt.title('Box Plot for Outliers')
    plt.xticks(rotation=45)
    plt.tight_layout()
    image_name = f'box_plot_{project_id}_{table_name}.png'
    # Save the box plot as an image
    plot_image_path = os.path.join(settings.MEDIA_ROOT,image_name )
    plt.savefig(plot_image_path)
    # Extract outliers data
    correlation_matrix = test_result.correlation_coefficients
    correlation_matrix_df = pd.DataFrame.from_dict(correlation_matrix)

    # Generate correlation matrix plot as a heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix_df, annot=True, cmap='viridis', fmt=".2f")
    plt.title('Correlation Matrix')
    plt.xticks(rotation=45)
    plt.yticks(rotation=0)
    plt.tight_layout()

    # Save the heatmap as an image
    correlation_matrix_image_name = f'correlation_matrix_{project_id}_{table_name}.png'
    correlation_matrix_image_path = os.path.join(settings.MEDIA_ROOT, correlation_matrix_image_name)
    plt.savefig(correlation_matrix_image_path)
    plt.close()  # Close the plot to free memory

    # Prepare the context with other data if needed
    context = {
        'test_result': test_result,
        'plot_image_path': image_name,
        'correlation_matrix_image_path': correlation_matrix_image_name
        # Add other data to the context as needed
    }
    
    return render(request, 'tables_details.html', context)

# def table_details(request, project_id, table_name):
#     test_result = TestResult.objects.get(project_id=project_id, table_name=table_name)  # Get your TestResult instance

#     context = {
#         'test_result': test_result,
#     }
#     print(test_result)
#     return render(request, 'tables_details.html', context)

def projects(request):
    user_projects = Project.objects.filter(user=request.user).prefetch_related('connection_details')
    for project in user_projects:
        try:
            project.total_tables = TestResult.objects.filter(project_id=project.id).count()
        except ConnectionDetails.DoesNotExist:
            project.total_tables = 0
    return render(request, 'projects.html', {'projects': user_projects})

def test_database_connection(connector_type,host, port, username, password, database_name):
    connection_string = f"{connector_type}://{username}:{password}@{host}:{port}/{database_name}"
    engine = create_engine(connection_string)
    try:
        with engine.connect():
            return True, None  # Connection successful
    except OperationalError as e:
        return False, str(e)  # Connection failed, return the error message

def create_project(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        visibility = request.POST.get('visibility')
        connector_type = request.POST.get('connector_type')
        host = request.POST.get('host')
        port = request.POST.get('port')
        username = request.POST.get('username')
        password = request.POST.get('password')
        database_name = request.POST.get('database_name')

        is_valid_connection, error_message = test_database_connection(connector_type,host, port, username, password, database_name)
        if not is_valid_connection:
            messages.error(request, f"Connection test failed: {error_message}")
            return render(request, 'create_project.html')

        project = Project.objects.create(
            user=request.user,  
            name=name,
            description=description,
            visibility=visibility
        )
        connection_details = ConnectionDetails.objects.create(
            project=project,
            connector_type=connector_type,
            host=host,
            port=port,
            username=username,
            database_name=database_name,
            password = password
        )
        return redirect('projects')  
    else:
        return render(request, 'create_project.html')

def update_project(request, project_id):
    project = Project.objects.get(pk=project_id)
    connection_details = project.connection_details

    if request.method == 'POST':
        project_form = ProjectForm(request.POST, instance=project)
        connection_form = ConnectionDetailsForm(request.POST, instance=connection_details)
        if project_form.is_valid() and connection_form.is_valid():
            connector_type = request.POST.get('connector_type')
            host = request.POST.get('host')
            port = request.POST.get('port')
            username = request.POST.get('username')
            password = request.POST.get('password')
            database_name = request.POST.get('database_name')

            is_valid_connection, error_message = test_database_connection(connector_type, host, port, username, password, database_name)
            if not is_valid_connection:
                messages.error(request, f"Connection test failed: {error_message}")
                return render(request, 'update_project.html', {'project_form': project_form, 'connection_form': connection_form, 'project': project})
            project_form.save()
            connection_form.save()
            return redirect('projects')
    else:
        project_form = ProjectForm(instance=project)
        connection_form = ConnectionDetailsForm(instance=connection_details)

    return render(request, 'update_project.html', {'project_form': project_form, 'connection_form': connection_form, 'project': project})


def delete_project(request, project_id):
    project = Project.objects.get(pk=project_id)
    if request.method == 'POST':
        project.delete()
        dag_file_path = f'/media/dev/5EEA651EEA64F425/Trainning/airflow-django/dags/yout_{project_id}.py'
        if os.path.exists(dag_file_path):
            os.remove(dag_file_path)
        return redirect('projects')
    return render(request, 'confirm_project_delete.html', {'project': project})


def calculate_success_rate(task_status):
    total_tasks = len(task_status)
    successful_tasks = sum(status == 'success' for status in task_status.values())
    success_rate = (successful_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    return success_rate

def calculate_average_duration(dag_runs):
    durations = []
    for run in dag_runs:
        start_date_str = run['start_date']
        end_date_str = run['end_date']
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S.%f%z')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M:%S.%f%z')
            duration = (end_date - start_date).total_seconds()
            if duration > 0:
                durations.append(duration)

    total_duration = sum(durations)
    num_durations = len(durations)
    if num_durations > 0:
        average_duration = total_duration / num_durations
        return round(average_duration, 2)
    else:
        return None

def manage_pipeline(request, project_id):
    try:
        project = Project.objects.get(id=project_id, user=request.user)
    except Project.DoesNotExist:
        return render(request, 'error.html', {'error_message': f'You are not authorized to access this page.'})

    dag_id = f"your_{project_id}"
    api_url_all_runs = f'http://localhost:8080/api/v1/dags/{dag_id}/dagRuns'
    api_url_info = f'http://localhost:8080/api/v1/dags/{dag_id}'
    username = 'admin'
    password = 'your_password'

    response_all_runs = requests.get(api_url_all_runs, auth=(username, password))
    if response_all_runs.status_code != 200:
        return render(request, 'error.html', {'error_message': f'Failed to fetch DAG runs for {dag_id}'})

    dag_runs = response_all_runs.json().get('dag_runs', [])
    # print(dag_runs)
    response_info = requests.get(api_url_info, auth=(username, password))
    if response_info.status_code != 200:
        return render(request, 'error.html', {'error_message': f'Failed to fetch DAG information for {dag_id}'})

    dag_info = response_info.json()
    # print(dag_info)
    average_duration = calculate_average_duration(dag_runs)
    print("sfsdkjfgsk",average_duration)

    next_dag_run_str = dag_info.get('next_dagrun_create_after')
    india_timezone = pytz.timezone('Asia/Kolkata')
    next_dag_run_utc = datetime.strptime(next_dag_run_str, '%Y-%m-%dT%H:%M:%S%z')
    next_dag_run_india = next_dag_run_utc.astimezone(india_timezone)
    formatted_next_dag_run = next_dag_run_india.strftime('%Y-%m-%d %H:%M:%S %Z%z')

    display_info = {
        'average_duration': average_duration,
        'dag_id': dag_info.get('dag_id'),
        'description': dag_info.get('description'),
        'schedule_interval': dag_info.get('schedule_interval', {}).get('value'),
        'next_dag_run': formatted_next_dag_run,
        'max_active_runs': dag_info.get('max_active_runs'),
        'max_active_tasks': dag_info.get('max_active_tasks'),
        'is_active': dag_info.get('is_active'),
        'is_paused': dag_info.get('is_paused'),
        'has_import_errors': dag_info.get('has_import_errors'),
        'has_task_concurrency_limits': dag_info.get('has_task_concurrency_limits'),
        'timetable_description': dag_info.get('timetable_description')
    }

    return render(request, 'manage_pipeline.html', {'display_info': display_info, 'dag_runs': dag_runs,'project_id':project_id})

def pause_dag(request, dag_id):
    if request.method == "POST":
        username = 'admin'
        password = 'your_password'
        project_id = request.POST['project_id']

        api_url_info = f'http://localhost:8080/api/v1/dags/{dag_id}'
        response_info = requests.get(api_url_info, auth=(username, password))

        if response_info.status_code == 200:
            dag_info = response_info.json()
            is_paused = dag_info.get('is_paused')

            new_paused_status = not is_paused
            payload = {"is_paused": new_paused_status}
            response_patch = requests.patch(api_url_info, json=payload, auth=(username, password))

            if response_patch.status_code == 200:
                if new_paused_status:
                    messages.success(request, "DAG paused successfully.")
                else:
                    messages.success(request, "DAG unpaused successfully.")
                return redirect('manage_pipeline', project_id=project_id)
            else:
                messages.error(request, "Failed to pause/unpause DAG.")
        else:
            messages.error(request, "Failed to fetch DAG information.")

    return redirect('manage_pipeline', project_id=project_id)

def dag_run_logs(request, dag_id, dag_run_id):
    username = 'admin'
    password = 'your_password'
    url = f"http://localhost:8080/api/v1/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/analyze_data_distribution/logs/1"

    try:
        response = requests.get(url,auth=(username,password))
        print(response)
        if response.status_code == 200:
            logs = response.text
            return render(request, 'dag_logs.html', {'logs': logs})
        else:
            return render(request, 'error.html', {'error_message': f'Failed to retrieve logs for DAG run {response}'})

    except Exception as e:
        return render(request, 'error.html', {'error_message': str(e)})

def trigger_dag(request, project_id):
    AIRFLOW_URL = "http://localhost:8080"
    USERNAME = "admin"
    PASSWORD = "your_password"
    DAG_ID = f'your_{project_id}'
    date = datetime.now()
    print(date)

    url = f"{AIRFLOW_URL}/api/v1/dags/{DAG_ID}/dagRuns"
    payload = {
        "conf": {} 
    }
    response = requests.post(url, json=payload, auth=(USERNAME, PASSWORD))
    print(response.text)
    if response.status_code == 200:
        messages.success(request, "DAG triggered successfully.")
        print("DAG triggered successfully.")
    else:
        messages.error(request, "Failed to trigger DAG.")
        print("Failed to trigger DAG.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('home')))


def create_dag_form(request,project_id):

    if request.method == 'POST':
        project = Project.objects.get(id=project_id)
        connection_details = project.connection_details
        connection_string = f"{connection_details.connector_type}://{quote_plus(connection_details.username)}:{quote_plus(connection_details.password)}@{connection_details.host}:{connection_details.port}/{connection_details.database_name}"
        dag_id = f"your_{project_id}"
        kr.set_password("profiling",f"{dag_id}",f"{connection_string}")
     
        start_date = request.POST.get('start_date')
        schedule_interval = request.POST.get('schedule_interval')
        # user_datetime = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
        dag_id = create_dag(project_id, start_date, schedule_interval, connection_details,dag_id)
        
        if dag_id:
            project.pipeline = dag_id
            project.save()
            messages.success(request, "DAG info saved.")
        else:
            messages.error(request, "Failed to create DAG.")
        
        return render(request, 'create_dag_form.html')
    else:
        return render(request, 'create_dag_form.html')

        # user_timezone = pytz.timezone('Asia/Kolkata')  
        # user_datetime = user_timezone.localize(user_datetime)

        # utc_datetime = user_datetime.astimezone(pytz.utc)
        # formatted_datetime = utc_datetime.strftime('%Y-%m-%dT%H:%M')
        # print("us time",utc_datetime)
        # print("formatted_datetime time",formatted_datetime)
        # schedule_interval = request.POST.get('schedule_interval')

#         dag_content = f'''
# from airflow import DAG
# from airflow.operators.python_operator import PythonOperator
# from datetime import datetime, timedelta
# from sqlalchemy import create_engine, MetaData, Table, select, func, text, INTEGER, NUMERIC, FLOAT
# from sqlalchemy.exc import IntegrityError
# import json
# from decimal import Decimal
# import pandas as pd
# import numpy as np
# import keyring as kr 

# dag_name = '{dag_id}'
# source_db_url = kr.get_password("profiling",dag_name)
# destination_db_url = 'mysql://root:Devhadvani_1@localhost:3306/data_plateform'

# default_args = {{
#     'owner': 'airflow',
#     'depends_on_past': False,
#     'email_on_failure': False,
#     'email_on_retry': False,
#     'retries': 1,
#     'retry_delay': timedelta(minutes=1),
#     'start_date': datetime.strptime('{formatted_datetime}', '%Y-%m-%dT%H:%M'),
# }}
# tables_data = {{}}

# class DecimalEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, Decimal):
#             return str(obj)
#         elif isinstance(obj, datetime):
#             return obj.isoformat()
#         return super().default(obj)

# def analyze_data_distribution():
#     tables_data = {{}}
#     source_engine = create_engine(source_db_url)
#     source_conn = source_engine.connect()
#     metadata = MetaData()
#     metadata.reflect(bind=source_engine)
#     for table_name, table_obj in metadata.tables.items():
#         data_types = {{}}
#         missing_values = {{}}
#         unique_values = {{}}
#         descriptive_stats = {{}}
#         duplicates = {{}}
#         foreign_keys = {{}}
#         correlation_coefficients = {{}}
#         total_row = source_conn.execute(select([func.count()]).select_from(table_obj)).scalar()
#         total_column = len(table_obj.columns)        
#         for column in table_obj.columns:
#             data_types[column.name] = str(column.type)
#             result = source_conn.execute(select([func.count()]).where(column == None))
#             missing_values[column.name] = result.scalar()
#             result = source_conn.execute(select([func.count(func.distinct(column))]))
#             unique_values[column.name] = result.scalar()
#             if isinstance(column.type, (INTEGER, NUMERIC, FLOAT)):
#                 query = select([
#                     func.avg(column),
#                     func.stddev(column),
#                     func.min(column),
#                     func.max(column)
#                 ])
#                 result = source_conn.execute(query)
#                 mean, std_dev, min_val, max_val = result.fetchone()
#                 descriptive_stats[column.name] = {{'mean': mean, 'std_dev': std_dev, 'min': min_val, 'max': max_val}}
#             query = select([column, func.count()]).group_by(column).having(func.count() > 1)
#             result = source_conn.execute(query)
#             duplicates[column.name] = [{{'value': row[0], 'count': row[1]}} for row in result]
#             numerical_columns = [column.name for column in table_obj.columns if isinstance(column.type, (INTEGER, NUMERIC, FLOAT))]
#             numerical_data = pd.read_sql_table(table_name, source_engine, columns=numerical_columns)
#             numerical_data = pd.read_sql_table(table_name, source_engine, columns=numerical_columns)
#             numerical_data = numerical_data.apply(pd.to_numeric, errors='coerce')
#             correlations = numerical_data.corr().to_dict()
#             correlation_coefficients = {{key: {{k: v if not np.isnan(v) else None for k, v in val.items()}} for key, val in correlations.items()}}

#             # correlation_coefficients[column.name] = {{key: val if not np.isnan(val) else None for key, val in correlations.items()}}
         
#             print(duplicates[column.name])
#         tables_data[table_name] = {{
#             'total_row': total_row,
#             'total_column': total_column,            
#             'data_types': data_types,
#             'missing_values': missing_values,
#             'unique_values': unique_values,
#             'descriptive_stats': descriptive_stats,
#             'duplicates': duplicates,
#             'foreign_keys': foreign_keys,
#             'correlation_coefficients': correlation_coefficients,
#         }}
#     source_conn.close()
#     destination_engine = create_engine(destination_db_url)
#     destination_conn = destination_engine.connect()



#     for table_name, table_data in tables_data.items():
#         for column_name, duplicates_list in table_data['duplicates'].items():
#             for duplicate_entry in duplicates_list:
#                 try:
#                     if isinstance(duplicate_entry['value'], bytes):
#                         duplicate_entry['value'] = duplicate_entry['value'].decode('utf-8')
#                 except UnicodeDecodeError:
#                     duplicate_entry['value'] = 'Decoding error: unable to decode as UTF-8'
#         try:
#             existing_record = destination_conn.execute(
#                 text("SELECT * FROM testresult WHERE project_id = :project_id AND table_name = :table_name"),
#                 {{'project_id': {project_id}, 'table_name': table_name}}
#             ).fetchone()
#             current_time = datetime.now()
#             if existing_record:
#                 destination_conn.execute(
#                     text("UPDATE testresult SET total_row = :total_row, total_column =:total_column, data_types = :data_types, missing_values = :missing_values, unique_values = :unique_values, descriptive_statistics = :descriptive_statistics, data_quality_issues = :data_quality_issues,correlation_coefficients=:correlation_coefficients, updated_at = :updated_at WHERE project_id = :project_id AND table_name = :table_name"),
#                     {{
#                         'project_id': {project_id},
#                         'table_name': table_name,
#                         'total_row': table_data['total_row'],
#                         'total_column': table_data['total_column'],                        
#                         'data_types': json.dumps(table_data['data_types']),
#                         'missing_values': json.dumps(table_data['missing_values']),
#                         'unique_values': json.dumps(table_data['unique_values']),
#                         'descriptive_statistics': json.dumps(table_data['descriptive_stats'],  cls=DecimalEncoder),
#                         'data_quality_issues': json.dumps(table_data['duplicates'],  cls=DecimalEncoder),
#                         'correlation_coefficients' : json.dumps(table_data['correlation_coefficients'],  cls=DecimalEncoder),
#                         'updated_at': current_time
#                     }}
#                 )
#             else:
#                 destination_conn.execute(
#                     text("INSERT INTO testresult (project_id, table_name,total_row,total_column, data_types, missing_values, unique_values, descriptive_statistics, data_quality_issues,correlation_coefficients, created_at, updated_at) VALUES (:project_id, :table_name,:total_row,:total_column, :data_types, :missing_values, :unique_values, :descriptive_statistics, :data_quality_issues,:correlation_coefficients, :created_at, :updated_at)"),
#                     {{
#                         'project_id': {project_id},
#                         'table_name': table_name,
#                         'total_row': table_data['total_row'],
#                         'total_column': table_data['total_column'],                        
#                         'data_types': json.dumps(table_data['data_types']),
#                         'missing_values': json.dumps(table_data['missing_values']),
#                         'unique_values': json.dumps(table_data['unique_values']),
#                         'descriptive_statistics': json.dumps(table_data['descriptive_stats'],  cls=DecimalEncoder),
#                         'data_quality_issues': json.dumps(table_data['duplicates'],  cls=DecimalEncoder),
#                         'correlation_coefficients' : json.dumps(table_data['correlation_coefficients'],  cls=DecimalEncoder),
#                         'created_at': current_time,
#                         'updated_at': current_time
#                     }}
#                 )

#         except IntegrityError as e:
#             print(f"Integrity error occurred while inserting data for table: ")

# with DAG('your_{project_id}', 
#          default_args=default_args, 
#          schedule_interval='{schedule_interval}',
#          catchup=False) as dag:
#     analyze_data_task = PythonOperator(
#         task_id='analyze_data_distribution',
#         python_callable=analyze_data_distribution
#     )
# '''


#         dag_file_path =  f'/media/dev/5EEA651EEA64F425/Trainning/airflow-django/dags/yout_{project_id}.py'

#         with open(dag_file_path, 'w') as f:
#             f.write(dag_content)
#         project.pipeline = dag_id
#         project.save()
#         messages.success(request, "DAG info saved.")
    
#     return render(request,'create_dag_form.html')