This document outlines the architectural approach and technical decisions for addressing a bug related to ASO CRD duplication within the OpenShift `cluster-api` repository.

## Design Document: Fix ASO CRD Duplication in `verify-capi-manifests.sh`

### 1. Executive Summary

This design document details the fix for a bug in the `hack/verify-capi-manifests