from pathlib import Path
import subprocess
import sys

import dagster as dg


PROJECT_ROOT = Path(__file__).resolve().parent
DBT_PROJECT_DIR = PROJECT_ROOT / "medical_warehouse"


def run_command(context, command, cwd=PROJECT_ROOT):
    """
    Helper function to run terminal commands inside Dagster.
    If a command fails, Dagster marks the op as failed.
    """
    context.log.info(f"Running command: {command}")
    context.log.info(f"Working directory: {cwd}")

    result = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        text=True,
        capture_output=True,
    )

    if result.stdout:
        context.log.info(result.stdout)

    if result.stderr:
        context.log.warning(result.stderr)

    if result.returncode != 0:
        raise Exception(f"Command failed: {command}")

    return result.stdout


@dg.failure_hook
def pipeline_failure_alert(context):
    """
    Local failure alert.
    In a real production setup, this could send Slack/email alerts.
    For this assignment, it records failure details in Dagster logs.
    """
    context.log.error(
        f"Pipeline failure alert: op '{context.op.name}' failed. "
        "Check Dagster logs for details."
    )


@dg.op
def scrape_telegram_data(context):
    """
    Runs the Telegram scraper and saves raw JSON/images into the data lake.
    """
    run_command(context, f"{sys.executable} src/scraper.py")
    return "scraping_complete"


@dg.op
def load_raw_to_postgres(context, scrape_status: str):
    """
    Loads raw Telegram JSON files into PostgreSQL raw.telegram_messages.
    """
    context.log.info(f"Previous step status: {scrape_status}")
    run_command(context, f"{sys.executable} src/load_raw_to_postgres.py")
    return "raw_load_complete"


@dg.op
def run_yolo_enrichment(context, load_status: str):
    """
    Runs YOLO object detection and loads detection results into PostgreSQL.
    """
    context.log.info(f"Previous step status: {load_status}")
    run_command(context, f"{sys.executable} src/yolo_detect.py")
    run_command(context, f"{sys.executable} src/load_yolo_to_postgres.py")
    return "yolo_enrichment_complete"


@dg.op
def run_dbt_transformations(context, yolo_status: str):
    """
    Runs dbt models and tests to build the warehouse marts.
    """
    context.log.info(f"Previous step status: {yolo_status}")

    run_command(
        context,
        "dbt run --profiles-dir .",
        cwd=DBT_PROJECT_DIR,
    )

    run_command(
        context,
        "dbt test --profiles-dir .",
        cwd=DBT_PROJECT_DIR,
    )

    return "dbt_transformations_complete"


@dg.job(hooks={pipeline_failure_alert})
def medical_telegram_pipeline():
    """
    Full pipeline:
    scrape Telegram data → load raw data → run YOLO enrichment → run dbt transformations.
    """
    scrape_status = scrape_telegram_data()
    load_status = load_raw_to_postgres(scrape_status)
    yolo_status = run_yolo_enrichment(load_status)
    run_dbt_transformations(yolo_status)


daily_medical_telegram_schedule = dg.ScheduleDefinition(
    job=medical_telegram_pipeline,
    cron_schedule="0 6 * * *",
    name="daily_medical_telegram_schedule",
    description="Runs the full medical Telegram pipeline every day at 6:00 AM.",
)


defs = dg.Definitions(
    jobs=[medical_telegram_pipeline],
    schedules=[daily_medical_telegram_schedule],
)