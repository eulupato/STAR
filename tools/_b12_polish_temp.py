from pathlib import Path

self_path = Path('core/self_model.py')
text = self_path.read_text(encoding='utf-8')
old = '''                namespaces.append({
                    "namespace": key,
                    "logical_capacity": item.get("logical_capacity"),
                    "materialized": True,
                })'''
new = '''                namespaces.append({
                    "namespace": key,
                    "logical_capacity": item.get("logical_capacity"),
                    "registered": True,
                })'''
if old not in text:
    raise SystemExit('knowledge namespace marker not found')
text = text.replace(old, new, 1)
old_exc = '''        except Exception as exc:  # representation must fail closed, not grant network
            return {"status": "unknown", "enabled": None, "source": f"network provider error: {type(exc).__name__}"}'''
new_exc = '''        except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
            return {"status": "unknown", "enabled": None, "source": f"network provider error: {type(exc).__name__}"}'''
if old_exc not in text:
    raise SystemExit('network exception marker not found')
text = text.replace(old_exc, new_exc, 1)
self_path.write_text(text, encoding='utf-8')

test_path = Path('tests/test_self_model.py')
test = test_path.read_text(encoding='utf-8')
marker = '''    resources = block.resources_snapshot()
    assert resources["hardware_telemetry"] == "unknown"
    assert block.uncertainties_snapshot()
'''
replacement = marker + '''    knowledge = block.knowledge_snapshot()
    assert knowledge["registered_namespaces"]
    assert all(item["registered"] is True for item in knowledge["registered_namespaces"])
    assert all("materialized" not in item for item in knowledge["registered_namespaces"])
'''
if marker not in test:
    raise SystemExit('self model test marker not found')
test = test.replace(marker, replacement, 1)
test_path.write_text(test, encoding='utf-8')
