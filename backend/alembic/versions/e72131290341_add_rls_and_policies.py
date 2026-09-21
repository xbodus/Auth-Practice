"""add RLS and policies

Revision ID: e72131290341
Revises: e6beca553122
Create Date: 2026-07-26 14:54:25.139506

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e72131290341'
down_revision: Union[str, Sequence[str], None] = 'e6beca553122'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add missing columns to users (phone, dob, company, updated_at, address, city, zipcode, country)
    op.add_column("users", sa.Column("phone", sa.String(15), nullable=False))
    op.add_column("users", sa.Column("dob", sa.Date, nullable=False))
    op.add_column("users", sa.Column("company", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False))
    op.add_column("users", sa.Column("address", sa.String(150), nullable=False))
    op.add_column("users", sa.Column("city", sa.String(50), nullable=False))
    op.add_column("users", sa.Column("zipcode", sa.String(20), nullable=False))
    op.add_column("users", sa.Column("country", sa.String(50), nullable=False))

    # Update created_at to create time on default
    op.alter_column("users", "created_at", server_default=sa.func.now(), nullable=False)

    # Enable RLS
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY")

    # Remove any duplicate policies
    op.execute("DROP POLICY IF EXISTS update_own_user ON users")
    op.execute("DROP POLICY IF EXISTS select_own_user ON users")
    op.execute("DROP FUNCTION IF EXISTS get_user_for_login(text)")
    op.execute("DROP TRIGGER IF EXISTS trg_users_updated_at ON users")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")
    op.execute("DROP TRIGGER IF EXISTS trg_users_freeze_created_at ON users")
    op.execute("DROP FUNCTION IF EXISTS prevent_created_at_update()")

    # Create table policies
    # 1. Users can only select entries associated with their user id (post-auth)
    op.execute("CREATE POLICY select_own_user ON users FOR SELECT TO playground_user_1 USING (user_id = current_setting('app.current_user_id', true)::integer)")
    op.execute("GRANT SELECT (first_name, last_name, username, email, phone, dob, company, address, city, zipcode, country, created_at, updated_at) ON users TO playground_user_1")

    # 2. Users can update everything except their user_id
    op.execute("CREATE POLICY update_own_user ON users FOR UPDATE TO playground_user_1 USING (user_id = current_setting('app.current_user_id', true)::integer) WITH CHECK (user_id = current_setting('app.current_user_id', true)::integer)")
    op.execute("GRANT UPDATE (first_name, last_name, username, password, email, phone, dob, company, address, city, zipcode, country) ON users TO playground_user_1")

    # Login lookup function — bypasses RLS narrowly, only for credential verification
    op.execute("""
               CREATE FUNCTION get_user_for_login(p_username text)
                   RETURNS TABLE
                           (
                               user_id integer,
                               password_hash text
                           ) SECURITY DEFINER
            SET search_path = public
            LANGUAGE sql
            AS $$
               SELECT user_id, password
               FROM users
               WHERE username = p_username;
               $$""")
    op.execute("GRANT EXECUTE ON FUNCTION get_user_for_login(text) TO playground_user_1")

    # Create function and trigger to update the updated_at value on UPDATE operations
    op.execute("DROP TRIGGER IF EXISTS trg_users_updated_at ON users")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")

    op.execute("""
               CREATE FUNCTION set_updated_at()
                   RETURNS trigger
                   LANGUAGE plpgsql
            AS $$
               BEGIN
                NEW.updated_at
               = now();
               RETURN NEW;
               END;
            $$
               """)

    op.execute("""
               CREATE TRIGGER trg_users_updated_at
                   BEFORE UPDATE
                   ON users
                   FOR EACH ROW
                   EXECUTE FUNCTION set_updated_at()
               """)

    # Create function and trigger to freeze created_at time to actual time of creation
    op.execute("""
               CREATE FUNCTION prevent_created_at_update()
                   RETURNS trigger
                   LANGUAGE plpgsql
            AS $$
               BEGIN
                    NEW.created_at = OLD.created_at;
                    RETURN NEW;
                END;
            $$
               """)

    op.execute("""
               CREATE TRIGGER trg_users_freeze_created_at
                   BEFORE UPDATE
                   ON users
                   FOR EACH ROW
                   EXECUTE FUNCTION prevent_created_at_update()
               """)



def downgrade() -> None:
    """Downgrade schema."""
    # Remove functions and triggers
    op.execute("DROP FUNCTION IF EXISTS get_user_for_login(text)")
    op.execute("DROP TRIGGER IF EXISTS trg_users_updated_at ON users")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")
    op.execute("DROP TRIGGER IF EXISTS trg_users_freeze_created_at ON users")
    op.execute("DROP FUNCTION IF EXISTS prevent_created_at_update()")

    # Drop added columns
    op.drop_column("users", "phone")
    op.drop_column("users", "dob")
    op.drop_column("users", "company")
    op.drop_column("users", "updated_at")
    op.drop_column("users", "address")
    op.drop_column("users", "city")
    op.drop_column("users", "zipcode")
    op.drop_column("users", "country")

    # Reverse created_at changes
    op.alter_column("users", "created_at", server_default=None, nullable=True)

    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS select_own_user ON users")
    op.execute("DROP POLICY IF EXISTS update_own_user ON users")

    # Disable RLS
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")

    # Go back to default user permissions
    op.execute("GRANT SELECT ON users TO playground_user_1")
    op.execute("GRANT UPDATE ON users TO playground_user_1")

