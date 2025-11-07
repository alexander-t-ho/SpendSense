"""Consent management for SpendSense."""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ingest.schema import Consent, User
import uuid


class ConsentManager:
    """Manage user consent for data processing and recommendations."""
    
    def __init__(self, db_session: Session):
        """Initialize consent manager.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def get_consent(self, user_id: str) -> Optional[Consent]:
        """Get consent status for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Consent record if exists, None otherwise
        """
        return self.db.query(Consent).filter(Consent.user_id == user_id).first()
    
    def has_consent(self, user_id: str) -> bool:
        """Check if user has consented to data processing.
        
        Args:
            user_id: User ID
        
        Returns:
            True if user has consented, False otherwise
        """
        consent = self.get_consent(user_id)
        return consent is not None and consent.consented is True
    
    def grant_consent(self, user_id: str) -> Consent:
        """Grant consent for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Created or updated Consent record
        
        Raises:
            ValueError: If user doesn't exist
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        consent = self.get_consent(user_id)
        
        if consent:
            # Update existing consent
            consent.consented = True
            consent.consented_at = datetime.now()
            consent.revoked_at = None
            consent.updated_at = datetime.now()
        else:
            # Create new consent
            consent = Consent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                consented=True,
                consented_at=datetime.now(),
                revoked_at=None
            )
            self.db.add(consent)
        
        self.db.commit()
        return consent
    
    def revoke_consent(self, user_id: str) -> Consent:
        """Revoke consent for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Updated Consent record
        
        Raises:
            ValueError: If user doesn't exist
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        consent = self.get_consent(user_id)
        
        if consent:
            consent.consented = False
            consent.revoked_at = datetime.now()
            consent.updated_at = datetime.now()
        else:
            # Create consent record with revoked status
            consent = Consent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                consented=False,
                consented_at=None,
                revoked_at=datetime.now()
            )
            self.db.add(consent)
        
        self.db.commit()
        return consent
    
    def require_consent(self, user_id: str) -> bool:
        """Check if user has consented, raise exception if not.
        
        Args:
            user_id: User ID
        
        Returns:
            True if consented
        
        Raises:
            PermissionError: If user has not consented
        """
        if not self.has_consent(user_id):
            raise PermissionError(
                f"User {user_id} has not consented to data processing. "
                "Recommendations cannot be generated without consent."
            )
        return True




