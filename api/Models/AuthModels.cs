/*
Models.cs 

Stores records and classes for DTOs (Data Transfer Objects)
*/
using System.ComponentModel.DataAnnotations;

namespace Verolith.Api.Models;


public record LoginCredentials(
    [property: Required(ErrorMessage = "Invalid username/password")] string Username, 
    [property: Required(ErrorMessage = "Invalid username/password")] string Password
);

public record UserLoginRecord(Guid UserId, string PasswordHash);

// Create tomorrow
public record AccountSignupRecord();

// See users table documentation for more information on user inserts
public record UserSignupRecord(
    [property: Required(ErrorMessage = "First name required"), MaxLength(50, ErrorMessage = "First name exceeds maximum length")] 
    string FirstName,
    [property: Required(ErrorMessage = "Last name required"), MaxLength(50, ErrorMessage = "Last name exceeds maximum length")] 
    string LastName,
    [property: Required(ErrorMessage = "Username required"), MaxLength(50, ErrorMessage = "Username exceeds maximum length")] 
    string Username,
    [property: Required(ErrorMessage = "Password required"), MaxLength(100, ErrorMessage = "Password exceeds maximum length")] 
    string Password,
    [property: Required(ErrorMessage = "Email required"), MaxLength(50, ErrorMessage = "Email exceeds maximum length"), EmailAddress] 
    string Email,
    [property: Required(ErrorMessage = "Phone required"), MaxLength(15, ErrorMessage = "Phone exceeds maximum length")] 
    string Phone,
    [property: Required(ErrorMessage = "Date of birth required")] 
    DateOnly DOB,
    [property: Required(ErrorMessage = "Address required"), MaxLength(150, ErrorMessage = "Address exceeds maximum length")] 
    string Address,
    [property: Required(ErrorMessage = "City required"), MaxLength(50, ErrorMessage = "City exceeds maximum length")]
    string City,
    [property: Required(ErrorMessage = "State required"), MaxLength(50, ErrorMessage = "State exceeds maximum length")]
    string State,
    [property: Required(ErrorMessage = "Zipcode required"), MaxLength(20, ErrorMessage = "Zipcode exceeds maximum length")] 
    string Zipcode,
    [property: Required(ErrorMessage = "Country required"), MaxLength(50, ErrorMessage = "Country exceeds maximum length")]
    string Country,
    [property: MaxLength(50, ErrorMessage = "Company exceeds maximum length")] 
    string? Company
);