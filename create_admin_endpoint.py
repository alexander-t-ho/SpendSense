"""
Temporary endpoint to create admin user in production.
Add this to api/main.py temporarily, then remove after creating admin.
"""

@app.post("/api/admin/create-admin")
def create_admin_user():
    """Temporary endpoint to create admin user. Remove after use."""
    session = get_session()
    try:
        admin_email = "admin@spendsense.com"
        admin_user = session.query(User).filter(
            (User.email == admin_email) | (User.username == admin_email)
        ).first()
        
        if admin_user:
            # Update existing user
            admin_user.username = admin_email
            admin_user.password_hash = get_password_hash("123456")
            admin_user.is_admin = True
            session.commit()
            return {"message": "Admin user updated", "email": admin_email}
        else:
            # Create new admin user
            import uuid
            admin_user = User(
                id=str(uuid.uuid4()),
                name="Admin User",
                email=admin_email,
                username=admin_email,
                password_hash=get_password_hash("123456"),
                is_admin=True
            )
            session.add(admin_user)
            session.commit()
            return {"message": "Admin user created", "email": admin_email}
    finally:
        session.close()

