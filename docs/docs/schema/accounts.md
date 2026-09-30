## Overview
\[Product\] is a multitenant application, allowing a single user account to be a member of multiple accounts. The accounts table defines the basic qualities of an account, and works in conjunction with [account_memberships](account_memberships.md) to map users to accounts.

---

## Schema
```sql
CREATE TABLE accounts (
    account_id  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    type        VARCHAR(20) NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at  TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    active      BOOLEAN DEFAULT TRUE NOT NULL,
    CONSTRAINT ck_accounts_type CHECK (type IN ('Personal', 'Business'))
);
```
<br>

---

## Sercurity and API Permissions
**Row Level Security (RLS)** is enabled and enforced on the accounts table to control authorizations for the API and database users. For example, specifically scoping a user to only accessing and altering their own information based on their _*user_id*_ injected at time of operation using `SET LOCAL app.current_user_id`. User's user_id will be attached to JWT token during their session.

**API Permissions** are assigned to the database user the API uses to access the table to minimize unnecessary privileges and data over exposure at the data layer.  

### RLS Policies
#### select_own_account
```sql
CREATE POLICY select_own_account ON accounts FOR SELECT TO playground_user_1 
USING (
    EXISTS (
        SELECT 1 FROM account_memberships am
        WHERE am.account_id = accounts.account_id
            AND am.user_id = current_setting('app.current_user_id', true)::integer
    )
);
```
Limits rows users can SELECT on the accounts table to rows where the ***set user_id*** *is a member of the account*. The user_id is set during the transaction using `SET LOCAL app.current_user_id`. Attempting to select accounts that do not have the set app.current_user_id as a member will return zero results.

#### update_own_account
```sql
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
);
```
Limits rows users can UPDATE on the accounts table to rows where the ***set user_id*** *is a member of account AND is assigned the admin role within the account*. Because users will have ultimate control of the state of their account, most importantly if the account is active or not, only the admins of accounts will have the capabilities to update account settings. The user_id is set during the transaction using `SET LOCAL app.current_user_id`. Attempting to update accounts that do not have the set app.current_user_id as a member or as a non-admin will be blocked.

<br>

### API Permissions
#### SELECT Permissions
```sql
GRANT SELECT (name, type, active) ON accounts TO playground_user_1;
```
Authenticated users will be able to select necessary information that is relevant to the account they are a member of, such as the name of the account, the type of account, and if the account is active. **Excludes**: account_id (attached to JWT after user selects account after authenticating), created_at, and updated_at (used for historical records). See [get_accounts_for_user(integer)](functions.md#get_accounts_for_userinteger) for more information. 

#### UPDATE Permissions
```sql
GRANT UPDATE (name, type, active) ON accounts TO playground_user_1;
```
Authenticated users will be able to update necessary information that is relevant to accounts they are an admin member of. Users shouldn't be able to directly update fields that affect the account's object identity or historical tracking, such as account_id, created_at, and updated_at via the API.

#### INSERT Permissions
```sql
GRANT INSERT (name, type) ON accounts TO playground_user_1;
```
INSERT operations will be standardized. Users will be able to create entries via the API that contain values for name and type—the type value will be checked validated using enum at API level and checked against constraint at data level to ensure Personal or Business account type. As seen in the [schema](#schema), none of these values are allowed to be `null`. Values will be automatically generated via the default values for account_id, created_at, updated_at, and active at time of creation. Prior to INSERT operations, inputs will be validated and sanatized at the API level.

#### DELETE Permissions
DELETE operations on the accounts table will not be accessible through the API. Users looking to delete their accounts will have their active status updated to `false`, essentially soft-deactivating their accounts. Users who do not comeback after retention period will have their accounts permanently deleted by an automation script using a privileged database account. 

---

## Triggers
### trg_accounts_freeze_created_at
```sql
CREATE TRIGGER trg_accounts_freeze_created_at
BEFORE UPDATE
ON accounts
FOR EACH ROW
EXECUTE FUNCTION prevent_created_at_update();
```
Entries entered into the accounts table will automatically have a create_at value assigned to the entry at time of creation. This value is intended for accurate historical records, and should not be modified via the API or any privileged database user. To ensure this, `trg_accounts_freeze_created_at` calls [prevent_created_at_update()](functions.md#prevent_created_at_update) to revert any potential updates to the created_at value to the original value.

### trg_accounts_updated_at
```sql
CREATE TRIGGER trg_accounts_updated_at
BEFORE UPDATE
ON accounts
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
```
On account creation, the updated_at value of the entry is synced with the created_at value. Every time the row is updated thereafter, `trg_users_updated_at` calls [set_updated_at()](functions.md#set_updated_at) to sync the updated_at value to the current time of the update. 

---

## Relationships
- [account_memberships](account_memberships.md)
