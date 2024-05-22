from datetime import datetime, timedelta
import pytz

def create_dag(project_id,start_date, schedule_interval, connection_details,dag_id):
    start_date = start_date
    user_datetime = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
    user_timezone = pytz.timezone('Asia/Kolkata')
    user_datetime = user_timezone.localize(user_datetime)
    utc_datetime = user_datetime.astimezone(pytz.utc)
    formatted_datetime = utc_datetime.strftime('%Y-%m-%dT%H:%M')
    dag_content = f'''
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from sqlalchemy import create_engine, MetaData, Table, select, func, text, INTEGER, NUMERIC, FLOAT
from sqlalchemy.exc import IntegrityError
import json
from decimal import Decimal
import pandas as pd
import numpy as np
import keyring as kr 

dag_name = '{dag_id}'
source_db_url = kr.get_password("profiling",dag_name)
destination_db_url = 'mysql://root:Devhadvani_1@localhost:3306/data_plateform'

default_args = {{
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
    'start_date': datetime.strptime('{formatted_datetime}', '%Y-%m-%dT%H:%M'),
}}
tables_data = {{}}

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def analyze_data_distribution():
    tables_data = {{}}
    outliers_data = {{}}
    source_engine = create_engine(source_db_url)
    source_conn = source_engine.connect()
    metadata = MetaData()
    metadata.reflect(bind=source_engine)
    for table_name, table_obj in metadata.tables.items():
        data_types = {{}}
        missing_values = {{}}
        unique_values = {{}}
        descriptive_stats = {{}}
        duplicates = {{}}
        foreign_keys = {{}}
        correlation_coefficients = {{}}
        total_row = source_conn.execute(select([func.count()]).select_from(table_obj)).scalar()
        total_column = len(table_obj.columns)        
        for column in table_obj.columns:
            data_types[column.name] = str(column.type)
            result = source_conn.execute(select([func.count()]).where(column == None))
            missing_values[column.name] = result.scalar()
            result = source_conn.execute(select([func.count(func.distinct(column))]))
            unique_values[column.name] = result.scalar()
            if isinstance(column.type, (INTEGER, NUMERIC, FLOAT)):
                query = select([
                    func.avg(column),
                    func.stddev(column),
                    func.min(column),
                    func.max(column)
                ])
                result = source_conn.execute(query)
                mean, std_dev, min_val, max_val = result.fetchone()
                descriptive_stats[column.name] = {{'mean': mean, 'std_dev': std_dev, 'min': min_val, 'max': max_val}}
            query = select([column, func.count()]).group_by(column).having(func.count() > 1)
            result = source_conn.execute(query)
            duplicates[column.name] = [{{'value': row[0], 'count': row[1]}} for row in result]
            numerical_columns = [column.name for column in table_obj.columns if isinstance(column.type, (INTEGER, NUMERIC, FLOAT))]
            numerical_data = pd.read_sql_table(table_name, source_engine, columns=numerical_columns)
            numerical_data = pd.read_sql_table(table_name, source_engine, columns=numerical_columns)
            numerical_data = numerical_data.apply(pd.to_numeric, errors='coerce')
            correlations = numerical_data.corr().to_dict()
            correlation_coefficients = {{key: {{k: v if not np.isnan(v) else None for k, v in val.items()}} for key, val in correlations.items()}}
            quartiles = numerical_data.quantile([0.25, 0.75])
            lower_quartile = quartiles.loc[0.25]
            upper_quartile = quartiles.loc[0.75]
            iqr = upper_quartile - lower_quartile
            lower_bound = lower_quartile - 1.5 * iqr
            upper_bound = upper_quartile + 1.5 * iqr
            outliers = {{}}
            for col in numerical_data.columns:
                outliers[col] = numerical_data[(numerical_data[col] < lower_bound[col]) | (numerical_data[col] > upper_bound[col])][col].tolist()
            outliers_data[table_name] = outliers         
            print(duplicates[column.name])
        tables_data[table_name] = {{
            'total_row': total_row,
            'total_column': total_column,            
            'data_types': data_types,
            'missing_values': missing_values,
            'unique_values': unique_values,
            'descriptive_stats': descriptive_stats,
            'duplicates': duplicates,
            'foreign_keys': foreign_keys,
            'correlation_coefficients': correlation_coefficients,
            'outliers': outliers_data[table_name] 
        }}
    source_conn.close()
    destination_engine = create_engine(destination_db_url)
    destination_conn = destination_engine.connect()



    for table_name, table_data in tables_data.items():
        for column_name, duplicates_list in table_data['duplicates'].items():
            for duplicate_entry in duplicates_list:
                try:
                    if isinstance(duplicate_entry['value'], bytes):
                        duplicate_entry['value'] = duplicate_entry['value'].decode('utf-8')
                except UnicodeDecodeError:
                    duplicate_entry['value'] = 'Decoding error: unable to decode as UTF-8'
        try:
            existing_record = destination_conn.execute(
                text("SELECT * FROM testresult WHERE project_id = :project_id AND table_name = :table_name"),
                {{'project_id': {project_id}, 'table_name': table_name}}
            ).fetchone()
            current_time = datetime.now()
            if existing_record:
                destination_conn.execute(
                    text("UPDATE testresult SET total_row = :total_row, total_column =:total_column, data_types = :data_types, missing_values = :missing_values, unique_values = :unique_values, descriptive_statistics = :descriptive_statistics, data_quality_issues = :data_quality_issues,correlation_coefficients=:correlation_coefficients, outliers = :outliers, updated_at = :updated_at WHERE project_id = :project_id AND table_name = :table_name"),
                    {{
                        'project_id': {project_id},
                        'table_name': table_name,
                        'total_row': table_data['total_row'],
                        'total_column': table_data['total_column'],                        
                        'data_types': json.dumps(table_data['data_types']),
                        'missing_values': json.dumps(table_data['missing_values']),
                        'unique_values': json.dumps(table_data['unique_values']),
                        'descriptive_statistics': json.dumps(table_data['descriptive_stats'],  cls=DecimalEncoder),
                        'data_quality_issues': json.dumps(table_data['duplicates'],  cls=DecimalEncoder),
                        'correlation_coefficients' : json.dumps(table_data['correlation_coefficients'],  cls=DecimalEncoder),
                        'outliers': json.dumps(table_data['outliers']),
                        'updated_at': current_time
                    }}
                )
            else:
                destination_conn.execute(
                    text("INSERT INTO testresult (project_id, table_name,total_row,total_column, data_types, missing_values, unique_values, descriptive_statistics, data_quality_issues,correlation_coefficients, outliers, created_at, updated_at) VALUES (:project_id, :table_name,:total_row,:total_column, :data_types, :missing_values, :unique_values, :descriptive_statistics, :data_quality_issues,:correlation_coefficients, :outliers, :created_at, :updated_at)"),
                    {{
                        'project_id': {project_id},
                        'table_name': table_name,
                        'total_row': table_data['total_row'],
                        'total_column': table_data['total_column'],                        
                        'data_types': json.dumps(table_data['data_types']),
                        'missing_values': json.dumps(table_data['missing_values']),
                        'unique_values': json.dumps(table_data['unique_values']),
                        'descriptive_statistics': json.dumps(table_data['descriptive_stats'],  cls=DecimalEncoder),
                        'data_quality_issues': json.dumps(table_data['duplicates'],  cls=DecimalEncoder),
                        'correlation_coefficients' : json.dumps(table_data['correlation_coefficients'],  cls=DecimalEncoder),
                        'outliers': json.dumps(table_data['outliers'],cls=DecimalEncoder),
                        'created_at': current_time,
                        'updated_at': current_time
                    }}
                )

        except IntegrityError as e:
            print(f"Integrity error occurred while inserting data for table: ")

with DAG('your_{project_id}', 
         default_args=default_args, 
         schedule_interval='{schedule_interval}',
         catchup=False) as dag:
    analyze_data_task = PythonOperator(
        task_id='analyze_data_distribution',
        python_callable=analyze_data_distribution
    )
'''


    dag_file_path =  f'/media/dev/5EEA651EEA64F425/Trainning/airflow-django/dags/yout_{project_id}.py'

    with open(dag_file_path, 'w') as f:
        f.write(dag_content)
    # project.pipeline = dag_id
    # project.save()
    # messages.success(request, "DAG info saved.") 
    return dag_id