
"""Project-wide extensions; existing legacy fixtures remain in tests/conftest.py."""

pytest_plugins = ['utilities.visitor_fixtures']

import subprocess
import pytest
from pathlib import Path


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """Generate and automatically open Allure report after test execution."""

    project_root = Path(__file__).resolve().parent
    results_dir = project_root / "allure-results"
    report_dir = project_root / "allure-report"

    # Check whether Allure results are available
    if not results_dir.exists() or not any(results_dir.iterdir()):
        print("\nAllure results not found. Report generation skipped.")
        return

    allure_cli = r"C:\Tools\allure-2.46.1\bin\allure.bat"

    try:
        # Generate Allure HTML report
        subprocess.run(
            [
                allure_cli,
                "generate",
                str(results_dir),
                "--clean",
                "-o",
                str(report_dir),
            ],
            cwd=str(project_root),
            check=True,
        )

        # Automatically open the generated report
        subprocess.Popen(
            [
                allure_cli,
                "open",
                str(report_dir),
            ],
            cwd=str(project_root),
        )

        print("\nAllure report generated and opened successfully.")

    except FileNotFoundError:
        print("\nAllure CLI not found. Check installation and PATH.")

    except subprocess.CalledProcessError:
        print("\nAllure report generation failed.")
