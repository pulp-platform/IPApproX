In order to pull certain IPs, ame the following file `ips_list.yml` and put it into the root directory of your project.

```YAML
# Clone project apb_node into folder apb
apb/apb_node:
  commit: master

# Fix to a certain commit
apb/apb_event_unit:
  commit: 63308047

# Clone from different group or username
rocket-chip-eth:
  group: groupname/username
  commit: master

# Specifiy alternatives
riscv:
  commit: master
  alternatives: [or10n,riscv,rocket-chip-eth]

# Add domain example

```

