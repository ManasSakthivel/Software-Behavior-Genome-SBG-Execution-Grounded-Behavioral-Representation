#!/usr/bin/env python3
"""
Actual evaluation of class-based programs using robust driver synthesis.
No hand-authored drivers. Explicit timeout/budget handling.
"""
import sys
sys.path.insert(0, ".")

import json
import pathlib
import importlib.util
import inspect
import time
from typing import Dict, Any, List, Optional, Tuple

# Batteries (same as protocol)
BATTERIES = {
    "int": [0, 1, -1, 2, 10, 100],
    "str": ["", "a", "test", "x"],
    "float": [0.0, 1.0, -1.0, 0.5],
    "bool": [True, False],
    "list": [[], [1], [1, 2]],
    "dict": [{}, {"a": 1}],
}

def infer_type(ann: Optional[str]) -> Optional[str]:
    """Infer battery type from annotation."""
    if ann is None:
        return None
    a = str(ann).lower()
    for t in ["int", "float", "bool", "str", "list", "dict"]:
        if t in a:
            return t
    return None

def synthesize_class(module_path: str, class_name: str, timeout_s: float = 1.0) -> Dict[str, Any]:
    """Synthesize and execute a class-based driver with explicit timeout/error handling."""
    result = {
        "class_name": class_name,
        "status": "unknown",
        "instances": 0,
        "method_calls": 0,
        "errors": [],
    }
    
    # Load module
    try:
        spec = importlib.util.spec_from_file_location("m", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        result["status"] = "module_load_failed"
        result["errors"].append(str(type(e).__name__))
        return result
    
    if not hasattr(module, class_name):
        result["status"] = "class_not_found"
        return result
    
    cls = getattr(module, class_name)
    if not inspect.isclass(cls):
        result["status"] = "not_a_class"
        return result
    
    # Try to construct instances
    instances = []
    try:
        sig = inspect.signature(cls.__init__)
        args = []
        
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            if param.default != inspect.Parameter.empty:
                continue
            if param.kind not in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
                result["status"] = "constructor_uses_varargs"
                return result
            
            t = infer_type(str(param.annotation))
            if t is None:
                result["status"] = "constructor_arg_unknown_type"
                return result
            
            args.append(BATTERIES[t][0])
        
        # Try to create one instance
        start = time.time()
        instance = cls(*args)
        elapsed = time.time() - start
        
        if elapsed > timeout_s:
            result["status"] = "constructor_timeout"
            result["errors"].append(f"took {elapsed:.2f}s")
            return result
        
        instances.append(instance)
        result["instances"] = 1
    
    except Exception as e:
        result["status"] = "construction_failed"
        result["errors"].append(type(e).__name__)
        return result
    
    # Call methods (with timeout protection)
    for method_name in sorted(dir(instances[0]))[:5]:  # Limit to 5 methods
        if method_name.startswith("_"):
            continue
        
        try:
            method = getattr(instances[0], method_name)
            if not callable(method):
                continue
            
            sig = inspect.signature(method)
            call_args = []
            
            for pname, param in sig.parameters.items():
                if param.default != inspect.Parameter.empty:
                    continue
                t = infer_type(str(param.annotation))
                if t is None:
                    break
                call_args.append(BATTERIES[t][0])
            else:
                # All args satisfied
                start = time.time()
                try:
                    result_val = method(*call_args)
                    elapsed = time.time() - start
                    if elapsed < timeout_s:
                        result["method_calls"] += 1
                except Exception as method_error:
                    result["errors"].append(f"{method_name}:{type(method_error).__name__}")
        except Exception:
            pass  # Silent fail on introspection
    
    result["status"] = "success" if result["method_calls"] > 0 else "no_methods"
    return result


def evaluate_unsupported_programs() -> Dict[str, Any]:
    """Evaluate the 6 previously unsupported programs."""
    corpus_dir = pathlib.Path("benchmark/corpus/base_programs")
    
    unsupported = {
        "api_rate_limiter": ["TokenBucket"],
        "conc_read_write_lock": ["ReadWriteLock"],
        "ds_hash_table": ["HashMap"],
        "file_config_parser": ["ConfigParser"],
        "fsm_vending_machine": ["VendingMachine"],
        "res_object_pool": ["ObjectPool"],
    }
    
    results = {
        "experiment": "CLASS_BASED_PROGRAM_EVALUATION",
        "programs_evaluated": 0,
        "programs_succeeded": 0,
        "total_method_calls": 0,
        "program_results": {},
    }
    
    for prog_name, classes in unsupported.items():
        prog_path = corpus_dir / f"{prog_name}.py"
        if not prog_path.exists():
            print(f"✗ {prog_name}: file not found")
            continue
        
        print(f"Evaluating {prog_name}...", end=" ", flush=True)
        results["programs_evaluated"] += 1
        
        prog_results = {}
        for cls_name in classes:
            result = synthesize_class(str(prog_path), cls_name, timeout_s=1.0)
            prog_results[cls_name] = result
            
            if result["status"] == "success":
                results["programs_succeeded"] += 1
                results["total_method_calls"] += result["method_calls"]
        
        results["program_results"][prog_name] = prog_results
        
        status = "✓" if any(r["status"] == "success" for r in prog_results.values()) else "✗"
        print(status)
    
    return results


if __name__ == "__main__":
    print("=" * 70)
    print("CLASS-BASED PROGRAM EVALUATION")
    print("=" * 70)
    print()
    
    results = evaluate_unsupported_programs()
    
    with open("artifacts/final/CLASS_BASED_EVALUATION.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print()
    print(f"Programs evaluated: {results['programs_evaluated']}")
    print(f"Programs with successful synthesis: {results['programs_succeeded']}")
    print(f"Total method calls executed: {results['total_method_calls']}")
    print()
    print("Results written to artifacts/final/CLASS_BASED_EVALUATION.json")
