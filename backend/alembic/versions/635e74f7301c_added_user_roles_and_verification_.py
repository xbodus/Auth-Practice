"""added user roles and verification schemea

Revision ID: 635e74f7301c
Revises: 0947b49f4b53
Create Date: 2026-09-05 16:07:27.701323

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '635e74f7301c'
down_revision: Union[str, Sequence[str], None] = '0947b49f4b53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Creation script for accounts: Personal (single user) and business (multitenant)
    op.create_table('accounts',
        sa.Column('account_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('active', sa.Boolean, server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint('account_id'),
        sa.CheckConstraint("type IN ('Personal', 'Business')", name='ck_accounts_type')
    )

    # Creation script for roles table: Defines roles for authorization purposes: Application only. Playground_user_1 will not be able to create roles
    op.create_table('roles',
        sa.Column('role_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('role_id'),
        sa.UniqueConstraint('name')
    )

    # Roles seed data
    op.execute("""INSERT INTO roles (name, description)
                    VALUES 
                        ('user', 'Basic user account with basic read-only permission within account and privileged access to own resources and resources assigned by manager or admin'),
                        ('manager', 'Privileged user for users assigned to manage resources within an account'),
                        ('admin', 'Superuser with complete control of account including account members. WARNING: Due to privileged nature of account, use sparingly')
               """)

    # Creation script for account memberships: Maps users and their roles to accounts
    op.create_table('account_memberships',
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.account_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('account_id', 'user_id')
    )

    # Creation script for email verification tokens
    op.create_table('email_verifications',
        sa.Column('verification_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=100), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), server_default=sa.text("now() + interval '5 minutes'"), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('verification_id')
    )

    # Creation script for password reset verification tokens
    op.create_table('password_resets',
        sa.Column('reset_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=100), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), server_default=sa.text("now() + interval '5 minutes'"), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('reset_id')
    )

    # User table alterations
    op.alter_column('users', 'phone',
                existing_type=sa.VARCHAR(length=15),
                nullable=False)
    op.alter_column('users', 'dob',
                existing_type=sa.DATE(),
                nullable=False)
    op.alter_column('users', 'created_at',
                existing_type=postgresql.TIMESTAMP(),
                type_=sa.DateTime(timezone=True),
                existing_nullable=False,
                existing_server_default=sa.text('now()'))
    op.alter_column('users', 'updated_at',
                existing_type=postgresql.TIMESTAMP(),
                type_=sa.DateTime(timezone=True),
                existing_nullable=False,
                existing_server_default=sa.text('now()'))
    op.add_column('users', sa.Column('active',
                sa.Boolean,
                server_default=sa.true(),
                nullable=False))

    # --------------------------------------------------------
    # SQL user permissions & RLS policies
    # Playground_user_1 should only have read-only privileges on Roles, EmailVerification, and PasswordToken tables
    # Can modify user roles (limited ability based on role. Managed at API level)
    # User roles as follows:
    #    - No account: guest
    #    - Sub-account: user/manager
    #    - Account manager: admin
    # Account owner defaults to admin access who can assign elevated account privileges to sub-accounts
    # Lock account access to accounts user is signed in under
    op.execute("ALTER TABLE accounts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE accounts FORCE ROW LEVEL SECURITY")

    op.execute("ALTER TABLE account_memberships ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE account_memberships FORCE ROW LEVEL SECURITY")

    op.execute("ALTER TABLE email_verifications ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE email_verifications FORCE ROW LEVEL SECURITY")

    op.execute("ALTER TABLE password_resets ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE password_resets FORCE ROW LEVEL SECURITY")

    # --------------------------------------------------------
    # Drop any duplicate policies
    ## Accounts
    op.execute("DROP POLICY IF EXISTS select_own_account ON accounts")
    op.execute("DROP POLICY IF EXISTS update_own_account ON accounts")
    op.execute("DROP TRIGGER IF EXISTS trg_accounts_updated_at ON accounts")
    op.execute("DROP TRIGGER IF EXISTS trg_accounts_freeze_created_at ON accounts")

    ## Account Memberships
    op.execute("DROP POLICY IF EXISTS select_own_account_memberships ON account_memberships")
    op.execute("DROP POLICY IF EXISTS admin_manage_account_members ON account_memberships")
    op.execute("DROP POLICY IF EXISTS admin_add_account_members ON account_memberships")
    op.execute("DROP POLICY IF EXISTS admin_remove_account_members ON account_memberships")
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_last_admin_removal ON account_memberships")
    op.execute("DROP TRIGGER IF EXISTS trg_account_memberships_freeze_created_at ON account_memberships")

    ## Email Verifications
    op.execute("DROP POLICY IF EXISTS select_own_email_verifications ON email_verifications")
    op.execute("DROP POLICY IF EXISTS update_own_email_verifications ON email_verifications")
    op.execute("DROP TRIGGER IF EXISTS trg_email_verifications_freeze_created_at ON email_verifications")
    op.execute("DROP TRIGGER IF EXISTS trg_email_verifications_freeze_expires_at ON email_verifications")

    ## Password Resets
    op.execute("DROP POLICY IF EXISTS select_own_password_resets ON password_resets")
    op.execute("DROP POLICY IF EXISTS update_own_password_resets ON password_resets")
    op.execute("DROP TRIGGER IF EXISTS trg_password_resets_freeze_created_at ON password_resets")
    op.execute("DROP TRIGGER IF EXISTS trg_password_resets_freeze_expires_at ON password_resets")

    ## Functions
    op.execute("DROP FUNCTION IF EXISTS prevent_expires_at_update()")
    op.execute("DROP FUNCTION IF EXISTS get_user_for_reset_token(text)")
    op.execute("DROP FUNCTION IF EXISTS get_user_id_for_email(text)")
    op.execute("DROP FUNCTION IF EXISTS insert_password_reset_token(integer, text)")
    op.execute("DROP FUNCTION IF EXISTS update_user_password(text, text)")
    op.execute("DROP FUNCTION IF EXISTS prevent_last_admin_removal()")
    op.execute("DROP FUNCTION IF EXISTS get_accounts_for_user(integer)")

    # --------------------------------------------------------
    # Grant SELECT, UPDATE, DELETE permissions where necessary
    ## Users Table
    op.execute("GRANT SELECT (active) ON users TO playground_user_1")
    op.execute("GRANT UPDATE (active) ON users TO playground_user_1")

    ## Accounts Table
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
    op.execute("GRANT SELECT (name, type, active) ON accounts TO playground_user_1")
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
    op.execute("GRANT UPDATE (name, type, active) ON accounts TO playground_user_1")


    ## Account Memberships Table
    op.execute("""
        CREATE POLICY select_own_account_memberships ON account_memberships FOR SELECT TO playground_user_1
        USING (
            EXISTS (
                SELECT 1 FROM account_memberships am
                WHERE am.account_id = account_memberships.account_id
                  AND am.user_id = current_setting('app.current_user_id', true)::integer
            )
        );
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
        );
    """)
    op.execute("GRANT SELECT ON account_memberships TO playground_user_1")
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
    op.execute("GRANT UPDATE (role_id) ON account_memberships TO playground_user_1")
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
        );
    """)
    op.execute("GRANT DELETE ON account_memberships TO playground_user_1")
    op.execute("GRANT INSERT (account_id, user_id, role_id) ON account_memberships TO playground_user_1")

    ## Email Verifications
    op.execute("CREATE POLICY select_own_email_verifications ON email_verifications FOR SELECT TO playground_user_1 USING (user_id = current_setting('app.current_user_id', true)::integer)")
    op.execute("GRANT SELECT (token, created_at, expires_at, used_at) ON email_verifications TO playground_user_1")
    op.execute("CREATE POLICY update_own_email_verifications ON email_verifications FOR UPDATE TO playground_user_1 USING (user_id = current_setting('app.current_user_id', true)::integer)")
    op.execute("GRANT UPDATE (used_at) ON email_verifications TO playground_user_1")

    ## Password Resets
    op.execute("CREATE POLICY select_own_password_resets ON password_resets FOR SELECT TO playground_user_1 USING (user_id = current_setting('app.current_user_id', true)::integer)")
    op.execute("GRANT SELECT (token, created_at, expires_at, used_at) ON password_resets TO playground_user_1")
    op.execute("CREATE POLICY update_own_password_resets ON password_resets FOR UPDATE TO playground_user_1 USING (user_id = current_setting('app.current_user_id', true)::integer)")
    op.execute("GRANT UPDATE (used_at) ON password_resets TO playground_user_1")

    ## Roles
    op.execute("GRANT SELECT ON roles TO playground_user_1")

    # Functions and Triggers
    op.execute("""
               CREATE TRIGGER trg_accounts_updated_at
                   BEFORE UPDATE
                   ON accounts
                   FOR EACH ROW
                   EXECUTE FUNCTION set_updated_at()
               """)

    op.execute("""
               CREATE TRIGGER trg_accounts_freeze_created_at
                   BEFORE UPDATE
                   ON accounts
                   FOR EACH ROW
                   EXECUTE FUNCTION prevent_created_at_update()
               """)

    op.execute("""
               CREATE TRIGGER trg_account_memberships_freeze_created_at
                   BEFORE UPDATE
                   ON account_memberships
                   FOR EACH ROW
                   EXECUTE FUNCTION prevent_created_at_update()
               """)

    op.execute("""
               CREATE TRIGGER trg_email_verifications_freeze_created_at
                   BEFORE UPDATE
                   ON email_verifications
                   FOR EACH ROW
                   EXECUTE FUNCTION prevent_created_at_update()
               """)

    op.execute("""
               CREATE TRIGGER trg_password_resets_freeze_created_at
                   BEFORE UPDATE
                   ON password_resets
                   FOR EACH ROW
                   EXECUTE FUNCTION prevent_created_at_update()
               """)

    op.execute("""
               CREATE FUNCTION prevent_expires_at_update()
                   RETURNS trigger
                   LANGUAGE plpgsql
                AS $$
                   BEGIN
                            NEW.expires_at = OLD.expires_at;
                   RETURN NEW;
                   END;
                $$
               """)

    op.execute("""
               CREATE TRIGGER trg_email_verifications_freeze_expires_at
                   BEFORE UPDATE
                   ON email_verifications
                   FOR EACH ROW
                   EXECUTE FUNCTION prevent_expires_at_update()
               """)

    op.execute("""
               CREATE TRIGGER trg_password_resets_freeze_expires_at
                   BEFORE UPDATE
                   ON password_resets
                   FOR EACH ROW
                   EXECUTE FUNCTION prevent_expires_at_update()
               """)

    ## Preverification function: Use when user attempts a password reset. Fetches user_id to attach to password reset token
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

    ## Preverification function: Use when user attempts to verify password reset token. Exposes only what's necessary to verify the token's authenticity
    op.execute("""
               CREATE FUNCTION get_user_for_reset_token(p_token_hash text)
                   RETURNS TABLE
                           (
                               user_id    integer,
                               expires_at timestamptz,
                               used_at    timestamptz
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

    ## Preverification function: Inserts generated password reset hash into database. Verifies success before email is sent to user with token
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

    ## Preverification function: Allows user to update their password for their account so the can log-in. First verifies token is not expired or used before updating password
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

    ## Grabs accounts user is assigned to so they can select which account they want to use. Account ID will be stored in JWT
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

    ## Prevents soft locking accounts if no admins left
    op.execute("""
        CREATE FUNCTION prevent_last_admin_removal()
            RETURNS trigger
            LANGUAGE plpgsql
        AS $$
        DECLARE
            admin_role_id integer;
            remaining_admins integer;
        BEGIN
            SELECT role_id INTO admin_role_id FROM roles WHERE name = 'admin';
        
            IF OLD.role_id = admin_role_id THEN
                IF TG_OP = 'DELETE' OR NEW.role_id != admin_role_id THEN
                    SELECT COUNT(*) INTO remaining_admins
                    FROM account_memberships
                    WHERE account_id = OLD.account_id
                      AND role_id = admin_role_id
                      AND user_id != OLD.user_id;
        
                    IF remaining_admins = 0 THEN
                        RAISE EXCEPTION 'Cannot remove the last admin from account %', OLD.account_id;
                    END IF;
                END IF;
            END IF;
        
            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            END IF;
            RETURN NEW;
        END;
        $$;
        
        
    """)

    op.execute("""
        CREATE TRIGGER trg_prevent_last_admin_removal
        BEFORE UPDATE OR DELETE ON account_memberships
        FOR EACH ROW
        EXECUTE FUNCTION prevent_last_admin_removal();
    """)




def downgrade() -> None:
    """Downgrade schema."""

    # --------------------------------------------------------
    # Drop triggers first (must go before their functions)
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_last_admin_removal ON account_memberships")
    op.execute("DROP TRIGGER IF EXISTS trg_account_memberships_freeze_created_at ON account_memberships")
    op.execute("DROP TRIGGER IF EXISTS trg_password_resets_freeze_expires_at ON password_resets")
    op.execute("DROP TRIGGER IF EXISTS trg_email_verifications_freeze_expires_at ON email_verifications")
    op.execute("DROP TRIGGER IF EXISTS trg_password_resets_freeze_created_at ON password_resets")
    op.execute("DROP TRIGGER IF EXISTS trg_email_verifications_freeze_created_at ON email_verifications")
    op.execute("DROP TRIGGER IF EXISTS trg_accounts_freeze_created_at ON accounts")
    op.execute("DROP TRIGGER IF EXISTS trg_accounts_updated_at ON accounts")

    # Drop functions introduced by this migration
    # (set_updated_at and prevent_created_at_update predate this migration — leave them alone)
    op.execute("DROP FUNCTION IF EXISTS prevent_last_admin_removal()")
    op.execute("DROP FUNCTION IF EXISTS get_accounts_for_user(integer)")
    op.execute("DROP FUNCTION IF EXISTS update_user_password(text, text)")
    op.execute("DROP FUNCTION IF EXISTS insert_password_reset_token(integer, text)")
    op.execute("DROP FUNCTION IF EXISTS get_user_for_reset_token(text)")
    op.execute("DROP FUNCTION IF EXISTS get_user_id_for_email(text)")
    op.execute("DROP FUNCTION IF EXISTS prevent_expires_at_update()")

    # --------------------------------------------------------
    # Revert users table alterations
    op.execute("REVOKE UPDATE (active) ON users FROM playground_user_1")
    op.execute("REVOKE SELECT (active) ON users FROM playground_user_1")
    op.drop_column('users', 'active')

    op.alter_column('users', 'updated_at',
                existing_type=sa.DateTime(timezone=True),
                type_=postgresql.TIMESTAMP(),
                existing_nullable=False,
                existing_server_default=sa.text('now()'))
    op.alter_column('users', 'created_at',
                existing_type=sa.DateTime(timezone=True),
                type_=postgresql.TIMESTAMP(),
                existing_nullable=False,
                existing_server_default=sa.text('now()'))
    op.alter_column('users', 'dob',
                existing_type=sa.DATE(),
                nullable=True)
    op.alter_column('users', 'phone',
                existing_type=sa.VARCHAR(length=15),
                nullable=True)

    # --------------------------------------------------------
    # Drop tables — children before parents (FK-safe order)
    # account_memberships references accounts, users, roles
    op.drop_table('account_memberships')

    # email_verifications / password_resets reference users only
    op.drop_table('password_resets')
    op.drop_table('email_verifications')

    # roles and accounts have no remaining dependents at this point
    op.drop_table('roles')
    op.drop_table('accounts')
