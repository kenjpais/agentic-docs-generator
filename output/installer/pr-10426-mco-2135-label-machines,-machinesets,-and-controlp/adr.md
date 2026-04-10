# Architecture Decision Record (ADR)

## Context and Problem Statement

With https://redhat.atlassian.net/browse/MCO-2133, the installer will become aware of the boot image being selected for each machine resource. This boot image information should be placed as a label/annotation on every machine and machineset resource so that the Machine Config Operator (