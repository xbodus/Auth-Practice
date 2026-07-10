# Auth Practice Playground
___
FastAPI + React Router * Postgres playground for testing API security best practices
___
## Auth Security Practices
__*Authentication Methods & Best Practices*__  
**API Keys**: Used for internal servers to authenticate each other  
**Oauth2**: Utilize 3rd party authentication such as Google's authentication  
**JWT**: Used for stateless authentication  
**MFA**: Using more than one method of authentication

__*Data at rest Best Practices*__  
**Hash Passwords**: Hash and salt passwords before storing in database

__*API Auth Security Best Practices*__  
**Rate Limit**: Limit number of requests to endpoints
**Account Lockout**: Lock accounts after multiple failed logins
**Permission Controls**: Implement proper account permissions: Admin, User, Guest, etc

__*Insecure*__  
**Basic Auth**: It is no longer enough to protect accounts with basic username and password
