"""
Тесты для модуля service.
"""
import pytest
from valutatrade_hub.service import UserService, PortfolioService, ConversionService
from valutatrade_hub.core.exceptions import AuthenticationError
from valutatrade_hub.infra.database import reset_database


@pytest.fixture(autouse=True)
def reset_db():
    """Сбрасывает БД перед каждым тестом."""
    reset_database()
    yield
    reset_database()


class TestUserService:
    """Тесты для UserService."""
    
    def test_register_user(self):
        """Тест регистрации пользователя."""
        service = UserService()
        user = service.register_user("testuser", "password123")
        assert user.username == "testuser"
        assert user.user_id > 0
    
    def test_register_duplicate_user(self):
        """Тест регистрации дублирующегося пользователя."""
        service = UserService()
        service.register_user("testuser", "password123")
        with pytest.raises(ValueError):
            service.register_user("testuser", "password456")
    
    def test_authenticate_user(self):
        """Тест аутентификации пользователя."""
        service = UserService()
        service.register_user("testuser", "password123")
        user = service.authenticate("testuser", "password123")
        assert user.username == "testuser"
    
    def test_authenticate_wrong_password(self):
        """Тест аутентификации с неверным паролем."""
        service = UserService()
        service.register_user("testuser", "password123")
        with pytest.raises(AuthenticationError):
            service.authenticate("testuser", "wrongpassword")
    
    def test_authenticate_nonexistent_user(self):
        """Тест аутентификации несуществующего пользователя."""
        service = UserService()
        with pytest.raises(AuthenticationError):
            service.authenticate("nonexistent", "password123")
    
    def test_change_password(self):
        """Тест смены пароля."""
        service = UserService()
        service.register_user("testuser", "password123")
        service.change_password("testuser", "password123", "newpassword456")
        user = service.authenticate("testuser", "newpassword456")
        assert user.username == "testuser"
    
    def test_get_user_info(self):
        """Тест получения информации о пользователе."""
        service = UserService()
        service.register_user("testuser", "password123")
        info = service.get_user_info("testuser")
        assert info["username"] == "testuser"
        assert "user_id" in info


class TestPortfolioService:
    """Тесты для PortfolioService."""
    
    @pytest.fixture(autouse=True)
    def setup_user(self):
        """Подготовка пользователя для тестов."""
        user_service = UserService()
        user = user_service.register_user("testuser", "password123")
        return user
    
    def test_add_currency_to_portfolio(self, setup_user):
        """Тест добавления валюты в портфель."""
        service = PortfolioService()
        wallet = service.add_currency_to_portfolio("testuser", "USD", 100.0)
        assert wallet.currency_code == "USD"
        assert wallet.balance == 100.0
    
    def test_deposit(self, setup_user):
        """Тест пополнения баланса."""
        service = PortfolioService()
        service.add_currency_to_portfolio("testuser", "USD", 100.0)
        new_balance = service.deposit("testuser", "USD", 50.0)
        assert new_balance == 150.0
    
    def test_withdraw(self, setup_user):
        """Тест снятия средств."""
        service = PortfolioService()
        service.add_currency_to_portfolio("testuser", "USD", 100.0)
        new_balance = service.withdraw("testuser", "USD", 30.0)
        assert new_balance == 70.0
    
    def test_get_wallet_info(self, setup_user):
        """Тест получения информации о кошельке."""
        service = PortfolioService()
        service.add_currency_to_portfolio("testuser", "USD", 100.0)
        info = service.get_wallet_info("testuser", "USD")
        assert info["currency"] == "USD"
        assert info["balance"] == 100.0
    
    def test_get_portfolio_summary(self, setup_user):
        """Тест получения обзора портфеля."""
        service = PortfolioService()
        service.add_currency_to_portfolio("testuser", "USD", 100.0)
        service.add_currency_to_portfolio("testuser", "EUR", 50.0)
        summary = service.get_portfolio_summary("testuser")
        assert summary["wallet_count"] == 2
        assert len(summary["wallets"]) == 2


class TestConversionService:
    """Тесты для ConversionService."""
    
    def test_get_conversion_rate(self):
        """Тест получения курса обмена."""
        service = ConversionService()
        rate = service.get_conversion_rate("USD", "EUR")
        assert isinstance(rate, float)
        assert rate > 0
    
    def test_get_conversion_rate_same_currency(self):
        """Тест получения курса для одной валюты."""
        service = ConversionService()
        rate = service.get_conversion_rate("USD", "USD")
        assert rate == 1.0
    
    def test_calculate_conversion(self):
        """Тест расчета конвертации."""
        service = ConversionService()
        result = service.calculate_conversion(100.0, "USD", "EUR")
        assert result["amount"] == 100.0
        assert result["from_currency"] == "USD"
        assert result["to_currency"] == "EUR"
        assert result["result"] > 0
        assert result["rate"] > 0
    
    def test_get_all_rates(self):
        """Тест получения всех курсов."""
        service = ConversionService()
        rates = service.get_all_rates()
        assert isinstance(rates, dict)
        assert len(rates) > 0
