# CUSTOMER IDENTITY AND ACCESS SPEC

## Goal
Define how customers are linked to their business and website, and how they safely log in to their own portal.

## Core Model
Every customer account is linked to:
- one business
- optionally a draft site
- optionally an active site
- package/access metadata

## MVP Login Recommendation
- login by phone number
- unique temporary password per customer account
- first login must require password change
- later roadmap: OTP / magic link / Google login

## Why not a shared default password?
A shared password such as 1234 for all customers is not acceptable for privacy and security.
Use unique temporary passwords instead.

## Required Fields
- customer_account_id
- business_id
- phone
- optional email
- optional contact name
- active_site_id / draft_site_id
- password_hash
- must_change_password
- is_active
- package_name

## Customer Visibility Rules
Customers may only see:
- their own business/site/account data
- limited package and billing view
- their own support/change requests

Customers may not see:
- internal admin notes
- other businesses or customers
- internal CEO recommendations
- internal lead scoring or strategy notes
