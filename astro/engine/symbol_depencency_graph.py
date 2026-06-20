import json
import os
from typing import Dict,Any,Optional

class Symbol_Dependency_Graph:
    
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.metadata_path = os.path.join(workspace_root, ".astro", "files_metadata.json")
        self.output_path = os.path.join(workspace_root, ".astro", "symbol_graph.astro") 
          
        self.metadata_data: Dict[str,Any] = {}
        self.file_graph: Dict[str,list[str]] = {}
    
        self.local_def: Dict[str,list[Dict[str,Any]]] = {}
        self.symbol: Dict[str,Dict[str,Any]] = {}
        
        self.graph = {
            "nodes": [],
            "edges": []
        }
        
        
    def run(self) -> None:
        self._load_metadata()
        
        
    def _load_metadata(self) -> None:
        if not os.path.exists(self.metadata_path):
            raise FileNotFoundError(f"Parser metadata missing. Run Parser Engine first. Path: {self.metadata_path}")            
        with open(self.metadata_path,"r", encoding="utf-8") as f:
            self.metadata_data = json.load(f)
        
    #actual functions
    #   PART-1:
    def _build_global_definition(self) -> None:
        """
        Scans all files to register declared classes, functions, methods, and
        global state variables into a global indexed namespace registry.
        """
        for file_path, file_meta in self.metadata_data.items():
            self.local_definitions[file_path] = []
            # Extract Classes and their internal methods
            for class_meta in file_meta.get("classes", []):
                class_name = class_meta["name"]
                class_fqn = self._generate_fqn(file_path, class_name)
                
                class_node = {
                    "id": class_fqn,
                    "name": class_name,
                    "kind": "CLASS",
                    "file": file_path,
                    "meta": class_meta
                }
                self.global_symbol_index[class_fqn] = class_node
                self.graph["nodes"].append(class_node)
                self.local_definitions[file_path].append(class_node)
                
                # Register class methods
                for method in class_meta.get("methods", []):
                    method_name = method["name"]
                    method_path = f"{class_name}.{method_name}"
                    method_fqn = self._generate_fqn(file_path, method_path)
                    
                    method_node = {
                        "id": method_fqn,
                        "name": method_name,
                        "kind": "METHOD",
                        "file": file_path,
                        "meta": method
                    }
                    self.global_symbol_index[method_fqn] = method_node
                    self.graph["nodes"].append(method_node)
                    self.local_definitions[file_path].append(method_node)
                    
                    # This will define the edges
                    self.graph["edges"].append({
                        "source": class_fqn,
                        "target": method_fqn,
                        "type": "DEFINES"
                    })

            # Extracing Global Independent Functions
            for func_meta in file_meta.get("functions", []):
                func_name = func_meta["name"]
                func_fqn = self._generate_fqn(file_path, func_name)
                
                func_node = {
                    "id": func_fqn,
                    "name": func_name,
                    "kind": "FUNCTION",
                    "file": file_path,
                    "meta": func_meta
                }
                self.global_symbol_index[func_fqn] = func_node
                self.graph["nodes"].append(func_node)
                self.local_definitions[file_path].append(func_node)

            # Extracting Global State Variables / Constants
            for var_meta in file_meta.get("global_variables", []):
                var_name = var_meta["name"]
                var_fqn = self._generate_fqn(file_path, var_name)
                
                var_node = {
                    "id": var_fqn,
                    "name": var_name,
                    "kind": "GLOBAL_VARIABLE",
                    "file": file_path,
                    "meta": var_meta
                }
                self.global_symbol_index[var_fqn] = var_node
                self.graph["nodes"].append(var_node)
                self.local_definitions[file_path].append(var_node)

    
    
    
    
    
    
    
     
        
    def _save_graph(self) -> None:
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)        
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(self.graph, f, indent=2)
        print(f"Indexed {len(self.graph['nodes'])} symbol nodes.")
        print(f"Mapped {len(self.graph['edges'])} structural symbol relationships.")
        print(f"Symbol Dependency Graph saved to: {self.output_path}")
        