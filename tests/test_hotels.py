import allure
import pytest
from pages.data import HOTEL_CASE, case_name
from pages.hotels_page import HotelsPage

@pytest.mark.regression
@pytest.mark.parametrize('case', [HOTEL_CASE], ids=case_name)
def test_hotels(case, page, audit):
    hotels = HotelsPage(page,audit)
    with allure.step('Open Hotels through the home header'):
        hotels.navigate()
    with allure.step('Expand the saved listing and verify confirmed source records'):
        hotels.verify_matches()
    audit.finish()
