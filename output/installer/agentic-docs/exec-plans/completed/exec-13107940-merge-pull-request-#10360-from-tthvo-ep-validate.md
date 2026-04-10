# OCPBUGS-77830: Skip redirect when validating endpoint accessibility

## Feature Title
OCPBUGS-77830: Skip redirect when validating endpoint accessibility

## Problem Statement
The OpenShift installer performs HTTP HEAD requests to validate the reachability of user-provided AWS service endpoint URLs. A critical issue arises in disconnected environments where certain AWS endpoints (