"""
Тесты для модулей core.models.
Тестируем User, Wallet и Portfolio.
"""
import pytest
from valutatrade_hub.core.models import User, Wallet, Portfolio
from valutatrade_hub.core.exceptions import (
    InvalidUsernameError,
    InvalidPasswordLengthError,
    InvalidAmountError,
)


class TestUser:
    """Тесты для класса User."""
    
    def test_create_new_user(self):
        """Тест создания нового пользователя."""
        user = User.create_new("testuser", "password123")
        assert user.username == "testuser"
        assert user.user_id > 0
        assert user.verify_password("password123")
        assert not user.verify_password("wrongpassword")
    
    def test_user_password_validation(self):
        """Тест валидации пароля при создании."""
        with pytest.raises(InvalidPasswordLengthError):
            User.create_new("testuser", "short")
    
    def test_user_username_validation(self):
        """Тест валидации имени пользователя."""
        with pytest.raises(InvalidUsernameError):
            User.create_new("", "password123")
    
    def test_change_password(self):
        """Тест смены пароля."""
        user = User.create_new("testuser", "password123")
        user.change_password("newpassword456")
        assert user.verify_password("newpassword456")
        assert not user.verify_password("password123")
    
    def test_user_to_dict(self):
        """Тест сериализации пользователя."""
        user = User.create_new("testuser", "password123")
        user_dict = user.to_dict()
        assert user_dict["username"] == "testuser"
        assert "user_id" in user_dict
        assert "password_hash" in user_dict
    
    def test_user_from_dict(self):
        """Тест десериализации пользователя."""
        user1 = User.create_new("testuser", "password123")
        user_dict = user1.to_dict()
        user2 = User.from_dict(user_dict)
        assert user1.username == user2.username
        assert user1.user_id == user2.user_id
        assert user2.verify_password("password123")


class TestWallet:
    """Тесты для класса Wallet."""
    
    def test_create_wallet(self):
        """Тест создания кошелька."""
        wallet = Wallet("USD", 100.0)
        assert wallet.currency_code == "USD"
        assert wallet.balance == 100.0
    
    def test_deposit(self):
        """Тест пополнения баланса."""
        wallet = Wallet("USD", 100.0)
        wallet.deposit(50.0)
        assert wallet.balance == 150.0
    
    def test_withdraw(self):
        """Тест снятия средств."""
        wallet = Wallet("USD", 100.0)
        wallet.withdraw(30.0)
        assert wallet.balance == 70.0
    
    def test_withdraw_insufficient_balance(self):
        """Тест снятия при недостаточном балансе."""
        wallet = Wallet("USD", 50.0)
        with pytest.raises(InvalidAmountError):
            wallet.withdraw(100.0)
    
    def test_wallet_to_dict(self):
        """Тест сериализации кошелька."""
        wallet = Wallet("USD", 100.0)
        wallet_dict = wallet.to_dict()
        assert wallet_dict["currency_code"] == "USD"
        assert wallet_dict["balance"] == 100.0
    
    def test_wallet_from_dict(self):
        """Тест десериализации кошелька."""
        wallet1 = Wallet("EUR", 250.5)
        wallet_dict = wallet1.to_dict()
        wallet2 = Wallet.from_dict(wallet_dict)
        assert wallet1.currency_code == wallet2.currency_code
        assert wallet1.balance == wallet2.balance


class TestPortfolio:
    """Тесты для класса Portfolio."""
    
    def test_create_portfolio(self):
        """Тест создания портфеля."""
        portfolio = Portfolio(user_id=1)
        assert portfolio.user_id == 1
        assert len(portfolio.wallets) == 0
    
    def test_add_currency(self):
        """Тест добавления валюты в портфель."""
        portfolio = Portfolio(user_id=1)
        wallet = portfolio.add_currency("USD", 100.0)
        assert "USD" in portfolio.wallets
        assert wallet.balance == 100.0
    
    def test_get_wallet(self):
        """Тест получения кошелька."""
        portfolio = Portfolio(user_id=1)
        portfolio.add_currency("USD", 100.0)
        wallet = portfolio.get_wallet("USD")
        assert wallet.currency_code == "USD"
        assert wallet.balance == 100.0
    
    def test_get_wallet_not_found(self):
        """Тест получения несуществующего кошелька."""
        portfolio = Portfolio(user_id=1)
        with pytest.raises(ValueError):
            portfolio.get_wallet("USD")
    
    def test_portfolio_to_dict(self):
        """Тест сериализации портфеля."""
        portfolio = Portfolio(user_id=1)
        portfolio.add_currency("USD", 100.0)
        portfolio.add_currency("EUR", 50.0)
        portfolio_dict = portfolio.to_dict()
        assert portfolio_dict["user_id"] == 1
        assert len(portfolio_dict["wallets"]) == 2
    
    def test_portfolio_from_dict(self):
        """Тест десериализации портфеля."""
        portfolio1 = Portfolio(user_id=1)
        portfolio1.add_currency("USD", 100.0)
        portfolio1.add_currency("EUR", 50.0)
        portfolio_dict = portfolio1.to_dict()
        portfolio2 = Portfolio.from_dict(portfolio_dict)
        assert portfolio1.user_id == portfolio2.user_id
        assert len(portfolio1.wallets) == len(portfolio2.wallets)
