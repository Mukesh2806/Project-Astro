astro-cli/
│
├── astro/                  # Main core application package
│   ├── __init__.py
│   │
│   ├── cli.py              # Entrypoint: Handles CLI arguments and user commands
│   │
│   ├── parser/             # THE PARSER LAYER (Tree-sitter)
│   │   ├── __init__.py
│   │   └── code_parser.py  # Reads files, extracts functions, variables, & imports
│   │
│   ├── engine/             # THE MAP LAYER (NetworkX)
│   │   ├── __init__.py
│   │   └── graph_engine.py # Builds Directed Graphs, tracks ripple effects/blast radius
│   │
│   └── ai/                 # THE CONTEXT LAYER (Ollama)
│       ├── __init__.py
│       └── ai_client.py    # Pipes the affected code to the local LLM for fixes
│
├── tests/                  # Test suite for validating your logic
│   ├── sample_code/        # Tiny dummy code files to let Astro run tests on
│   │   ├── file_a.py
│   │   └── file_b.py
│   └── test_engine.py
│
├── requirements.txt        # Your Python dependencies
├── README.md               # Clean, beautiful technical documentation
└── main.py                 # Absolute root execution file

Branching-
main
 │
 └── dev
      │
      ├── feat/tree-sitter-parser
      ├── feat/symbol-extraction
      ├── feat/call-graph
      ├── feat/impact-engine
      └── feat/ai-layer

git checkout dev
git pull

git checkout -b feat/tree-sitter-parser