import os
import json
import sys
import pendulum
from airflow.decorators import dag, task

# Thêm đường dẫn vào sys.path để import các module Python nội bộ
sys.path.append("/opt/airflow/etl/extract")
sys.path.append("/opt/airflow/etl/load")

@dag(
    dag_id="football_etl_pipeline",
    schedule_interval="@daily",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    tags=["football", "etl"],
    description="Pipeline mẫu theo chuẩn TaskFlow API cho dự án HQTCSDL",
)
def football_etl_pipeline():

    @task(task_id="extract_fixtures")
    def run_extract_fixtures():
        # Import động để tránh lỗi import khi Airflow phân tích cú pháp DAG (DAG parsing)
        from extract_fixtures import extract_fixtures, save_fixtures
        response = extract_fixtures()
        save_fixtures(response)

    @task.short_circuit(task_id="validate_extract")
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
                response_data = data[0].get("data", {}).get("response", [])
                return len(response_data) > 0
        except Exception:
            return False

    @task(task_id="transform_fixtures")
    def run_transform_fixtures():
        import papermill as pm
        notebook_path = "/opt/airflow/etl/transform/transform_fixture_data.ipynb"
        notebook_dir = os.path.dirname(notebook_path)
        pm.execute_notebook(notebook_path, notebook_path, cwd=notebook_dir)

    @task.short_circuit(task_id="validate_transform")
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

    @task(task_id="load_fixtures")
    def run_load_fixtures():
        from load_fixture_data import main as load_main
        load_main()

    # Thiết lập luồng chạy
    run_extract_fixtures() >> check_extract_has_data() >> run_transform_fixtures() >> check_transform_has_new_data() >> run_load_fixtures()

# Khởi tạo DAG
football_etl_pipeline()

