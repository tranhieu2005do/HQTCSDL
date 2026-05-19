import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator

# Tự động hóa quá trình chạy ETL
with DAG(
    dag_id="football_etl_pipeline",
    schedule_interval="@daily",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    tags=["football", "etl"],
    description="Pipeline mẫu cho dự án hệ quản trị cơ sở dữ liệu (Extract -> Transform -> Load)",
) as dag:

    # 1. Extract Task
    # Gọi file Python trong thư mục etl/extract
    # Cần set PYTHONPATH để Python hiểu được module api_client, config...
    extract_task = BashOperator(
        task_id="extract_fixtures",
        bash_command="export PYTHONPATH=/opt/airflow/etl/extract:$PYTHONPATH && python /opt/airflow/etl/extract/extract_fixtures.py",
    )

    # 2. Transform Task
    # Chạy file Jupyter Notebook bằng lệnh nbconvert
    transform_task = BashOperator(
        task_id="transform_fixtures",
        bash_command="jupyter nbconvert --execute --to notebook --inplace /opt/airflow/etl/transform/transform_fixture_data.ipynb",
    )

    # 3. Load Task
    # Đẩy dữ liệu đã xử lý vào database
    load_task = BashOperator(
        task_id="load_fixtures",
        bash_command="export PYTHONPATH=/opt/airflow/etl/load:$PYTHONPATH && python /opt/airflow/etl/load/load_fixture_data.py",
    )

    # Thiết lập chuỗi dependency (Luồng thực thi)
    extract_task >> transform_task >> load_task
