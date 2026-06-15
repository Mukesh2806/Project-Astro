## Version Scope

This document describes the architecture of Astro V1.

Supported Analysis Layers:

- Syntax & Grammar Errors
- Codebase Integrity Issues
- Environment & Compatibility Issues

Future layers such as Runtime Contract Analysis and Business Logic Analysis are outside the scope of V1.

### Astro Architecture

## Overview

Astro is defined as a multi-layer software intelligence engine that analyzes source code from multiple perspectives, including syntax, structural integrity, runtime contracts, business logic risks and deployment readiness

# High-Level Architecture

Project Source Code 
        |
        ▼
Project Scanner  ───► Filters paths & finds valid files
           │
           ▼
    Parser Engine    ───► Validates Layer 1 Syntax & extracts raw strings
           │
           ▼
    Graph Engine     ───► Resolves strings to absolute paths & links modules
           │
           ▼
 Configuration Analyzer ──► Cross-references Graph keys with requirements.txt
           │
           ▼
  Integrity Analyzer ───► Runs Cycle (DFS) & Dead Code algorithms on the Graph
           │
           ▼
   Report Generator  ───► Flattens all findings into a clean CLI output terminal



## Core Components

# Project Scanner

Responsibilities -

- Discover project files
- filtering unwanted files and directories

Inputs -

- Source Code directory

Output -

- List of files and directories

# Parser Engine

Responsibilities - 

- parse source code
- Generate syntax trees
- extract meaningful symbols and metadata

Input -

- source files

Output -

- AST structures
- Symbol metadata
- Import metadata

# Configuration Analyzer

Responsibilities -

- validate project environment
- check dependency consistency
- detect deployment risks

Inputs -

- requirements.txt
- lockfiles
- project metadata

Outputs - 

- environment warnings

# Graph Engine

Responsibilities -

- Build dependency network
- Track imports and refs
- construct project relationship graph

Inputs -

- AST graph

Outputs ->

- Dependency Graph

# Integrity Analyzer

Responsibilities - 

- Detect circular dependencies
- Detect broken import
- Detect broken codebase integrity

Inputs -

- Dependency Graph

Outputs -

- Integrity findings

# Report Generator 

Responsibilities -

- Aggregate findings
- prioritize risks
- Generate final analysis reports

Outputs -

- Integrity reports
- Compatibility report
- Risk summary

## Design Principle

- Modular Architecture
- Layered verification
- Extensible plugin system
- Environment-aware analysis

## Current Status

This architecture represents the intended design and may evolve as research and implementation progress.


### Graph Engine Architecture


## Layer 1 — File Dependency Graph

### Purpose

Represents relationships between files/modules in the codebase.

### Nodes

* Files
* Modules

### Edges

* `IMPORTS`
* `DEPENDS_ON`

### Example

```
auth_service.py ──imports──► manager.py
```

### Responsibilities

* Dependency tracking
* Impact analysis at file level
* Incremental graph updates
* Circular dependency detection
* Project structure visualization

### Questions Answered

* Which files depend on this file?
* What files will be affected if this file changes?
* Which files import this module?
* Are there circular dependencies?

### Value

Acts as a coarse-grained filtering layer, reducing the search space before deeper semantic analysis.

---

## Layer 2 — Symbol Dependency Graph

### Purpose

Represents relationships between code symbols inside files.

### Nodes

* Functions
* Classes
* Methods
* Global variables
* Constants

### Edges

* `CALLS`
* `INHERITS`
* `USES`
* `RETURNS`
* `ACCESSES`
* `DEFINES`

### Example

```
verify_token ──calls──► find_workspace_root
```

### Responsibilities

* Symbol usage tracking
* Call graph generation
* API breakage analysis
* Dead code detection
* Cross-reference generation

### Questions Answered

* Who calls this function?
* Where is this class used?
* What breaks if this API changes?
* Which functions depend on this symbol?

### Value

Provides semantic understanding of how code components interact.

---

## Layer 3 — Unified Semantic Graph

### Purpose

Combines file-level and symbol-level relationships into a single traversable graph.

### Nodes

* Files
* Modules
* Functions
* Classes
* Methods
* Variables

### Edges

* All Layer 1 edges
* All Layer 2 edges
* Cross-layer ownership edges

### Example

```
auth_service.py
     │
     ▼
verify_token
     │
     ▼
find_workspace_root
     │
     ▼
manager.py
```

### Responsibilities

* End-to-end impact analysis
* Semantic code navigation
* Dependency tracing
* Architectural reasoning
* Intelligent code understanding

### Questions Answered

* If this function changes, what files are affected?
* Why does this file depend on another file?
* What is the complete dependency chain?
* What is the shortest path between two symbols?

### Value

Transforms Astro from a dependency tracker into a semantic code intelligence engine capable of reasoning across the entire codebase.
