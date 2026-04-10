# ADR 10360: Skip Redirects for AWS Endpoint Validation

## Status
Accepted

## Date
2023-10-27 (or current date of generation)

## Context

The OpenShift installer validates the reachability of user-provided service endpoint URLs by performing HTTP HEAD requests. A critical issue has been identified where certain AWS service endpoints, such as `https://sts.ap-southeast-1.amazonaws.com`, respond with an HTTP `302 Found` status, redirecting to AWS documentation URLs like `https://aws.amazon.com/iam`.

