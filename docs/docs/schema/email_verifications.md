## Overview
The `email_verifications` table stores verification token hashes sent to users upon account registration or email change requests. Each token is associated with a specific user, has a 5-minute expiration window, and tracks when it was used via `used_at`.

---

## Schema
```sql
CREATE TABLE email_verifications (
    verification_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token           VARCHAR(100) NOT NULL UNIQUE,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    expires_at      TIMESTAMPTZ DEFAULT NOW() + INTERVAL '5 minutes' NOT NULL,
    used_at         TIMESTAMPTZ
);
```

<br>

---

## Security and API Permissions
**Row Level Security (RLS)** is enabled and enforced on the `email_verifications` table to control authorizations for the API and database users. For example, specifically scoping a user to only accessing and altering their own information based on their _*user_id*_ injected at time of operation using `SET LOCAL app.current_user_id`. User's user_id will be attached to JWT token during their session.

**API Permissions** are assigned to the database user the API uses to access the table to minimize unnecessary privileges and data over exposure at the data layer.  

### RLS Policies
#### select_own_email_verifications
```sql
CREATE POLICY select_own_email_verifications ON email_verifications FOR SELECT TO playground_user_1
USING (
    user_id = current_setting('app.current_user_id', true)::integer
);
```
Limits rows users can SELECT on the email_verifications table to rows where the ***set user_id*** *is the token's user_id*. The user_id is set during the transaction using `SET LOCAL app.current_user_id`. Attempting to select tokens that do not have the set app.current_user_id as the token's user will return zero results.

<br>

### API Permissions
#### SELECT Permissions
```sql
GRANT SELECT (token, created_at, expires_at, used_at) ON email_verifications TO playground_user_1;
```
SELECT operations on email_verifications through the API will be used to allow users to validate tokens required to validate a users email.

#### UPDATE Permissions
UPDATE operations on email_verifications through the API are used to update the used_at value of a token at time of email verification. The API will not update the table directly, but through a security definer function called [verify_email_verification_token(text)](functions.md#verify_email_verification_tokentext).

#### INSERT Permissions
INSERT operations on email_verifications through the API are used to create tokens when a user either creates a new account, or updates the email of a user account after creation. The API will only need to insert the user_id attached to the user initiating the email verification workflow and hashed token, as token_id, created_at, expires_at, and used_at are all generated on token creation via defualt values. The insert operation will be handled by the security definer function [insert_email_verification_token(integer, text)](functions.md#insert_email_verification_tokeninteger-text)

#### DELETE Permissions
DELETE operations on the users table will not be accessible through the API. For record keeping purposes, tokens created will not be allowed to be deleted after creation via the API. After a retention period, the privileged database user will automatically remove tokens.

---

## Triggers
### trg_email_verifications_freeze_created_at
```sql
CREATE TRIGGER trg_email_verifications_freeze_created_at
BEFORE UPDATE ON email_verifications
FOR EACH ROW
EXECUTE FUNCTION prevent_created_at_update();
```
Entries entered into the email_verifications table will automatically have a create_at value assigned to the entry at time of creation. This value is intended for accurate historical records, and should not be modified via the API or any privileged database user. To ensure this, `trg_email_verifications_freeze_created_at` calls [prevent_created_at_update()](functions.md#prevent_created_at_update) to revert any potential updates to the created_at value to the original value.

### trg_email_verifications_freeze_expires_at
```sql
CREATE TRIGGER trg_email_verifications_freeze_expires_at
BEFORE UPDATE ON email_verifications
FOR EACH ROW
EXECUTE FUNCTION prevent_expires_at_update();
```
Entries entered into the email_verifications table will automatically have a expires_at value assigned to the entry at time of creation. This value is intended to strengthen token validation by putting a cap on the time a token is valid for use, and should not be modified via the API or any privileged database user. To ensure this, `trg_email_verifications_freeze_expires_at` calls [prevent_expires_at_update()](functions.md#prevent_expires_at_update) to revert any potential updates to the expires_at value to the original value.

---

## Relationships
- [users](users.md)

<br>