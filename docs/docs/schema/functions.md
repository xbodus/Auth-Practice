# Functions

## Overview
Functions have been added to the database to minimize data exposure and allow for certain 
functionality within the database. This section covers every function within the database and
use cases within the application.

---

## Pre-Authentication Functions
### get_user_for_login(text)
```sql
# Function
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
$$;

# Grant execution privileges on the function to API user
GRANT EXECUTE ON FUNCTION get_user_for_login(text) TO playground_user_1;
```
To expose only data need for users logging into the application, `get_user_for_login(text)` is used to
inject only the **user_id** and **password_hash** during the login process. Doing this bypasses RLS policies 
that require a valid user_id (which is not available to an unauthenticated user) to access user login data. 
See [users schema](/schema/users/#security-and-api-permissions) for more information on relevant policies and permissions.


### get_user_id_for_email(text)
```sql
CREATE FUNCTION get_user_id_for_email(p_email text)
    RETURNS integer
    SECURITY DEFINER
    SET search_path = public
    LANGUAGE sql
AS $$
    SELECT user_id FROM users WHERE email = p_email;
$$;

GRANT EXECUTE ON FUNCTION get_user_id_for_email(text) TO playground_user_1;
```

Function required for pre-authenticated workflows that require a valid **user_id**. Takes a user's email, and returns the user_id attached to that email. Users who need to reset their password will need to access a limited list of tables in the database prior to authentication. All tables have RLS policies that required at minimum a valid user_id to access rows, such as the [password_resets](/schema/password_resets) table that stores tokens attached to the user's user_id required to validate user identity prior to resetting the password. Users that haven't logged in are pre-authenticated and their user_id has not been attached to their session via JWT. For the duration of the password reset workflow, `get_user_id_for_email(text)` is used by the API to get the user_id of a user's email.  


### insert_password_reset_token(integer, text)
```sql
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

GRANT EXECUTE ON FUNCTION insert_password_reset_token(integer, text) TO playground_user_1;
```

Function called by the API when pre-authenticated user initializes a password reset workflow. Takes the user_id and generated password token hash, and stores it in the reset_tokens table. Returns true if insert is successful, else false. Tokens inserted using this function will automatically have a created_at value, an expires_at value (5 minutes after generation), and will default into an unused state at time of creation. 


### get_user_for_reset_token(text)
```sql
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

GRANT EXECUTE ON FUNCTION get_user_for_reset_token(text) TO playground_user_1;
```

Function used during password reset workflow used to validate the authenticity of a password reset token. Takes password reset token, and returns the attached user_id, expires_at, and used_at. When a user is validating a token prior to resetting their password, the token needs to meet some conditions: the token needs to be attached to the user via user_id, it cannot be expired, and it must not be used. _*This is a read-only pre-check for the UI to know if user can move to password reset, or be denied.*_ If these conditions are met, the user will be allowed to update their password using [update_user_password()](#update_user_passwordtext-text)


### update_user_password(text, text)
```sql
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

GRANT EXECUTE ON FUNCTION update_user_password(text, text) TO playground_user_1;
```

Function used to finalize the password reset workflow of a pre-authenticated user. Takes a validated token and new password, grabs the user_id from _*the user_id attached to the token*_ and stores it in **v_user_id** if the token is not expired or used, updates the user's password with the new password using the user_id from the token, and updates the used_at column of the token. Returns true if the operation was successful, else false. See [set_updated_at()](#set_updated_at) to see how the user's updated_at value is synced with the time of the password change.


## Post-Authentication Functions
### get_accounts_for_user(integer)
```sql
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

GRANT EXECUTE ON FUNCTION get_accounts_for_user(integer) TO playground_user_1;
```

Function used after a successful login to display all accounts a user is a member of using the user's user_id. The application is multitenant enabled, meaning a user can be a part of more than one account. Because of this, if the user is a member of more than one account, they will need to select which account they will be operating within to complete the login process. The API calls `get_accounts_for_user(integer)` during the login processes and stores the selected account_id as a part of the JWT for the session.

---

## Table Functions
### prevent_created_at_update()
```sql
CREATE FUNCTION prevent_created_at_update()
    RETURNS trigger
    LANGUAGE plpgsql
AS $$
    BEGIN
        NEW.created_at = OLD.created_at;
        RETURN NEW;
    END;
$$;
```
Function used by tables to freeze the created_at value of entries. Created_at is a value automatically added to inserted rows at the time of creation. No user, not a regular user or privileged database admin, will be allowed to update the created_at value, as it serves as an important historical record keeping value. To ensure this, tables that include a created_at column will not allow the API UPDATE permission to the created_at column, and a trigger is attached to applicable tables calling `prevent_created_at_update()` to prevent even privileged database accounts from updating the value while the trigger is active.

### set_updated_at()
```sql
CREATE FUNCTION set_updated_at()
    RETURNS trigger
    LANGUAGE plpgsql
AS $$
    BEGIN
        NEW.updated_at = now();
        RETURN NEW;
    END;
$$;
```

Function used by tables to automatically sync the updated_at value when certain conditions have been me. Every time an entry is updated, the updated_at value needs to be synced to the current time of the update. This needs to be ensured, and not remembered. Also, this value should only be updated when the UPDATE operation is ran on valid columns in a row and no other condition. The updated value should not be updated manually. To achieve this, the API user is assigned UPDATE permissions on columns allowed to be updated per table schema and triggers have been setup on tables with the updated_at column calling `set_updated_at()` at the time that any applicable row that meets the aforementioned conditions has been updated. 

### prevent_expires_at_update()
```sql
CREATE FUNCTION prevent_expires_at_update()
    RETURNS trigger
    LANGUAGE plpgsql
AS $$
    BEGIN
        NEW.expires_at = OLD.expires_at;
        RETURN NEW;
    END;
$$;
```

Function used by token tables ([password_resets](/schema/password_resets) and [email_verfications](/schema/email_verifications)) to prevent tampering of the expires_at value. Token verification relies on expires_at as an important parmemeter to determine the validity of a token. This value must be set at time of token creation and never altered thereafter, as it can lead to malicious use cases. To ensure proper preventative measures are in place, the API is not given permission to perform UPDATE operations on tables that include the expires_at column, and applicable tables have triggers that call on `prevent_expires_at_update()` to block privileged database accounts from updating the column while the trigger is active. 


### prevent_last_admin_removal()
```sql
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
```

Function used by [accounts](/schema/accounts) to prevent users from soft locking accounts due to no admins being able to control the account. User within an account assigned the role of admin will have ultimate control of what happens in their account, barring they follow acceptable use policies. The admin account will be in control of deciding account authorizations to sub-users, controlling account details, and deciding deactivation of account. Deleting all admins from an account would cause the account to lose access to this functionality, essentially soft locking the account from alterations that require an admin. To prevent this, a trigger is placed on the accounts table that calls `prevent_last_admin_removal()` on UPDATE and DELETE operations.
<br>