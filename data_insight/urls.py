from django.urls import path
from .views import *

urlpatterns = [
    path('register', register_view, name='register'),
    path('login', login_view, name='login'),
    path('logout_form', logout_form, name='logout'),
    path('projects', projects, name='projects'),
    path('create_project', create_project, name='create_project'),
    path('project_detail/<str:project_id>', project_details, name='project_detail'),
    path('trigger_dag/<str:project_id>', trigger_dag, name='trigger_dag'),
    path('manage_pipeline/<str:project_id>', manage_pipeline, name='manage_pipeline'),
    path('pause_dag/<str:dag_id>', pause_dag, name='pause_dag'),
    path('projects/<str:project_id>/tables/<str:table_name>/', table_details, name='table_details'),
    path('create_dag_form/<str:project_id>', create_dag_form, name='create_dag_form'),
    path('dag_run_logs/<str:dag_id>/<str:dag_run_id>/', dag_run_logs, name='dag_run_logs'),
    path('update_project/<int:project_id>', update_project, name='update_project'),
    path('delete_project/<int:project_id>', delete_project, name='delete_project'),

    # path('generate_dynamic_dag/',generate_dynamic_dag,name="generate_dynamic_dag"),
    # path('project/<str:project_id>', project_details, name='project_details'),
    # path('set_pipeline/<str:project_id>', set_pipeline, name='set_pipeline'),
    # # path('get_tables/<str:project_id>', get_tables, name='get_tables'),
    # path('establish_connection/<str:project_id>',establish_connection,name="establish_connection"),
    # path('tables/', tables_list, name='tables_list'),
    # path('table/<int:table_id>/', table_rows, name='table_rows'),
    # path('project/<int:project_id>/', project_detail, name='project_detail'),
    # path('project/<int:project_id>/generate_and_trigger_dag/', generate_and_trigger_dag, name='generate_and_trigger_dag'),
    # path('generate_dynamic_dag/<int:project_id>/', generate_dynamic_dag, name='generate_dynamic_dag'),
    path('', home, name='home'),
]
