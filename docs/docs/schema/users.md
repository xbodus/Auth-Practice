## Overview
The users table serves to store individual user account information. User accounts will be the main 
object to determine authentication to and authorizations within an [account](/schema/accounts).

---

## Schema
```sql
CREATE TABLE users (
    user_id       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name    VARCHAR(50) NOT NULL,
    last_name     VARCHAR(50) NOT NULL,
    username      VARCHAR(50) NOT NULL UNIQUE,
    password      VARCHAR(100) NOT NULL,
    email         VARCHAR(100) NOT NULL UNIQUE,
    email_verified BOOLEAN DEFAULT FALSE NOT NULL,
    phone         VARCHAR(15) NOT NULL,
    dob           DATE NOT NULL,
    address       VARCHAR(150) NOT NULL,
    city          VARCHAR(50) NOT NULL,
    state         VARCHAR(50) NOT NULL,
    zipcode       VARCHAR(20) NOT NULL,
    country       VARCHAR(50) NOT NULL,
    company       VARCHAR(50),
    created_at    TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at    TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    active        BOOLEAN DEFAULT TRUE NOT NULL
);
```
<br>

---

## Security and API Permissions
**Row Level Security (RLS)** is enabled and enforced on the users table to control what data a
user can access. Specifically scoping a user to only accessing and altering their own information based
on their _*user_id*_ injected at time of operation using `SET LOCAL app.current_user_id`. User's 
user_id will be attached to JWT token during their session.

**API Permissions** are assigned to the database user the API uses to access the table to 
minimize unnecessary privileges and data over exposure at the data layer.  

### RLS Policies  
#### select_own_user 
```sql
CREATE POLICY select_own_user ON users FOR SELECT TO playground_user_1 
USING (
    user_id = current_setting('app.current_user_id', true)::integer
)
```
Limits rows users are able to select to only rows that are attached to their _*user_id*_. 
Users attempting to select from the users table without valid user_id will be blocked.

#### update_own_user 
```sql
CREATE POLICY update_own_user ON users FOR UPDATE TO playground_user_1 
USING (
    user_id = current_setting('app.current_user_id', true)::integer
) 
WITH CHECK (
    user_id = current_setting('app.current_user_id', true)::integer
)
```
Limits rows users are able to update to only rows that are attached to their _*user_id*_.
Users attempting to update data within the users table without valid user_id will be blocked.

<br>

### API Permissions 
#### SELECT Permissions 
```sql
GRANT SELECT (first_name, last_name, username, email, email_verified, phone, dob, company, address, city, zipcode, country, created_at, updated_at, active) ON users TO playground_user_1
```
Authenticated users will be able to select most information that is relevant to their user account. Excludes: user_id (attached to JWT after user authenticates) and password (only exposed at time of login). See [get_user_for_login()](/schema/functions/#get_user_for_logintext) for more information. 

#### UPDATE Permissions 
```sql
GRANT UPDATE (first_name, last_name, username, password, email, phone, dob, company, address, city, zipcode, country, active) ON users TO playground_user_1
```
Authenticated users will be able to update most information that is relevant to their user account. Users shouldn't be able to directly update fields that affect the user object identity, authorizations, or historical tracking, such as user_id, email_verified, created_at, and updated_at via the API.

#### INSERT Permissions
```sql
GRANT INSERT (first_name, last_name, username, password, email, phone, dob, address, city, state, zipcode, country, company) ON users TO playground_user_1
```
INSERT operations will be standardized. Users will be able to create entries via the API that contain values for first_name, last_name, username, email, phone, dob, company, address, city, zipcode, and country. As seen in the schema, none of these values are allowed to be `null`. Values will be automatically generated via the default values for user_id, email_verified, created_at, updated_at, and active at time of creation. Prior to INSERT operations, inputs will be validated and sanatized at the API level.

#### DELETE Permissions
DELETE operations on the users table will not be accessible through the API. Users looking to delete their accounts will have their active status updated to `false`, essentially soft-deactivating their accounts. Users who do not comeback after retention period will have their accounts permanently deleted by an automation script using a privileged database account. 

---

## Triggers
### trg_users_freeze_created_at
```sql
CREATE TRIGGER trg_users_freeze_created_at
BEFORE UPDATE
ON users
FOR EACH ROW
EXECUTE FUNCTION prevent_created_at_update()
```
Entries entered into the users table will automatically have a create_at value assigned to the entry at time of creation. This value is intended for accurate historical records, and should not be modified via the API or any privileged database user. To ensure this, `trg_users_freeze_created_at` calls [prevent_created_at_update()](/schema/functions/#prevent_created_at_update) to revert any potential updates to the created_at value to the original value.

### trg_update_email_verified
```sql
CREATE TRIGGER trg_update_email_verified
BEFORE UPDATE
ON users
FOR EACH ROW
EXECUTE FUNCTION reset_email_verified_on_change()
```
On account creation, new users will be asked to verify their email to verify account authenticity. Users who do not complete this task will not have privileged access to the application. This is a method to deter illegitimate signups, such as bot sign ups and avoid potential problems if account is locked out without a method to recover the account. Users will still be able to update their emails if necessary. Doing so would require re-verifying their email account causing `trg_update_email_verified` to fire and call [reset_email_verified_on_change()](/schema/functions/#reset_email_verified_on_change). 

### trg_users_updated_at
```sql
CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE
ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at()
```
On account creation, the updated_at value of the entry is synced with the created_at value. Every time the row is updated thereafter, `trg_users_updated_at` calls [set_updated_at()](/schema/functions/#set_updated_at) to sync the updated_at value to the current time of the update. 

---

## Relationships
- [account_memberships](/schema/account_memberships)
- [email_verifications](/schema/email_verifications)
- [password_resets](/schema/password_resets)


<br>