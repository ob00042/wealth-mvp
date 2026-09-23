from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, engine
from app.models.advisor import Advisor
from app.models.client import Client
from app.models.bank import Bank
from app.models.account import Account
from app.models.position import Position
from app.utils.auth import hash_password
from app.models.history import Transaction, AccountValuation
from seed_history import seed_demo_history


def seed_additional_data():
    db = SessionLocal()
    
    try:
        # Delete existing data in reverse order of dependencies
        print("Cleaning up existing data...")
        
        db.query(Transaction).delete()
        db.query(AccountValuation).delete()

        # Delete positions first (they depend on accounts)
        db.query(Position).delete()
        
        # Delete accounts (they depend on banks)
        db.query(Account).delete()
        
        # Delete banks (they depend on clients)
        db.query(Bank).delete()
        
        # Delete clients (they depend on advisors)
        db.query(Client).delete()
        
        # Delete advisors
        db.query(Advisor).delete()
        
        db.commit()
        print("✅ Cleaned up existing data")
        
        # Create a sample advisor
        advisor = Advisor(
            first_name="John",
            last_name="Smith",
            email="john.smith@example.com",
            hashed_password=hash_password("password")
        )
        db.add(advisor)
        db.flush()
        
        print(f"Created advisor: {advisor.first_name} {advisor.last_name}")
        
        # Create Jane Doe
        jane_doe = Client(
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@example.com",
            hashed_password=hash_password("JaneDemo123!"),
            advisor_id=advisor.id
        )
        db.add(jane_doe)
        db.flush()
        
        # Create Jane's first bank
        jane_bank = Bank(
            name="Bank of America",
            client_id=jane_doe.id
        )
        db.add(jane_bank)
        db.flush()
        
        # Create Jane's first account
        jane_account1 = Account(
            name="Jane's Primary Checking",
            account_type="Checking",
            currency="USD",
            balance=Decimal("25000.00"),
            bank_id=jane_bank.id
        )
        db.add(jane_account1)
        db.flush()
        
        print(f"Created Jane Doe with initial account")
        
        # Add another account for Jane Doe in her existing bank
        new_account = Account(
            name="Jane's Investment Account",
            account_type="Investment",
            currency="USD",
            balance=Decimal("45000.00"),
            bank_id=jane_bank.id
        )
        db.add(new_account)
        db.flush()
        
        # Add some positions to the new account
        position1 = Position(
            security_name="Apple Inc.",
            ticker="AAPL",
            asset_type="Stock",
            quantity=Decimal("50"),
            market_value=Decimal("9500.00"),
            currency="USD",
            account_id=new_account.id
        )
        position2 = Position(
            security_name="Microsoft Corporation",
            ticker="MSFT",
            asset_type="Stock",
            quantity=Decimal("30"),
            market_value=Decimal("12000.00"),
            currency="USD",
            account_id=new_account.id
        )
        db.add(position1)
        db.add(position2)
        
        print(f"Added investment account for Jane Doe: {new_account.name}")
        
        # Create 2 more banks for Jane Doe
        jane_bank2 = Bank(
            name="Chase Bank",
            client_id=jane_doe.id
        )
        db.add(jane_bank2)
        db.flush()
        
        jane_account2 = Account(
            name="Jane's Chase Savings",
            account_type="Savings",
            currency="USD",
            balance=Decimal("35000.00"),
            bank_id=jane_bank2.id
        )
        db.add(jane_account2)
        db.flush()
        
        print(f"Added bank for Jane Doe: {jane_bank2.name}")
        
        jane_bank3 = Bank(
            name="Wells Fargo",
            client_id=jane_doe.id
        )
        db.add(jane_bank3)
        db.flush()
        
        jane_account3 = Account(
            name="Jane's Wells Fargo Checking",
            account_type="Checking",
            currency="USD",
            balance=Decimal("15000.00"),
            bank_id=jane_bank3.id
        )
        db.add(jane_account3)
        db.flush()
        
        print(f"Added bank for Jane Doe: {jane_bank3.name}")
        
        # Create Mister Agapitos
        mister_agapitos = Client(
            first_name="Mister",
            last_name="Agapitos",
            email="mister.agapitos@example.com",
            hashed_password=hash_password("AgapitosDemo123!"),
            advisor_id=advisor.id
        )
        db.add(mister_agapitos)
        db.flush()
        
        # Create first bank for Mister Agapitos
        agapitos_bank = Bank(
            name="National Bank of Greece",
            client_id=mister_agapitos.id
        )
        db.add(agapitos_bank)
        db.flush()
        
        # Create second bank for Mister Agapitos
        agapitos_bank2 = Bank(
            name="Piraeus Bank",
            client_id=mister_agapitos.id
        )
        db.add(agapitos_bank2)
        db.flush()
        
        # Create 4 accounts for Mister Agapitos (3 in first bank, 1 in second bank)
        accounts_data = [
            {
                "name": "Agapitos Checking Account",
                "account_type": "Checking",
                "currency": "EUR",
                "balance": Decimal("25000.00"),
                "bank_id": agapitos_bank.id
            },
            {
                "name": "Agapitos Savings Account",
                "account_type": "Savings",
                "currency": "EUR",
                "balance": Decimal("75000.00"),
                "bank_id": agapitos_bank.id
            },
            {
                "name": "Agapitos Investment Portfolio",
                "account_type": "Investment",
                "currency": "EUR",
                "balance": Decimal("120000.00"),
                "bank_id": agapitos_bank.id
            },
            {
                "name": "Agapitos Piraeus Bank Account",
                "account_type": "Checking",
                "currency": "EUR",
                "balance": Decimal("40000.00"),
                "bank_id": agapitos_bank2.id
            }
        ]
        
        for acc_data in accounts_data:
            account = Account(
                name=acc_data["name"],
                account_type=acc_data["account_type"],
                currency=acc_data["currency"],
                balance=acc_data["balance"],
                bank_id=acc_data["bank_id"]
            )
            db.add(account)
            db.flush()
            
            # Add positions to the investment account
            if acc_data["account_type"] == "Investment":
                positions = [
                    Position(
                        security_name="Coca-Cola HBC",
                        ticker="EEE",
                        asset_type="Stock",
                        quantity=Decimal("100"),
                        market_value=Decimal("2500.00"),
                        currency="EUR",
                        account_id=account.id
                    ),
                    Position(
                        security_name="Alpha Bank",
                        ticker="ALPHA",
                        asset_type="Stock",
                        quantity=Decimal("200"),
                        market_value=Decimal("3200.00"),
                        currency="EUR",
                        account_id=account.id
                    ),
                    Position(
                        security_name="Greek Government Bonds",
                        ticker=None,
                        asset_type="Bond",
                        quantity=Decimal("50"),
                        market_value=Decimal("50000.00"),
                        currency="EUR",
                        account_id=account.id
                    )
                ]
                for pos in positions:
                    db.add(pos)
            
            print(f"Added account for Mister Agapitos: {account.name}")
        
        db.flush()
        seed_demo_history(db)
        db.commit()
        print("\n✅ Successfully seeded data!")
        print(f"- Created advisor John Smith")
        print(f"- Created Jane Doe with 4 accounts across 3 banks")
        print(f"- Created Mister Agapitos with 4 accounts across 2 banks")
        print(f"\nLogin credentials:")
        print(f"Email: john.smith@example.com")
        print(f"Password: password")
        print("Client Jane Doe: jane.doe@example.com / JaneDemo123!")
        print("Client Mister Agapitos: mister.agapitos@example.com / AgapitosDemo123!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding data: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_additional_data()
