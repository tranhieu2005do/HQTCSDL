import os
import json
import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import ShortCircuitOperator

def check_extract_has_data():
    """Kiểm tra xem quá trình extract có trích xuất được dữ liệu hay không."""
    file_path = "/opt/airflow/etl/output/fixtures.json"
    if not os.path.exists(file_path):
        return False
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not data or len(data) == 0:
                return False
            # Data trả về từ api-football thường nằm trong trường 'response' của payload
            response_data = data[0].get("data", {}).get("response", [])
            return len(response_data) > 0
    except Exception:
        return False

def check_transform_has_new_data():
    """Kiểm tra xem quá trình transform có tạo ra dữ liệu hợp lệ để load không."""
    file_path = "/opt/airflow/database/fixtures.json"
    if not os.path.exists(file_path):
        return False
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return len(data) > 0
    except Exception:
        return False

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

    validate_extract_task = ShortCircuitOperator(
        task_id="validate_extract",
        python_callable=check_extract_has_data,
    )

    # 2. Transform Task
    # Chạy file Jupyter Notebook bằng lệnh nbconvert
    transform_task = BashOperator(
        task_id="transform_fixtures",
        bash_command="jupyter nbconvert --execute --to notebook --inplace /opt/airflow/etl/transform/transform_fixture_data.ipynb",
    )

    validate_transform_task = ShortCircuitOperator(
        task_id="validate_transform",
        python_callable=check_transform_has_new_data,
    )

    # 3. Load Task
    # Đẩy dữ liệu đã xử lý vào database
    load_task = BashOperator(
        task_id="load_fixtures",
        bash_command="export PYTHONPATH=/opt/airflow/etl/load:$PYTHONPATH && python /opt/airflow/etl/load/load_fixture_data.py",
    )

    # Thiết lập chuỗi dependency (Luồng thực thi có kiểm tra điều kiện)
    extract_task >> validate_extract_task >> transform_task >> validate_transform_task >> load_task
