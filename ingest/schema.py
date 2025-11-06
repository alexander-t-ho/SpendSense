"""Database schema definitions for SpendSense."""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, 
    ForeignKey, Text, JSON, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    consent = relationship("Consent", back_populates="user", uselist=False, cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    
    def get_loan_accounts(self):
        """Get all loan accounts (mortgage and student loans) with their interest rates and due dates.
        
        Returns:
            dict: {
                'mortgage': {
                    'account': Account,
                    'interest_rate': float,
                    'next_payment_due_date': datetime
                } or None,
                'student_loan': {
                    'account': Account,
                    'interest_rate': float,
                    'next_payment_due_date': datetime
                } or None
            }
        """
        loans = {'mortgage': None, 'student_loan': None}
        
        for account in self.accounts:
            if account.type == "loan":
                if account.subtype == "mortgage":
                    loans['mortgage'] = {
                        'account': account,
                        'interest_rate': account.interest_rate,
                        'next_payment_due_date': account.next_payment_due_date,
                        'balance': abs(account.current) if account.current else 0
                    }
                elif account.subtype == "student_loan":
                    loans['student_loan'] = {
                        'account': account,
                        'interest_rate': account.interest_rate,
                        'next_payment_due_date': account.next_payment_due_date,
                        'balance': abs(account.current) if account.current else 0
                    }
        
        return loans
    
    def __repr__(self):
        return f"<User(id={self.id}, name={self.name})>"


class Account(Base):
    """Account model matching Plaid structure."""
    __tablename__ = "accounts"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    account_id = Column(String, unique=True, nullable=False)  # Plaid account ID
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # checking, savings, credit, etc.
    subtype = Column(String)  # more specific: checking, credit card, money market, HSA
    iso_currency_code = Column(String, default="USD")
    
    # Balances
    available = Column(Float)
    current = Column(Float)
    limit = Column(Float)  # For credit cards
    
    # Credit card specific fields
    amount_due = Column(Float)  # Total amount due on credit card
    minimum_payment_due = Column(Float)  # Minimum payment due
    
    # Loan-specific fields (for mortgages and student loans)
    interest_rate = Column(Float)  # Interest rate for loans
    next_payment_due_date = Column(DateTime)  # Next payment due date for loans
    
    # Metadata
    holder_category = Column(String)  # individual, business (exclude business)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    liabilities = relationship("Liability", back_populates="account", cascade="all, delete-orphan")
    
    def get_loan_info(self):
        """Get loan-specific information if this is a loan account.
        
        Returns:
            dict: {
                'interest_rate': float,
                'next_payment_due_date': datetime,
                'loan_type': str  # 'mortgage' or 'student_loan'
            } or None if not a loan account
        """
        if self.type == "loan" and self.subtype in ["mortgage", "student_loan"]:
            return {
                'interest_rate': self.interest_rate,
                'next_payment_due_date': self.next_payment_due_date,
                'loan_type': self.subtype,
                'balance': abs(self.current) if self.current else 0
            }
        return None
    
    def __repr__(self):
        return f"<Account(id={self.account_id}, type={self.type}, user_id={self.user_id})>"


class Transaction(Base):
    """Transaction model matching Plaid structure."""
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False)
    transaction_id = Column(String, unique=True, nullable=False)  # Plaid transaction ID
    date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    merchant_name = Column(String)
    merchant_entity_id = Column(String)
    payment_channel = Column(String)  # in store, online, other
    
    # Personal finance categories
    primary_category = Column(String)
    detailed_category = Column(String)
    
    # Status
    pending = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.transaction_id}, amount={self.amount}, date={self.date})>"


class Liability(Base):
    """Liability model for credit cards, mortgages, student loans."""
    __tablename__ = "liabilities"
    
    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False)
    
    # Credit card fields
    apr_type = Column(String)  # variable, fixed
    apr_percentage = Column(Float)
    minimum_payment_amount = Column(Float)
    last_payment_amount = Column(Float)
    last_payment_date = Column(DateTime)
    is_overdue = Column(Boolean, default=False)
    next_payment_due_date = Column(DateTime)
    last_statement_balance = Column(Float)
    
    # Mortgage/Student Loan fields
    interest_rate = Column(Float)
    
    # Metadata
    liability_type = Column(String)  # credit_card, mortgage, student_loan
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="liabilities")
    
    def __repr__(self):
        return f"<Liability(id={self.id}, type={self.liability_type}, account_id={self.account_id})>"


class Consent(Base):
    """User consent tracking."""
    __tablename__ = "consents"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    consented = Column(Boolean, default=False)
    consented_at = Column(DateTime)
    revoked_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="consent")
    
    def __repr__(self):
        return f"<Consent(user_id={self.user_id}, consented={self.consented})>"


class Recommendation(Base):
    """Recommendation model."""
    __tablename__ = "recommendations"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    recommendation_type = Column(String, nullable=False)  # education, partner_offer
    title = Column(String, nullable=False)
    description = Column(Text)  # Personalized recommendation text
    rationale = Column(Text, nullable=False)  # Plain-language explanation
    content_id = Column(String)  # Reference to content catalog / recommendation template ID
    persona_id = Column(String)  # Which persona triggered this
    
    # Additional fields for persona-based recommendations
    action_items = Column(JSON)  # List of action items
    expected_impact = Column(Text)  # Expected impact/benefit
    priority = Column(String)  # high, medium, low
    
    # Status
    approved = Column(Boolean, default=False)
    approved_at = Column(DateTime)
    approved_by = Column(String)  # Admin user who approved (optional)
    flagged = Column(Boolean, default=False)
    rejected = Column(Boolean, default=False)
    rejected_at = Column(DateTime)
    rejected_by = Column(String)  # Admin user who rejected (optional)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="recommendations")
    
    def __repr__(self):
        return f"<Recommendation(id={self.id}, type={self.recommendation_type}, user_id={self.user_id}, approved={self.approved})>"


class Budget(Base):
    """Budget model for user-defined and suggested budgets."""
    __tablename__ = "budgets"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    category = Column(String)  # null for overall budget, otherwise category name
    amount = Column(Float, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    is_suggested = Column(Boolean, default=False)  # True if AI-suggested, False if user-defined
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Budget(user_id={self.user_id}, category={self.category}, amount={self.amount})>"


class NetWorthHistory(Base):
    """Historical net worth snapshots for trend visualization."""
    __tablename__ = "net_worth_history"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    snapshot_date = Column(DateTime, nullable=False)
    total_assets = Column(Float, nullable=False)
    total_liabilities = Column(Float, nullable=False)
    net_worth = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<NetWorthHistory(user_id={self.user_id}, date={self.snapshot_date}, net_worth={self.net_worth})>"


class UserFeedback(Base):
    """User feedback on insights and recommendations."""
    __tablename__ = "user_feedback"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    insight_id = Column(String)  # Identifier for the insight/recommendation
    insight_type = Column(String)  # 'weekly_recap', 'budget_suggestion', 'recommendation', etc.
    feedback_type = Column(String, nullable=False)  # 'like', 'dislike'
    feedback_metadata = Column(JSON)  # Additional context (optional) - renamed from 'metadata' to avoid SQLAlchemy conflict
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<UserFeedback(user_id={self.user_id}, insight_type={self.insight_type}, feedback={self.feedback_type})>"


class CancelledSubscription(Base):
    """Track cancelled subscriptions for users."""
    __tablename__ = "cancelled_subscriptions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    merchant_name = Column(String, nullable=False)
    cancelled_at = Column(DateTime, default=func.now(), nullable=False)
    cancelled_by = Column(String)  # Optional: track if cancelled via recommendation
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Unique constraint: user can only cancel each merchant once
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )
    
    def __repr__(self):
        return f"<CancelledSubscription(user_id={self.user_id}, merchant_name={self.merchant_name}, cancelled_at={self.cancelled_at})>"


class ApprovedActionPlan(Base):
    """Track user-approved action plans for recommendations."""
    __tablename__ = "approved_action_plans"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    recommendation_id = Column(String, ForeignKey("recommendations.id"), nullable=False, index=True)
    approved_at = Column(DateTime, default=func.now(), nullable=False)
    status = Column(String, default='active')  # active, completed, cancelled
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    recommendation = relationship("Recommendation")
    
    def __repr__(self):
        return f"<ApprovedActionPlan(user_id={self.user_id}, recommendation_id={self.recommendation_id}, status={self.status})>"


# Database setup
def get_engine(db_path: str = "data/spendsense.db"):
    """Get SQLAlchemy engine."""
    return create_engine(f"sqlite:///{db_path}", echo=False)


def get_session(db_path: str = "data/spendsense.db"):
    """Get database session."""
    engine = get_engine(db_path)
    Session = sessionmaker(bind=engine)
    return Session()


def init_db(db_path: str = "data/spendsense.db"):
    """Initialize database with schema."""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine

