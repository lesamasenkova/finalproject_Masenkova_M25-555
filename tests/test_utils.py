"""
Тесты для модуля core.utils.
"""
import pytest
from valutatrade_hub.core.utils import validate_amount, validate_currency_code
from valutatrade_hub.core.exceptions import InvalidAmountError


class TestValidation:
    """Тесты для функций валидации."""
    
    def test_validate_amount_positive(self):
        """Тест валидации положительной суммы."""
        amount = validate_amount(100.0)
        assert amount == 100.0
    
    def test_validate_amount_zero_not_allowed(self):
        """Тест валидации нулевой суммы (не разрешено)."""
        with pytest.raises(InvalidAmountError):
            validate_amount(0.0, allow_zero=False)
    
    def test_validate_amount_zero_allowed(self):
        """Тест валидации нулевой суммы (разрешено)."""
        amount = validate_amount(0.0, allow_zero=True)
        assert amount == 0.0
    
    def test_validate_amount_negative(self):
        """Тест валидации отрицательной суммы."""
        with pytest.raises(InvalidAmountError):
            validate_amount(-50.0)
    
    def test_validate_currency_code_valid(self):
        """Тест валидации правильного кода валюты."""
        code = validate_currency_code("USD")
        assert code == "USD"
    
    def test_validate_currency_code_lowercase(self):
        """Тест валидации кода валюты в нижнем регистре."""
        code = validate_currency_code("usd")
        assert code == "USD"
    
    def test_validate_currency_code_empty(self):
        """Тест валидации пустого кода валюты."""
        with pytest.raises(ValueError):
            validate_currency_code("")
