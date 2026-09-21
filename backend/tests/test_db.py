import pytest
import os
from pytest_postgresql import factories
from dotenv import load_dotenv
from pathlib import Path
import psycopg
from datetime import datetime, timezone

load_dotenv()

# Use pytest --postgresql-drop-test-database to clean up test database if client fails to cleanup
postgresql_my_proc = factories.postgresql_noproc(
    host=os.getenv("PG_HOST"),
    port=int(os.getenv("PG_PORT", 5432)),
    user=os.getenv("PG_SUPER_USER"),
    password=os.getenv("PG_SUPER_PASSWORD"),
    load=[Path("seed_data/postgres_seed.sql")]
)

client = factories.postgresql("postgresql_my_proc", dbname="test_playground")


def test_schema_seeded_correctly(client):
    with client.cursor() as cur:
        # Table exists
        cur.execute("SELECT to_regclass('users')")
        assert cur.fetchone()[0] is not None

        # RLS is enabled and forced
        cur.execute("""
            SELECT relrowsecurity, relforcerowsecurity
            FROM pg_class WHERE relname = 'users'
        """)
        row = cur.fetchone()
        assert row == (True, True)

        # Policies exist
        cur.execute("SELECT policyname FROM pg_policies WHERE tablename = 'users'")
        policies = {r[0] for r in cur.fetchall()}
        assert {"select_own_user", "update_own_user"} <= policies

        # Function exists
        cur.execute("SELECT proname FROM pg_proc WHERE proname = 'get_user_for_login'")
        assert cur.fetchone() is not None

        # Triggers exist
        cur.execute("""
            SELECT tgname FROM pg_trigger
            WHERE tgrelid = 'users'::regclass AND NOT tgisinternal
        """)
        triggers = {r[0] for r in cur.fetchall()}
        assert {"trg_users_updated_at", "trg_users_freeze_created_at", "trg_update_email_verified"} <= triggers


class TestSelectRLS:
    def test_select_no_user_id(self, client):
        """Test no data is returned if app.current_user_id is not set"""
        with client.cursor() as cur:
            # Set role to application user (where database policies are applicable)
            cur.execute("SET ROLE playground_user_1")

            cur.execute("SELECT first_name FROM users WHERE username = 'acmeemployee1'")
            results: tuple[str] | None = cur.fetchone()
            assert results is None

    def test_select_w_user_id(self, client):
        """Test user can select data associated to their user id"""
        with client.cursor() as cur:
            # Set role to application user (where database policies are applicable)
            cur.execute("SET ROLE playground_user_1")

            # Set current user id to 1 to test RLS on SELECT operation
            cur.execute("SET LOCAL app.current_user_id = 1")

            # Verify user can only SELECT entries related to their user_id
            cur.execute("SELECT first_name, last_name FROM users")
            results: list[tuple[str, str]] = cur.fetchall()
            assert len(results) == 1
            assert results[0][0] == "Paul"
            assert results[0][1] == "McDaniels"

    def test_select_w_bad_user_id(self, client):
        """Test user should not be allowed to select data not associated with their user_id"""
        with client.cursor() as cur:
            # Set role to application user (where database policies are applicable)
            cur.execute("SET ROLE playground_user_1")

            # Set app.current_user_id
            cur.execute("SET LOCAL app.current_user_id = 2")

            # Ensure users cannot select data not tied to their user_id (Paul's user id is 1)
            cur.execute("SELECT first_name FROM users WHERE first_name = 'Paul'")
            results = cur.fetchone()
            assert results is None

    def test_select_user_id(self, client):
        """Test user should not be allowed to select by user_id"""
        with client.cursor() as cur:
            # Set role to application user (where database policies are applicable)
            cur.execute("SET ROLE playground_user_1")

            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                cur.execute("SELECT user_id FROM users WHERE first_name = 'Paul'")

    def test_select_password(self, client):
        """Test user should not be allowed to select by password"""
        with client.cursor() as cur:
            # Set role to application user (where database policies are applicable)
            cur.execute("SET ROLE playground_user_1")

            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                cur.execute("SELECT password FROM users WHERE first_name = 'Paul'")

    def test_select_all(self, client):
        """Test user should not be allowed to select all (*) because they are not allowed to select user_id or password"""
        with client.cursor() as cur:
            # Set role to application user (where database policies are applicable)
            cur.execute("SET ROLE playground_user_1")

            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                cur.execute("SELECT * FROM users WHERE first_name = 'Paul'")


class TestUpdateRLS:
    def test_update_no_user_id(self, client):
        """Test no data is returned if app.current_user_id is not set"""
        with client.cursor() as cur:
            # Set role to application user (where database policies are applicable)
            cur.execute("SET ROLE playground_user_1")

            # Ensure users aren't allowed to update users if app.current_user_id not set
            cur.execute("UPDATE users SET first_name = 'Bob' WHERE first_name = 'Paul'")
            assert cur.rowcount == 0

            # Verify user "Paul" was not updated
            cur.execute("SET LOCAL app.current_user_id = 1")
            cur.execute("SELECT first_name FROM users WHERE username = 'acmeemployee1'")
            results: tuple[str] = cur.fetchone()
            assert results[0] == "Paul"

    def test_update_wrong_user_id(self, client):
        """User 2 cannot update user 1's row"""
        with client.cursor() as cur:
            cur.execute("SET ROLE playground_user_1")
            cur.execute("SET LOCAL app.current_user_id = 2")

            cur.execute("UPDATE users SET first_name = 'Bob' WHERE first_name = 'Paul'")
            assert cur.rowcount == 0

            cur.execute("RESET ROLE")
            cur.execute("SELECT first_name FROM users WHERE username = 'acmeemployee1'")
            results = cur.fetchone()
            assert results[0] == "Paul"

    def test_prevent_created_at_update_function_and_trigger(self, client):
        """Test UPDATE operations on created_at values revert to original value"""
        with client.cursor() as cur:
            # In order to test the function and trigger, playground_user_1 needs to be granted UPDATE privileges on created_at (defense in depth needs to be disabled temporarily)
            # Scoped to test database only
            cur.execute("GRANT UPDATE (created_at) ON users TO playground_user_1")

            # Set role to application user (where database policies are applicable)
            cur.execute("SET ROLE playground_user_1")

            cur.execute("SET LOCAL app.current_user_id = 1")

            # Fetch the original created_at time
            cur.execute("SELECT created_at FROM users WHERE first_name = 'Paul'")
            results = cur.fetchone()
            created = results[0]

            # Try to update and compare new created_at time against old created_at time
            cur.execute(f"UPDATE users SET created_at = %s WHERE first_name = 'Paul'", (datetime.now(timezone.utc),))
            cur.execute("SELECT created_at FROM users WHERE first_name = 'Paul'")
            results = cur.fetchone()
            assert results[0] == created

    def test_set_updated_at_function_and_trigger(self, client):
        """Test UPDATE operations on updated_at values update when table entry is updated"""
        with client.cursor() as cur:
            # Set role to application user (where database policies are applicable)
            cur.execute("SET ROLE playground_user_1")

            cur.execute("SET LOCAL app.current_user_id = 1")

            # Fetch the original updated_at time
            cur.execute("SELECT updated_at FROM users WHERE first_name = 'Paul'")
            results = cur.fetchone()
            updated = results[0]

            # Try to update and compare new updated_at time against old updated_at time
            cur.execute(f"UPDATE users SET username = 'acmeemployee2' WHERE first_name = 'Paul'")
            cur.execute("SELECT username, updated_at FROM users WHERE first_name = 'Paul'")
            results = cur.fetchone()
            assert results[0] == 'acmeemployee2'
            assert results[1] != updated

    def test_update_w_baseline_privileges(self, client):
        """Test user cannot update created_at with baseline table privileges"""
        with client.cursor() as cur:
            # Set role to application user (where database policies are applicable)
            cur.execute("SET ROLE playground_user_1")

            cur.execute("SET LOCAL app.current_user_id = 1")

            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                cur.execute("UPDATE users SET created_at = %s WHERE first_name = 'Paul'", (datetime.now(timezone.utc),))


class TestLogin:
    def test_get_user_for_login(self, client):
        """Test function to return username and password hash from database"""
        with client.cursor() as cur:
            # Set role to application user (where database policies are applicable)
            cur.execute("SET ROLE playground_user_1")

            cur.execute("SELECT * FROM get_user_for_login(%s)", ("acmeemployee1",))
            results = cur.fetchone()
            assert results is not None

            user_id, password = results
            assert user_id == 1
            assert password == "Pa55w0rd!"

    def test_get_user_for_login_invalid_username(self, client):
        """Returns nothing for a username that doesn't exist"""
        with client.cursor() as cur:
            cur.execute("SET ROLE playground_user_1")

            cur.execute("SELECT * FROM get_user_for_login(%s)", ("nonexistent_user",))
            result = cur.fetchone()

            assert result is None

    def test_direct_table_select_denied_without_function(self, client):
        """Check user cannot return user_id and password for authentication without using login function
           Important because users with not have authorization in the application without valid user_id
           User will not have valid user id until authenticated"""
        with client.cursor() as cur:
            cur.execute("SET ROLE playground_user_1")

            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                cur.execute("SELECT password FROM users WHERE username = %s", ("acmeemployee1",))


class TestFunctionsAndTriggers:
    def test_reset_email_verified(self, client):
        """Check trg_update_email_verified fires when user updates email resetting email verified using
            reset_email_verified_on_change function"""
        with client.cursor() as cur:
            cur.execute("SET ROLE playground_user_1")
            cur.execute("SET LOCAL app.current_user_id = 1")

            cur.execute("SELECT email_verified FROM users WHERE username = %s", ("acmeemployee1",))
            result = cur.fetchone()[0]

            cur.execute("UPDATE users SET email = %s WHERE username = %s", ("pmcdaniels2@acme.com", "acmeemployee1"))
            cur.execute("SELECT email_verified FROM users WHERE username= %s", ("acmeemployee1",))
            updated_result = cur.fetchone()[0]

            assert result is True
            assert updated_result != result
            assert updated_result is False

    def test_reset_email_verified_with_no_email_change(self, client):
        """Check trg_update_email_verified fires, but doesn't update email verified if user doesn't update
            email"""
        with client.cursor() as cur:
            cur.execute("SET ROLE playground_user_1")
            cur.execute("SET LOCAL app.current_user_id = 1")

            cur.execute("SELECT email_verified FROM users WHERE username = %s", ("acmeemployee1",))
            result = cur.fetchone()[0]

            cur.execute("UPDATE users SET first_name = %s WHERE username = %s", ("Pauline", "acmeemployee1"))
            cur.execute("SELECT email_verified FROM users WHERE username= %s", ("acmeemployee1",))
            updated_result = cur.fetchone()[0]

            assert result is True
            assert updated_result == result
            assert updated_result is True

    def test_user_cannot_update_email_verified_by_default(self, client):
        """Check user cannot directly update email_verified with current permissions"""
        with client.cursor() as cur:
            cur.execute("SET ROLE playground_user_1")
            cur.execute("SET LOCAL app.current_user_id = 1")

            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                cur.execute("UPDATE users SET email_verified = %s WHERE username = %s", (True, "acmeemployee1"))