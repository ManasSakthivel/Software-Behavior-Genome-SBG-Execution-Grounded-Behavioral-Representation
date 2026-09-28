#!/usr/bin/env python3
"""
driver_synthesizer.py
=====================
General-purpose driver synthesis for class-based and stateful programs.
"""
from __future__ import annotations

import ast
import inspect
import sys
import typing
from collections import namedtuple
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# Input batteries: same as experiments/final/protocol.py
INT_BATTERY = [0, 1, -1, 2, 10, 100, -100, 999, 1000000, -999999, 42]
FLOAT_BATTERY = [0.0, 1.0, -1.0, 0.5, 2.5, 100.0, -100.0, 3.14159, 1e6, 1e-6]
STR_BATTERY = ["", "a", "test", "x", "hello", "world", "foo", "bar", "data", "key", "value"]
BOOL_BATTERY = [True, False]
LIST_BATTERY = [[], [1], [1, 2], ["a"], ["x", "y"], [1, "a"], list(range(5))]
DICT_BATTERY = [{}, {"a": 1}, {"x": "y"}, {"key": "value"}, {1: 2, 3: 4}]

MethodCall = namedtuple("MethodCall", ["receiver_id", "method_name", "args", "arg_types", "result", "exception"])

@dataclass
class DriverSynthesisResult:
    """Outcome of attempting to synthesize a driver for one class."""
    class_name: str
    constructible: bool
    reason: str  # why unsupported, if not constructible
    instances: List[Any]  # successfully created instances
    method_calls: List[MethodCall]  # successfully executed calls
    unsupported_methods: Dict[str, str]  # method_name -> reason


def _infer_type_from_annotation(ann: Optional[typing.Any]) -> Optional[str]:
    """Map a type annotation to a battery key."""
    if ann is None:
        return None
    
    # Handle string annotations
    if isinstance(ann, str):
        ann_str = ann.lower()
        if "int" in ann_str:
            return "int"
        if "str" in ann_str or "string" in ann_str:
            return "str"
        if "float" in ann_str or "double" in ann_str:
            return "float"
        if "bool" in ann_str:
            return "bool"
        if "list" in ann_str or "sequence" in ann_str:
            return "list"
        if "dict" in ann_str or "mapping" in ann_str:
            return "dict"
        return None
    
    # Handle actual types
    origin = typing.get_origin(ann)
    if origin is not None:
        if origin in (list,):
            return "list"
        if origin in (dict,):
            return "dict"
        return None
    
    # Simple type
    if ann in (int, type(1)):
        return "int"
    if ann in (str, type("")):
        return "str"
    if ann in (float, type(1.0)):
        return "float"
    if ann in (bool, type(True)):
        return "bool"
    if ann in (list, type([])):
        return "list"
    if ann in (dict, type({})):
        return "dict"
    
    return None


def _infer_battery(arg_type: Optional[str]) -> List[Any]:
    """Return battery values for a type."""
    batteries = {
        "int": INT_BATTERY,
        "float": FLOAT_BATTERY,
        "str": STR_BATTERY,
        "bool": BOOL_BATTERY,
        "list": LIST_BATTERY,
        "dict": DICT_BATTERY,
    }
    return batteries.get(arg_type, [])


def synthesize_driver(
    module_path: str,
    class_name: str,
    max_instances: int = 3,
    max_calls_per_instance: int = 5,
) -> DriverSynthesisResult:
    """Attempt to synthesize a driver for a single class."""
    
    # Load the module
    spec = __import__("importlib.util").util.spec_from_file_location("target", module_path)
    if spec is None or spec.loader is None:
        return DriverSynthesisResult(
            class_name=class_name,
            constructible=False,
            reason="module_import_failed",
            instances=[],
            method_calls=[],
            unsupported_methods={},
        )
    
    try:
        module = __import__("importlib.util").util.module_from_spec(spec)
        sys.modules["target"] = module
        spec.loader.exec_module(module)
    except Exception as e:
        return DriverSynthesisResult(
            class_name=class_name,
            constructible=False,
            reason=f"module_execution_failed",
            instances=[],
            method_calls=[],
            unsupported_methods={},
        )
    
    # Get the class
    if not hasattr(module, class_name):
        return DriverSynthesisResult(
            class_name=class_name,
            constructible=False,
            reason="class_not_found",
            instances=[],
            method_calls=[],
            unsupported_methods={},
        )
    
    cls = getattr(module, class_name)
    if not inspect.isclass(cls):
        return DriverSynthesisResult(
            class_name=class_name,
            constructible=False,
            reason="not_a_class",
            instances=[],
            method_calls=[],
            unsupported_methods={},
        )
    
    # Try to construct instances
    instances: List[Any] = []
    try:
        sig = inspect.signature(cls.__init__)
        args = []
        
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            if param.default != inspect.Parameter.empty:
                continue
            if param.kind not in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            ):
                return DriverSynthesisResult(
                    class_name=class_name,
                    constructible=False,
                    reason="constructor_uses_varargs",
                    instances=[],
                    method_calls=[],
                    unsupported_methods={},
                )
            
            inferred = _infer_type_from_annotation(param.annotation)
            battery = _infer_battery(inferred)
            
            if not battery:
                return DriverSynthesisResult(
                    class_name=class_name,
                    constructible=False,
                    reason="constructor_arg_type_unknown",
                    instances=[],
                    method_calls=[],
                    unsupported_methods={},
                )
            
            args.append(battery[0])
        
        # Create instances
        for i in range(min(max_instances, 2)):
            try:
                instance = cls(*args)
                instances.append(instance)
            except Exception:
                if i == 0:
                    return DriverSynthesisResult(
                        class_name=class_name,
                        constructible=False,
                        reason="construction_execution_failed",
                        instances=[],
                        method_calls=[],
                        unsupported_methods={},
                    )
                break
    except Exception:
        return DriverSynthesisResult(
            class_name=class_name,
            constructible=False,
            reason="introspection_failed",
            instances=[],
            method_calls=[],
            unsupported_methods={},
        )
    
    if not instances:
        return DriverSynthesisResult(
            class_name=class_name,
            constructible=False,
            reason="no_instances_created",
            instances=[],
            method_calls=[],
            unsupported_methods={},
        )
    
    # Collect and call public methods
    unsupported_methods: Dict[str, str] = {}
    method_calls: List[MethodCall] = []
    
    for method_name in dir(instances[0]):
        if method_name.startswith("_"):
            continue
        
        try:
            method = getattr(instances[0], method_name)
            if not callable(method):
                continue
        except Exception:
            continue
        
        for instance_id, instance in enumerate(instances):
            if len(method_calls) >= len(instances) * max_calls_per_instance:
                break
            
            try:
                method_obj = getattr(instance, method_name)
                sig = inspect.signature(method_obj)
                
                call_args = []
                arg_types = []
                can_call = True
                
                for pname, param in sig.parameters.items():
                    if param.default != inspect.Parameter.empty:
                        continue
                    
                    inferred = _infer_type_from_annotation(param.annotation)
                    battery = _infer_battery(inferred)
                    
                    if not battery:
                        can_call = False
                        break
                    
                    call_args.append(battery[0])
                    arg_types.append(inferred or "unknown")
                
                if not can_call:
                    unsupported_methods[method_name] = "argument_type_unknown"
                    continue
                
                result = method_obj(*call_args)
                method_calls.append(MethodCall(
                    receiver_id=instance_id,
                    method_name=method_name,
                    args=call_args,
                    arg_types=arg_types,
                    result=result,
                    exception=None,
                ))
            
            except Exception as e:
                method_calls.append(MethodCall(
                    receiver_id=instance_id,
                    method_name=method_name,
                    args=call_args,
                    arg_types=arg_types,
                    result=None,
                    exception=type(e).__name__,
                ))
    
    return DriverSynthesisResult(
        class_name=class_name,
        constructible=True,
        reason="",
        instances=instances,
        method_calls=method_calls,
        unsupported_methods=unsupported_methods,
    )


def find_public_classes(module_path: str) -> List[str]:
    """Find all public classes in a module."""
    try:
        with open(module_path) as f:
            tree = ast.parse(f.read())
    except Exception:
        return []
    
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            classes.append(node.name)
    
    return classes
