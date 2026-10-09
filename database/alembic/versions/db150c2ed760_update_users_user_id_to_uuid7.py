"""Update users user_id to uuid7

Revision ID: db150c2ed760
Revises: 9676992bcb6d
Create Date: 2026-10-08 20:02:08.244531

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db150c2ed760'
down_revision: Union[str, Sequence[str], None] = '9676992bcb6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Convert users.user_id and all referencing FKs to UUID."""
    # 1. Drop foreign key constraints referencing users.user_id
    op.drop_constraint("account_memberships_user_id_fkey", "account_memberships", type_="foreignkey")
    op.drop_constraint("email_verifications_user_id_fkey", "email_verifications", type_="foreignkey")
    op.drop_constraint("password_resets_user_id_fkey", "password_resets", type_="foreignkey")

    # 2. Drop all RLS policies referencing user_id before altering column type
    op.execute("DROP POLICY IF EXISTS select_own_user ON users")
    op.execute("DROP POLICY IF EXISTS update_own_user ON users")
    op.execute("DROP POLICY IF EXISTS select_own_account ON accounts")
    op.execute("DROP POLICY IF EXISTS update_own_account ON accounts")
    op.execute("DROP POLICY IF EXISTS select_own_account_memberships ON account_memberships")
    op.execute("DROP POLICY IF EXISTS admin_manage_account_members ON account_memberships")
    op.execute("DROP POLICY IF EXISTS admin_add_account_members ON account_memberships")
    op.execute("DROP POLICY IF EXISTS admin_remove_account_members ON account_memberships")
    op.execute("DROP POLICY IF EXISTS select_own_email_verifications ON email_verifications")
    op.execute("DROP POLICY IF EXISTS select_own_password_resets ON password_resets")

    # 3. Drop sequence default and IDENTITY from users.user_id
    op.execute("ALTER TABLE users ALTER COLUMN user_id DROP DEFAULT")
    op.execute("ALTER TABLE users ALTER COLUMN user_id DROP IDENTITY IF EXISTS")

    # 4. Alter columns to UUID
    op.alter_column("users", "user_id", type_=sa.Uuid(), existing_type=sa.Integer(), postgresql_using="gen_random_uuid()")
    op.alter_column("account_memberships", "user_id", type_=sa.Uuid(), existing_type=sa.Integer(), postgresql_using="gen_random_uuid()")
    op.alter_column("email_verifications", "user_id", type_=sa.Uuid(), existing_type=sa.Integer(), postgresql_using="gen_random_uuid()")
    op.alter_column("password_resets", "user_id", type_=sa.Uuid(), existing_type=sa.Integer(), postgresql_using="gen_random_uuid()")

    # 5. Re-create foreign key constraints
    op.create_foreign_key(
        "account_memberships_user_id_fkey", "account_memberships", "users",
        ["user_id"], ["user_id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "email_verifications_user_id_fkey", "email_verifications", "users",
        ["user_id"], ["user_id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "password_resets_user_id_fkey", "password_resets", "users",
        ["user_id"], ["user_id"], ondelete="CASCADE"
    )

    # 6. Re-create RLS policies with ::uuid cast
    ## Users
    op.execute("""
        CREATE POLICY select_own_user ON users FOR SELECT TO playground_user_1 
        USING (user_id = current_setting('app.current_user_id', true)::uuid)
    """)

    op.execute("""
        CREATE POLICY update_own_user ON users FOR UPDATE TO playground_user_1 
        USING (user_id = current_setting('app.current_user_id', true)::uuid) 
        WITH CHECK (user_id = current_setting('app.current_user_id', true)::uuid)
    """)

    ## Accounts
    op.execute("""
        CREATE POLICY select_own_account ON accounts FOR SELECT TO playground_user_1 
        USING (
            EXISTS (
                SELECT 1 FROM account_memberships am
                WHERE am.account_id = accounts.account_id
                  AND am.user_id = current_setting('app.current_user_id', true)::uuid
            )
        )
    """)

    op.execute("""
        CREATE POLICY update_own_account ON accounts FOR UPDATE TO playground_user_1
        USING (
            EXISTS (
                SELECT 1 FROM account_memberships am
                JOIN roles r ON r.role_id = am.role_id
                WHERE am.account_id = accounts.account_id
                  AND am.user_id = current_setting('app.current_user_id', true)::uuid
                  AND r.name = 'admin'
            )
        )
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM account_memberships am
                JOIN roles r ON r.role_id = am.role_id
                WHERE am.account_id = accounts.account_id
                  AND am.user_id = current_setting('app.current_user_id', true)::uuid
                  AND r.name = 'admin'
            )
        )
    """)

    ## Account Memberships
    op.execute("""
        CREATE POLICY select_own_account_memberships ON account_memberships FOR SELECT TO playground_user_1
        USING (
            EXISTS (
                SELECT 1 FROM account_memberships am
                WHERE am.account_id = account_memberships.account_id
                  AND am.user_id = current_setting('app.current_user_id', true)::uuid
            )
        )
    """)

    op.execute("""
        CREATE POLICY admin_manage_account_members ON account_memberships FOR UPDATE TO playground_user_1
        USING (
            EXISTS (
                SELECT 1 FROM account_memberships am
                JOIN roles r ON r.role_id = am.role_id
                WHERE am.account_id = account_memberships.account_id
                  AND am.user_id = current_setting('app.current_user_id', true)::uuid
                  AND r.name = 'admin'
            )
        )
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM account_memberships am
                JOIN roles r ON r.role_id = am.role_id
                WHERE am.account_id = account_memberships.account_id
                  AND am.user_id = current_setting('app.current_user_id', true)::uuid
                  AND r.name = 'admin'
            )
        )
    """)

    op.execute("""
        CREATE POLICY admin_add_account_members ON account_memberships FOR INSERT TO playground_user_1
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM account_memberships am_actor
                JOIN roles r ON r.role_id = am_actor.role_id
                WHERE am_actor.account_id = account_memberships.account_id
                  AND am_actor.user_id = current_setting('app.current_user_id', true)::uuid
                  AND r.name = 'admin'
            )
        )
    """)

    op.execute("""
        CREATE POLICY admin_remove_account_members ON account_memberships FOR DELETE TO playground_user_1
        USING (
            EXISTS (
                SELECT 1 FROM account_memberships am
                JOIN roles r ON r.role_id = am.role_id
                WHERE am.account_id = account_memberships.account_id
                  AND am.user_id = current_setting('app.current_user_id', true)::uuid
                  AND r.name = 'admin'
            )
        )
    """)

    ## Email Verifications & Password Resets
    op.execute("""
        CREATE POLICY select_own_email_verifications ON email_verifications FOR SELECT TO playground_user_1 
        USING (user_id = current_setting('app.current_user_id', true)::uuid)
    """)

    op.execute("""
        CREATE POLICY select_own_password_resets ON password_resets FOR SELECT TO playground_user_1 
        USING (user_id = current_setting('app.current_user_id', true)::uuid)
    """)

    # 7. Grant explicit INSERT on user_id to API runtime user
    op.execute("GRANT INSERT (user_id) ON users TO playground_user_1")

    # 8. Update Functions referencing user_id
    ## get_user_for_login(text) -> user_id uuid
    op.execute("DROP FUNCTION IF EXISTS get_user_for_login(text)")
    op.execute("""
        CREATE FUNCTION get_user_for_login(p_username text)
        RETURNS TABLE (
            user_id uuid,
            password_hash text
        ) SECURITY DEFINER
        SET search_path = public
        LANGUAGE sql
        AS $$
            SELECT user_id, password
            FROM users
            WHERE username = p_username;
        $$;
    """)
    op.execute("GRANT EXECUTE ON FUNCTION get_user_for_login(text) TO playground_user_1")

    ## get_user_id_for_email(text) -> uuid
    op.execute("DROP FUNCTION IF EXISTS get_user_id_for_email(text)")
    op.execute("""
        CREATE FUNCTION get_user_id_for_email(p_email text)
        RETURNS uuid
        SECURITY DEFINER
        SET search_path = public
        LANGUAGE sql
        AS $$
            SELECT user_id FROM users WHERE email = p_email;
        $$;
    """)
    op.execute("GRANT EXECUTE ON FUNCTION get_user_id_for_email(text) TO playground_user_1")

    ## get_user_for_reset_token(text) -> user_id uuid
    op.execute("DROP FUNCTION IF EXISTS get_user_for_reset_token(text)")
    op.execute("""
        CREATE FUNCTION get_user_for_reset_token(p_token_hash text)
        RETURNS TABLE (
            user_id uuid,
            expires_at timestamptz,
            used_at timestamptz
        ) SECURITY DEFINER
        SET search_path = public
        LANGUAGE sql
        AS $$
            SELECT user_id, expires_at, used_at
            FROM password_resets
            WHERE token = p_token_hash
            ORDER BY created_at DESC LIMIT 1;
        $$;
    """)
    op.execute("GRANT EXECUTE ON FUNCTION get_user_for_reset_token(text) TO playground_user_1")

    ## insert_password_reset_token(uuid, text)
    op.execute("DROP FUNCTION IF EXISTS insert_password_reset_token(integer, text)")
    op.execute("DROP FUNCTION IF EXISTS insert_password_reset_token(uuid, text)")
    op.execute("""
        CREATE FUNCTION insert_password_reset_token(p_user_id uuid, p_token_hash text)
        RETURNS BOOLEAN 
        SECURITY DEFINER
        SET search_path = public
        LANGUAGE plpgsql
        AS $$
        BEGIN
            INSERT INTO password_resets (user_id, token)
            VALUES (p_user_id, p_token_hash);
            RETURN TRUE;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN FALSE;
        END;
        $$;
    """)
    op.execute("GRANT EXECUTE ON FUNCTION insert_password_reset_token(uuid, text) TO playground_user_1")

    ## insert_email_verification_token(uuid, text)
    op.execute("DROP FUNCTION IF EXISTS insert_email_verification_token(integer, text)")
    op.execute("DROP FUNCTION IF EXISTS insert_email_verification_token(uuid, text)")
    op.execute("""
        CREATE FUNCTION insert_email_verification_token(p_user_id uuid, p_token_hash text)
        RETURNS BOOLEAN 
        SECURITY DEFINER
        SET search_path = public
        LANGUAGE plpgsql
        AS $$
        BEGIN
            INSERT INTO email_verifications (user_id, token)
            VALUES (p_user_id, p_token_hash);
            RETURN TRUE;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN FALSE;
        END;
        $$;
    """)
    op.execute("GRANT EXECUTE ON FUNCTION insert_email_verification_token(uuid, text) TO playground_user_1")

    ## update_user_password(text, text)
    op.execute("DROP FUNCTION IF EXISTS update_user_password(text, text)")
    op.execute("""
        CREATE FUNCTION update_user_password(p_token_hash text, u_new_password text)
        RETURNS BOOLEAN
        SECURITY DEFINER
        SET search_path = public
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_user_id uuid;
        BEGIN
            SELECT user_id INTO v_user_id
            FROM password_resets
            WHERE token = p_token_hash
                AND used_at IS NULL
                AND expires_at > now()
            LIMIT 1
            FOR UPDATE;

            IF v_user_id IS NULL THEN
                RETURN FALSE;
            END IF;

            UPDATE users SET password = u_new_password WHERE user_id = v_user_id;
            UPDATE password_resets SET used_at = now() WHERE token = p_token_hash;
            RETURN TRUE;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN FALSE;
        END;
        $$;
    """)
    op.execute("GRANT EXECUTE ON FUNCTION update_user_password(text, text) TO playground_user_1")

    ## get_accounts_for_user(uuid)
    op.execute("DROP FUNCTION IF EXISTS get_accounts_for_user(integer)")
    op.execute("DROP FUNCTION IF EXISTS get_accounts_for_user(uuid)")
    op.execute("""
        CREATE FUNCTION get_accounts_for_user(p_user_id uuid)
        RETURNS TABLE(account_id integer, account_name text, account_type text, role_name text)
        SECURITY DEFINER
        SET search_path = public
        LANGUAGE sql
        AS $$
            SELECT a.account_id, a.name, a.type, r.name
            FROM account_memberships am
            JOIN accounts a ON a.account_id = am.account_id
            JOIN roles r ON r.role_id = am.role_id
            WHERE am.user_id = p_user_id;
        $$;
    """)
    op.execute("GRANT EXECUTE ON FUNCTION get_accounts_for_user(uuid) TO playground_user_1")


def downgrade() -> None:
    """Downgrade schema: Revert UUIDs back to INTEGER."""
    # 1. Drop foreign key constraints
    op.drop_constraint("account_memberships_user_id_fkey", "account_memberships", type_="foreignkey")
    op.drop_constraint("email_verifications_user_id_fkey", "email_verifications", type_="foreignkey")
    op.drop_constraint("password_resets_user_id_fkey", "password_resets", type_="foreignkey")

    # 2. Drop all RLS policies referencing user_id before altering column type
    op.execute("DROP POLICY IF EXISTS select_own_user ON users")
    op.execute("DROP POLICY IF EXISTS update_own_user ON users")
    op.execute("DROP POLICY IF EXISTS select_own_account ON accounts")
    op.execute("DROP POLICY IF EXISTS update_own_account ON accounts")
    op.execute("DROP POLICY IF EXISTS select_own_account_memberships ON account_memberships")
    op.execute("DROP POLICY IF EXISTS admin_manage_account_members ON account_memberships")
    op.execute("DROP POLICY IF EXISTS admin_add_account_members ON account_memberships")
    op.execute("DROP POLICY IF EXISTS admin_remove_account_members ON account_memberships")
    op.execute("DROP POLICY IF EXISTS select_own_email_verifications ON email_verifications")
    op.execute("DROP POLICY IF EXISTS select_own_password_resets ON password_resets")

    # 3. Alter columns back to Integer
    op.alter_column("users", "user_id", type_=sa.Integer(), existing_type=sa.Uuid(), postgresql_using="1")
    op.alter_column("account_memberships", "user_id", type_=sa.Integer(), existing_type=sa.Uuid(), postgresql_using="1")
    op.alter_column("email_verifications", "user_id", type_=sa.Integer(), existing_type=sa.Uuid(), postgresql_using="1")
    op.alter_column("password_resets", "user_id", type_=sa.Integer(), existing_type=sa.Uuid(), postgresql_using="1")

    # 4. Restore sequence default on users.user_id
    op.execute("CREATE SEQUENCE IF NOT EXISTS users_user_id_seq OWNED BY users.user_id")
    op.execute("ALTER TABLE users ALTER COLUMN user_id SET DEFAULT nextval('users_user_id_seq')")

    # 5. Re-create foreign key constraints
    op.create_foreign_key(
        "account_memberships_user_id_fkey", "account_memberships", "users",
        ["user_id"], ["user_id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "email_verifications_user_id_fkey", "email_verifications", "users",
        ["user_id"], ["user_id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "password_resets_user_id_fkey", "password_resets", "users",
        ["user_id"], ["user_id"], ondelete="CASCADE"
    )

    # 6. Re-create RLS policies with ::integer cast
    ## Users
    op.execute("""
        CREATE POLICY select_own_user ON users FOR SELECT TO playground_user_1 
        USING (user_id = current_setting('app.current_user_id', true)::integer)
    """)

    op.execute("""
        CREATE POLICY update_own_user ON users FOR UPDATE TO playground_user_1 
        USING (user_id = current_setting('app.current_user_id', true)::integer) 
        WITH CHECK (user_id = current_setting('app.current_user_id', true)::integer)
    """)

    ## Accounts
    op.execute("""
        CREATE POLICY select_own_account ON accounts FOR SELECT TO playground_user_1 
        USING (
            EXISTS (
                SELECT 1 FROM account_memberships am
                WHERE am.account_id = accounts.account_id
                  AND am.user_id = current_setting('app.current_user_id', true)::integer
            )
        )
    """)

    op.execute("""
        CREATE POLICY update_own_account ON accounts FOR UPDATE TO playground_user_1
        USING (
            EXISTS (
                SELECT 1 FROM account_memberships am
                JOIN roles r ON r.role_id = am.role_id
                WHERE am.account_id = accounts.account_id
                  AND am.user_id = current_setting('app.current_user_id', true)::integer
                  AND r.name = 'admin'
            )
        )
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM account_memberships am
                JOIN roles r ON r.role_id = am.role_id
                WHERE am.account_id = accounts.account_id
                  AND am.user_id = current_setting('app.current_user_id', true)::integer
                  AND r.name = 'admin'
            )
        )
    """)

    ## Account Memberships
    op.execute("""
        CREATE POLICY select_own_account_memberships ON account_memberships FOR SELECT TO playground_user_1
        USING (
            EXISTS (
                SELECT 1 FROM account_memberships am
                WHERE am.account_id = account_memberships.account_id
                  AND am.user_id = current_setting('app.current_user_id', true)::integer
            )
        )
    """)

    op.execute("""
        CREATE POLICY admin_manage_account_members ON account_memberships FOR UPDATE TO playground_user_1
        USING (
            EXISTS (
                SELECT 1 FROM account_memberships am
                JOIN roles r ON r.role_id = am.role_id
                WHERE am.account_id = account_memberships.account_id
                  AND am.user_id = current_setting('app.current_user_id', true)::integer
                  AND r.name = 'admin'
            )
        )
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM account_memberships am
                JOIN roles r ON r.role_id = am.role_id
                WHERE am.account_id = account_memberships.account_id
                  AND am.user_id = current_setting('app.current_user_id', true)::integer
                  AND r.name = 'admin'
            )
        )
    """)

    op.execute("""
        CREATE POLICY admin_add_account_members ON account_memberships FOR INSERT TO playground_user_1
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM account_memberships am_actor
                JOIN roles r ON r.role_id = am_actor.role_id
                WHERE am_actor.account_id = account_memberships.account_id
                  AND am_actor.user_id = current_setting('app.current_user_id', true)::integer
                  AND r.name = 'admin'
            )
        )
    """)

    op.execute("""
        CREATE POLICY admin_remove_account_members ON account_memberships FOR DELETE TO playground_user_1
        USING (
            EXISTS (
                SELECT 1 FROM account_memberships am
                JOIN roles r ON r.role_id = am.role_id
                WHERE am.account_id = account_memberships.account_id
                  AND am.user_id = current_setting('app.current_user_id', true)::integer
                  AND r.name = 'admin'
            )
        )
    """)

    ## Email Verifications & Password Resets
    op.execute("""
        CREATE POLICY select_own_email_verifications ON email_verifications FOR SELECT TO playground_user_1 
        USING (user_id = current_setting('app.current_user_id', true)::integer)
    """)

    op.execute("""
        CREATE POLICY select_own_password_resets ON password_resets FOR SELECT TO playground_user_1 
        USING (user_id = current_setting('app.current_user_id', true)::integer)
    """)

    # 7. Revoke explicit INSERT on user_id
    op.execute("REVOKE INSERT (user_id) ON users FROM playground_user_1")

    # 8. Revert Functions to integer
    op.execute("DROP FUNCTION IF EXISTS get_user_for_login(text)")
    op.execute("""
        CREATE FUNCTION get_user_for_login(p_username text)
        RETURNS TABLE (
            user_id integer,
            password_hash text
        ) SECURITY DEFINER
        SET search_path = public
        LANGUAGE sql
        AS $$
            SELECT user_id, password
            FROM users
            WHERE username = p_username;
        $$;
    """)
    op.execute("GRANT EXECUTE ON FUNCTION get_user_for_login(text) TO playground_user_1")

    op.execute("DROP FUNCTION IF EXISTS get_user_id_for_email(text)")
    op.execute("""
        CREATE FUNCTION get_user_id_for_email(p_email text)
        RETURNS integer
        SECURITY DEFINER
        SET search_path = public
        LANGUAGE sql
        AS $$
            SELECT user_id FROM users WHERE email = p_email;
        $$;
    """)
    op.execute("GRANT EXECUTE ON FUNCTION get_user_id_for_email(text) TO playground_user_1")

    op.execute("DROP FUNCTION IF EXISTS get_user_for_reset_token(text)")
    op.execute("""
        CREATE FUNCTION get_user_for_reset_token(p_token_hash text)
        RETURNS TABLE (
            user_id integer,
            expires_at timestamptz,
            used_at timestamptz
        ) SECURITY DEFINER
        SET search_path = public
        LANGUAGE sql
        AS $$
            SELECT user_id, expires_at, used_at
            FROM password_resets
            WHERE token = p_token_hash
            ORDER BY created_at DESC LIMIT 1;
        $$;
    """)
    op.execute("GRANT EXECUTE ON FUNCTION get_user_for_reset_token(text) TO playground_user_1")

    op.execute("DROP FUNCTION IF EXISTS insert_password_reset_token(uuid, text)")
    op.execute("DROP FUNCTION IF EXISTS insert_password_reset_token(integer, text)")
    op.execute("""
        CREATE FUNCTION insert_password_reset_token(p_user_id integer, p_token_hash text)
        RETURNS BOOLEAN 
        SECURITY DEFINER
        SET search_path = public
        LANGUAGE plpgsql
        AS $$
        BEGIN
            INSERT INTO password_resets (user_id, token)
            VALUES (p_user_id, p_token_hash);
            RETURN TRUE;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN FALSE;
        END;
        $$;
    """)
    op.execute("GRANT EXECUTE ON FUNCTION insert_password_reset_token(integer, text) TO playground_user_1")

    op.execute("DROP FUNCTION IF EXISTS insert_email_verification_token(uuid, text)")
    op.execute("DROP FUNCTION IF EXISTS insert_email_verification_token(integer, text)")
    op.execute("""
        CREATE FUNCTION insert_email_verification_token(p_user_id integer, p_token_hash text)
        RETURNS BOOLEAN 
        SECURITY DEFINER
        SET search_path = public
        LANGUAGE plpgsql
        AS $$
        BEGIN
            INSERT INTO email_verifications (user_id, token)
            VALUES (p_user_id, p_token_hash);
            RETURN TRUE;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN FALSE;
        END;
        $$;
    """)
    op.execute("GRANT EXECUTE ON FUNCTION insert_email_verification_token(integer, text) TO playground_user_1")

    op.execute("DROP FUNCTION IF EXISTS update_user_password(text, text)")
    op.execute("""
        CREATE FUNCTION update_user_password(p_token_hash text, u_new_password text)
        RETURNS BOOLEAN
        SECURITY DEFINER
        SET search_path = public
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_user_id integer;
        BEGIN
            SELECT user_id INTO v_user_id
            FROM password_resets
            WHERE token = p_token_hash
                AND used_at IS NULL
                AND expires_at > now()
            LIMIT 1
            FOR UPDATE;

            IF v_user_id IS NULL THEN
                RETURN FALSE;
            END IF;

            UPDATE users SET password = u_new_password WHERE user_id = v_user_id;
            UPDATE password_resets SET used_at = now() WHERE token = p_token_hash;
            RETURN TRUE;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN FALSE;
        END;
        $$;
    """)
    op.execute("GRANT EXECUTE ON FUNCTION update_user_password(text, text) TO playground_user_1")

    op.execute("DROP FUNCTION IF EXISTS get_accounts_for_user(uuid)")
    op.execute("DROP FUNCTION IF EXISTS get_accounts_for_user(integer)")
    op.execute("""
        CREATE FUNCTION get_accounts_for_user(p_user_id integer)
        RETURNS TABLE(account_id integer, account_name text, account_type text, role_name text)
        SECURITY DEFINER
        SET search_path = public
        LANGUAGE sql
        AS $$
            SELECT a.account_id, a.name, a.type, r.name
            FROM account_memberships am
            JOIN accounts a ON a.account_id = am.account_id
            JOIN roles r ON r.role_id = am.role_id
            WHERE am.user_id = p_user_id;
        $$;
    """)
    op.execute("GRANT EXECUTE ON FUNCTION get_accounts_for_user(integer) TO playground_user_1")