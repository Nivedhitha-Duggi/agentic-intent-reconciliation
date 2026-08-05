# Architecture

The YAML files are the project source inputs. `desired.yaml` is authoritative intent; `current.yaml` represents deployed state.

Supported chain:

```text
DeviceMF -> DeviceConfigMF -> Uplink -> Fiber -> ONT
```

Creation uses forward order. Deletion uses reverse order. Modification preserves the resource identity and replaces only the intended attributes.

The real-agent layer never invents operations. It explains and coordinates operations already produced by deterministic comparison and dependency logic.
