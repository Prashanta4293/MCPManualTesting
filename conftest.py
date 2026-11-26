
"""Project-wide extensions; existing legacy fixtures remain in tests/conftest.py."""

pytest_plugins = ['utilities.visitor_fixtures']

import subprocess
from pathlib import Path

import allure
import pytest


@pytest.fixture(autouse=True)
def allure_failure_screenshots(request):
    """
    Capture actual browser screenshots when a test fails.
    Screenshots are attached to Allure without masking.
    """

    registered_pages = []
    cleanup_callbacks = []

    def register_page(page, cleanup=None):
        """Register standard or manually created Playwright pages."""

        if page is not None and page not in registered_pages:
            registered_pages.append(page)

        if cleanup is not None:
            cleanup_callbacks.append(cleanup)

    # Automatically register the standard Playwright page fixture.
    if 'page' in request.fixturenames:
        try:
            page = request.getfixturevalue('page')
            register_page(page)
        except Exception:
            pass

    yield register_page

    try:
        report = getattr(request.node, 'rep_call', None)

        if report is not None and report.failed:

            if not registered_pages:
                print(
                    f'\nNo Playwright page registered for '
                    f'{request.node.name}.'
                )

            for index, page in enumerate(registered_pages, start=1):
                try:
                    if page.is_closed():
                        continue

                    screenshot = page.screenshot(
                        full_page=True,
                        animations='disabled'
                    )

                    allure.attach(
                        screenshot,
                        name=f'{request.node.name}-failure-{index}',
                        attachment_type=allure.attachment_type.PNG
                    )

                    print(
                        f'\nFailure screenshot attached: '
                        f'{request.node.name}'
                    )

                except Exception as exc:
                    print(
                        f'\nScreenshot capture failed for '
                        f'{request.node.name}: '
                        f'{type(exc).__name__}'
                    )

    finally:
        # Clean up manually registered browser resources.
        for cleanup in reversed(cleanup_callbacks):
            try:
                cleanup()
            except Exception:
                pass


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Store test reports for fixture teardown."""

    outcome = yield
    report = outcome.get_result()

    setattr(item, f'rep_{report.when}', report)


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """Generate and automatically open Allure report after test execution."""

    project_root = Path(__file__).resolve().parent
    results_dir = project_root / 'allure-results'
    report_dir = project_root / 'allure-report'

    if not results_dir.exists() or not any(results_dir.iterdir()):
        print('\nAllure results not found. Report generation skipped.')
        return

    allure_cli = r'C:\Tools\allure-2.46.1\bin\allure.bat'

    try:
        subprocess.run(
            [
                allure_cli,
                'generate',
                str(results_dir),
                '--clean',
                '-o',
                str(report_dir),
            ],
            cwd=str(project_root),
            check=True,
        )

        subprocess.Popen(
            [
                allure_cli,
                'open',
                str(report_dir),
            ],
            cwd=str(project_root),
        )

        print('\nAllure report generated and opened successfully.')

    except FileNotFoundError:
        print('\nAllure CLI not found. Check installation and PATH.')

    except subprocess.CalledProcessError:
        print('\nAllure report generation failed.')
