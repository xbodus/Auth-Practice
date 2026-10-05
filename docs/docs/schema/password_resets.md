## Overview
The `password_resets` table stores token hashes used for secure password reset workflows. Each token is associated with a specific user, has a defined expiration window (defaulting to 5 minutes), and tracks whether and when it was consumed via `used_at`.

---

## Schema
```sql
CREATE TABLE password_resets (
    reset_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token      VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '5 minutes' NOT NULL,
    used_at    TIMESTAMPTZ
);
```

<br>

---

## Security and API Permissions
**Row Level Security (RLS)** is enabled and enforced on the `password_resets` table to control authorizations for API and database users. Operations are scoped to the user's `user_id` injected during transactions using `SET LOCAL app.current_user_id`.

**API Permissions** are restricted to limit token exposure and prevent tampering.

### RLS Policies
#### select_own_password_resets
```sql
CREATE POLICY select_own_password_resets ON password_resets FOR SELECT TO playground_user_1
USING (
    user_id = current_setting('app.current_user_id', true)::integer
);
```
Limits SELECT operations to password reset records belonging to the authenticated user.

<br>

### API Permissions
#### SELECT Permissions
```sql
GRANT SELECT (token, created_at, expires_at, used_at) ON password_resets TO playground_user_1;
```
SELECT operations on password_resets through the API will be used to allow users to validate tokens required to validate a users reset token.

#### UPDATE Permissions
UPDATE operations on password_resets through the API are used to update the used_at value of a token at time of email verification. The API will not update the table directly, but through a security definer function called [verify_password_reset_token(text)](functions.md#verify_password_reset_tokentext).

#### INSERT Permissions
INSERT operations on password_resets through the API are used to create tokens when a user initiates the password reset workflow. The API will only need to insert the user_id attached to the user initiating the password reset and hashed token, as token_id, created_at, expires_at, and used_at are all generated on token creation via defualt values. The insert operation will be handled by the security definer function [insert_password_reset_token(integer, text)](functions.md#insert_password_reset_tokeninteger-text)


#### DELETE Permissions
DELETE operations on the password_resets table will not be accessible through the API. For record keeping purposes, tokens created will not be allowed to be deleted after creation via the API. After a retention period, the privileged database user will automatically remove tokens.

---

## Triggers
### trg_password_resets_freeze_created_at
```sql
CREATE TRIGGER trg_password_resets_freeze_created_at
BEFORE UPDATE ON password_resets
FOR EACH ROW
EXECUTE FUNCTION prevent_created_at_update();
```
Entries entered into the password_resets table will automatically have a create_at value assigned to the entry at time of creation. This value is intended for accurate historical records, and should not be modified via the API or any privileged database user. To ensure this, `trg_password_resets_freeze_created_at` calls [prevent_created_at_update()](functions.md#prevent_created_at_update) to revert any potential updates to the created_at value to the original value.

### trg_password_resets_freeze_expires_at
```sql
CREATE TRIGGER trg_password_resets_freeze_expires_at
BEFORE UPDATE ON password_resets
FOR EACH ROW
EXECUTE FUNCTION prevent_expires_at_update();
```
Entries entered into the password_resets table will automatically have a expires_at value assigned to the entry at time of creation. This value is intended to strengthen token validation by putting a cap on the time a token is valid for use, and should not be modified via the API or any privileged database user. To ensure this, `trg_password_resets_freeze_expires_at` calls [prevent_expires_at_update()](functions.md#prevent_expires_at_update) to revert any potential updates to the expires_at value to the original value.

---

## Relationships
- [users](users.md)

<br>