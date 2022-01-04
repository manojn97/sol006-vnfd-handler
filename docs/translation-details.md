# Translation Rules

The driver for the translation is the input package - see resources/input/packages/example.  The package has a single file under the Definitions folder - in the example it is called vnfd.yaml - it could be called by any name.  It will be a yaml file.
Alongside the Definitions folder there will be a Files folder that should contain a folder for each vdu in the package, the folders will be called using the same name as the id of the VDU in the yaml file.

The aim is to create a single CP4NA package where there is an assembly that represents the VNF and for each VDU there will be a resource package.  These resource packages will be 'Contains' within the Assembly package.

# Assembly Construction

The Assembly yaml file is placed in a Descriptor folder of the assembly package.  The assembly will have 3 sections: `properties`, `composition`, and possibly `operations`.

## `properties`

The properties of the assembly are derived from two places - `configurable-properties` and `ext-cpd`.

*configurable-properties*

  Configurable properties is a list of property names followed by a value. The value is likely to contain a string wrapped in angled brackets, e.g. `<admin-password>`.  

```yaml
  configurable-properties:
    availability_zone: <availability_zone> 
    system_image: "image_name.qcow"
    system_flavor: <system_flavor>   
    admin_password: <admin_password>
    root_password: <root_password>
    license: <license>          
    default_gateway: <default_gateway>   
    system_vm_instance_name: <vdu1.vm_instance_name>
```

For each property in the `configurable-properties` section a top level assembly property should be created.  If the name contains a value without the brackets the assembly property will be defined as follows:

```yaml
   system_image:
     value: "image_name.qcow"
```

Where the property value uses angled brackets the property will become:

```yaml
   system_flavor:
      type: "string"
```

Except where the value in the angled brackets contains the id of a vdu in the format `<vdu-id.property_name>`  In this case the property will become:

```yaml
   system_vm_instance_name:
      value: ${vdu-id.vdu1.vm_instance_name}
```
In other words the angled brackets are replaced by the `${...}` format.

*ext-cpd*

Ext-cpd standads for external connection point descriptors.  These are the interfaces of the vnfd that will be attached to networks.  The assumption for these is that in the assembly they will create two properties, one that represents the network being attached to the ext-cpd and one which will be set by the vdu to be the ip address of the ext-cpd.

```yaml
  ext-cpd:
  - id: vnf-mgmt-ext
    int-cpd:
      cpd: vdu-eth0-int
      vdu-id: vdu1
  - id: vnf-internal-ext
    int-cpd:
      cpd: vdu-eth1-int
      vdu-id: vdu1
  - id: vnf-ha-ext
    int-cpd:
      cpd: vdu-eth0-int
      vdu-id: vdu2
```

Taking the first cpd in this list - `vnf-mgmt-ext` would generate the following two properties:

```yaml
  vnf-mgmt-ext-vl:
    type: string
    description: Network for cpd vnf-mgmt-ext ext-cpd
  vnf-mgmt-ext-ipaddress:
    type: string
    description: Ip Address for cpd vnf-mgmt-ext ext-cpd
    read-only: true
    value: ${vdu1.vdu-eth0-int-ipaddress}
```

The first property is where the network name is passed in and the second is the ip-address being passed from the vdu.  **NOTE:** the vdu property in the value is derived from the internal cpd that is referenced.


## `composition`

The composition section of an assembly describes the resources or assemblies that make up the assembly.  Composition entries will usually result in the orchestrator creating virtual resources in a VIM.

For the translation there would be one composition entry per vdu in the vnfd.

```yaml
composition:
  vdu1:
    type: $lmctl:/contains:/vdu1:/descriptor_name
    meta-type: vdu
    ...
    properties:
      ...
```

This will come mainly from the vdu section:

```yaml
  vdu:
  - id: vdu1
    name: A VDU
    version: 1.0  
    description: a VDU       
    configurable-properties:
      availability_zone: <vnf1.availability_zone>
      stack_name: <instance.name>
      id: <instance.id>
      index: <instance.index>
      ...           
      vm_instance_name: <read-only>                           
    int-cpd:
      ...
    virtual-compute-desc: small-compute
    virtual-storage-desc:
    - main-storage
    - backup-storage
    sw-image-desc: system-image
```

The composition entry is labelled using the id of the vdu.  The type is defined in this way as the resource it is referring to is going to be packaged inside the assembly.  This name is used by `lmctl` to define the name based on the hierarchy in the package.

There will normally be either a `quantity` field or a `cluster` section.  How to derive this will be defined later.

`properties` are derived from the `configurable-properties` section of the vdu definition.  The rules are as follows:

`availability_zone: <vnf1.availability_zone>` will become:

```yaml
    availability_zone:
       type: string
```

`vm_instance_name: <read-only>` will become:

```yaml
    vm_instance_name:
       read-only: true
```

`property: "property value"` will become:

```yaml
    property:
       value: "property value"
```
Any property with a mapping that starts with `instance.`

```yaml
    stack_name: <instance.name>
    id: <instance.id>
    index: <instance.index>
```
 will not be included in the composition properties but will become value properties of the resource - see Resource properties

The int-cpd will create two fields in a similar manner to the ext-cpd, one for the network and one for an ip-address.

```yaml
    int-cpd:
    - id: vdu-eth0-int
      virtual-network-interface-requirement:
      - name: vdu-eth0
        position: 0
    - id: vdu-eth1-int
      virtual-network-interface-requirement:
      - name: vdu-eth1
        position: 1
```

will become:

```yaml
      vdu-eth0-int-ipaddress:
        type: string
        description: Ip Address for cpd vnf-mgmt-ext int-cpd
        read-only: true
      vdu-eth0-int-vl:
        type: string
        description: Network for cpd vnf-mgmt-ext int-cpd
        value: ${vnf-mgmt-ext-vl}
      vdu-eth1-int-ipaddress:
        type: string
        description: Ip Address for cpd vnf-internal-ext int-cpd
        read-only: true
      vdu-eth1-int-vl:
        type: string
        description: Network for cpd vnf-internal-ext int-cpd
        value: ${vnf-internal-ext-vl}
```

**NOTE:** the mapping is from the external cpd property name created at the top of the assembly.

### Deployment Locations

For a resource to be deployed it must be associated with deployment_location.  The translation tool will need to provide an cli option to help define the values for the deployment locations of the VDU in the package.  The default is that all vdus wil be deployed in the same deployment location.

When all vdus will be deployed in the same deployment location the following property need to be added to the assembly top-level properties:

```yaml
  deployment_location:
    type: string
```

Then for each vdu in the composition section a property will need to be added in the format:

```yaml
      deployment_location:
        value: ${deployment_location}
```

When the cli option is to have a deployment location per vdu the properties will be ass follow, for the top-level assembly:

```yaml
  vdu1_deployment_location:
    type: string
  vdu2_deployment_location:
    type: string
```

where `vdu1` and `vdu2` are the ids of the vdus in the vnfd.  The composition properties per vdu will be as follows:

```yaml
      deployment_location:
        value: ${vdu1_deployment_location}
```

Where `vdu1` is the id of the vdu in question.

### `quantity` or `cluster`

To determine the quantity or cluster section of the composition requires quite a lot of logic.  The values for this are mainly in the deployment flavour section of the vnfd called `df:`

```yaml
  df:
  - id: default-df
    instantiation-level:
    - id: single
      vdu-level:
      - number-of-instances: 1
        vdu-id: vdu1  
      - number-of-instances: 1
        vdu-id: vdu2              
      scaling-info:
      - scaling-aspect-id: cluster     
    vdu-profile:
    - id: vdu1
      min-number-of-instances: 1 
    - id: vdu2
      min-number-of-instances: 1              
    default-instantiation-level: single
    scaling-aspect:
    - id: cluster
      name: cluster
      description: a description
      max-scale-level: 2
      aspect-delta-details:
        deltas:
        - id: first
          vdu-delta: 
          - id: vdu2
            number-of-instances: 1  
```

For this release we are only supporting a single `df:` entry.  It will have an `id` , single `instantiation-level` an dif there is to be a cluster defined it should have a `scaling-aspect` defined.

Start by gathering the `min-number-of instances:` per vdu from the vdu profile.

Then get the `number-of-instances` from the `instantiation-level` per vdu.

In the `instantiation-level` there may be a 'scaling-info' field that points at a particular 'scaling-aspect'.  If there is this will define some details about the scaling of the vdu(s).  The scaling aspect may have a field called `max-scale-level` this will be used to derive the max size of the cluster.  Finally we need to see which vdu is t be scaled.  This is referenced in the deltas section of the scaling aspect.  We will only be supporting a single delta in this release. The vdu referenced will have a cluster section.  The `number-of-instances` in the delta indicates how many instances will be created every time a scale request is made.

The following is the rules for the quantity and cluster assuming all the above field have been collected per vdu (where they exist).

Where a vdu is not referenced in a `scaling-aspect` it will have a `quantity` field.  The value in the field will be the value of the `number-of-instances:` field in the instantiation-level. If no such field exists then the vdu is not expected to be instantiated and therefore no composition for the vdu should be included in the assembly.  If the `vdu-profile` `min-number-of-instances` is greater than the `instantiation-level` `number-of-instances` then the `min-number-of-instances` will be used for the `quantity` field.

```yaml
  vdu1:
    type: $lmctl:/contains:/vdu1:/descriptor_name
    meta-type: vdu
    quatity: 1
```

When a scaling aspect is defined and references a vdu, the composition section will have a cluster section instead of a quantity field.

```yaml
  vdu2:
    type: $lmctl:/contains:/vdu2:/descriptor_name
    meta-type: vdu
    cluster:
      initial-quantity: 1
      minimum-nodes: 1
      maximum-nodes: 3
      scaling-increment: 1
```

`initial-quantity` will default to `1` if the `min-number-of-instances` or the `instantiation-level` `number-of-instances` is missing. (There should be at least the `instantiation-level` `number-of-instances` in the document).

`minimum-nodes` will be set to the `number-of-instances` in the `instatiation-level` or 1 is that is missing.

`maximum-nodes` is set to either the `scaling-aspects` `max-scale-level` multiplied by the `vdu-delta` `number-of-instances`.

`scaling-increment` is the `number-of-instances` in the `vdu-delta` section.

## `operations`

An assembly may promote operations from any of the resources or assemblies in the composition section.

Within the vnfd there is a section that may have entries as follows:

```yaml
  lifecycle-management-script:
  - id: vdu1.AddRule  
    event: external-lifecycle-management-script-event   
    lcm-transition-event: AddRule
    script-input:
      system_policy_name:
        description: name of system policy 
        type: string
        default: system_policy
      ...
```

This defines an operation.  Most of the information is included here will be used when generating the associated resource descriptors.  For assemblies this would be transformed into:

```yaml
operations:
  AddRule:
    source-operation: vdu1.AddRule
```

# Package Transformation

Given a package of the format:

```bash
.
└── vnf1
    ├── Definitions
    │   └── vnfd.yaml
    └── Files
        ├── vdu1
        │   └── Lifecycle
        └── vdu2
            └── Lifecycle
```

This would be transformed into the following package format:

```bash
.
└── vnf1
    ├── Contains
    │   ├── vdu1
    │   │   ├── Definitions
    │   │   │   └── lm
    │   │   └── Lifecycle
    │   └── vdu2
    │       ├── Definitions
    │       └── Lifecycle
    ├── Descriptor
    │   └── assembly.yaml
    └── lmproject.yml
```

1. The main package has a Descriptor folder and an `lmproject.yml` that is used by `lmctl` to transfer the package to the CP4NA server
1. Each vdu will result in a child resource package that will be contained in the assembly package using the `Contains` structure
1. Each vdu will have a Definitions/lm folder that will contain the resource.yaml file for the contained resource
1. The contents of the Lifecycle directories are copoied with not changes applied?
1. The lmproject.yml files will have a similar format to the following:

```yaml
contains:
- directory: vdu1
  type: Resource
  resource-manager: brent
  name: vdu1
- directory: vdu2
  type: Resource
  resource-manager: brent
  name: vdu2
schema: 2.0
version: '1.0'
type: Assembly
name: vnf1
```

# Resource Creation

For each vdu a `resource.yaml` file will have to be created.  This will have the following sections:

```yaml
name: resource::vdu1-vnf1::1.0
meta-type: VDU
description: 'A VDU: a VDU'
properties:
   ...
lifecycle:
   ...
operations:
   ...
```

The name of the resource will be a combination of the vdu id and the vnfd-id.

## `properties`

There are 3 sets of properties that need to be considered.

1. `configurable-properties`
1. `int-cpd` network properties
1. `...desc` based properties


### `configurable-properties`

Within the vdu there should be a set of properties defined.  These like the assembly properties will have mappings in angle brackets.  The following transformations need to happen:

```yaml
    configurable-properties:
      availability_zone: <vnf1.availability_zone>
      stack_name: <instance.name>
      id: <instance.id>
      index: <instance.index>
      ...           
      vm_instance_name: <read-only>  
```

becomes: 

```yaml
properties:
  availability_zone:
    type: string
    value: ${vnf1.availability_zone}
  stack_name:
    type: string
    value: ${instance.name}    
  id:
    value: ${instance.id}
  index:
    value: ${instance.index}
  ...
  vm_instance_name:
    read-only: true
```

### `int-cpd` network properties

Like the ext-cpd, there will need to be properties created for the Internal CPs.  The following:

```yaml
    int-cpd:
    - id: vdu-eth0-int
      virtual-network-interface-requirement:
      - name: vdu-eth0
        position: 0
    - id: vdu-eth1-int
      virtual-network-interface-requirement:
      - name: vdu-eth1
        position: 1
```

Would result in the following set of properties being added to the resource file:

```yaml
  vdu-eth0-int-ipaddress:
    type: string
    description: Ip Address for cpd vnf-mgmt-ext int-cpd
    read-only: true
  vdu-eth0-int-vl:
    type: string
    description: Network for cpd vnf-mgmt-ext int-cpd
  vdu-eth1-int-ipaddress:
    type: string
    description: Ip Address for cpd vnf-internal-ext int-cpd
    read-only: true
  vdu-eth1-int-vl:
    type: string
    description: Network for cpd vnf-internal-ext int-cpd
```

### `...desc` based properties

The final set of properties are a way to pass into the resource.yaml details of the compute and storage that have been defined in the vnfd/vdu definitions.  In the vdu there are leaf references to the following `desc'` sections:

```yaml
    virtual-compute-desc: small-compute
    virtual-storage-desc:
    - main-storage
    - backup-storage
    sw-image-desc: system-image
```

These refer to the identified sections within the vnfd.  In the example these are:

```yaml
  virtual-compute-desc:
  - id: small-compute
    virtual-cpu:
      num-virtual-cpu: 1
    virtual-memory:
      size: "2.0"
  - id: medium-compute
    virtual-cpu:
      num-virtual-cpu: 4
    virtual-memory:
      size: "16.0"      
  virtual-storage-desc:
  - id: main-storage
    type-of-storage: BLOCK
    block-storage-data:
      size-of-storage: 10
  - id: backup-storage
    type-of-storage: BLOCK
    block-storage-data:
      size-of-storage: 20    
  sw-image-desc:
  - id: system-image
    name: The Image
    ...
```

For the first two sections a property will be created that contains the details of the section used by the vdu.  This would result in the following properties being created in the resource.yaml file:

```yaml
  vdu-compute-desc:
    type: map
    value:
      id: small-compute
      virtual-cpu:
        num-virtual-cpu: 1
      virtual-memory:
        size: '2.0'
  vdu-storage-desc:
    type: list
    value:
    - id: main-storage
      type-of-storage: BLOCK
      block-storage-data:
        size-of-storage: 10
    - id: backup-storage
      type-of-storage: BLOCK
      block-storage-data:
        size-of-storage: 20
```

This is merely copying the contents in to a `value:` section and defining the type as map or list.  Even if storage only had one item it should be defined as a list.


### Lifecycle
To determine what goes into the section we will need to look at the files in the resources `Lifecycle` directory of the resource.  

```bash
 └── vdu1
    └── Lifecycle
        ├── Openstack
        │   └── heat.yml
        └── ansible
            ├── config
            │   ├── host_vars
            │   └── inventory
            └── scripts
                ├── AddRule.yml
                ├── Install.yml
                ├── Reconfigure.yaml
                ├── RemoveRule.yml
                ├── UninstallLicense.yaml
                ├── ansible_modules
                ├── roles
                └── vnf_vars
```

1. If there is an `Openstack` directory then we will add the following to the `lifecycle` section:

```yaml
  Create:
    drivers:
      Openstack:
        selector:
          infrastructure-type:
          - Openstack
  Delete:
    drivers:
      Openstack:
        selector:
          infrastructure-type:
          - Openstack
```
2. For each script file in the `Lifecycle/ansible/scripts` directory that is a lifecycle transition (from this list: `Create`, `Install`, `Configure`, `Reconfigure`, `Start`, `Integrity`, `Stop`, `Uninstall`, `Delete`) the following is added to the `lifecycle` section:

```yaml
  <replace with script filename without extension>:
    drivers:
      ansible:
        selector:
          infrastructure-type:
          - '*'
```
**NOTE** other files may exists in the scripts directory.

### Operations

These are derived from the `lifecycle-management-script` section of the vnfd. 

```yaml
  lifecycle-management-script:
  - id: vdu1.AddRule  
    event: external-lifecycle-management-script-event   
    lcm-transition-event: AddRule
    script-input:
      system_policy_name:
        description: name of system policy 
        type: string
        default: system_policy
      system_rule_name: 
        description: name of system rule
        type: string
        default: system_rule
      destination_ipaddr:
        description: spgw ip address to add to system rule
        type: string
      source_ipaddr:
        description: source ip address to add to system rule (change during reconfigure)
        type: string
        default: 10.10.1.0
```

For each entry in this section we will create an operation in the associated vdu resource.  To link one of the scripts to a vdu the id of the script must start with the vdu id followed by the name of the operation (**vdu1**.AddRule).  Once the vdu has been calculated this `lifecycle-management-script` is transformed into the following:

```yaml
  AddRule:
    properties:
      system_policy_name:
        description: name of system policy
        type: string
        default: system_policy
      system_rule_name:
        description: name of system rule
        type: string
        default: system_rule
      destination_ipaddr:
        description: spgw ip address to add to system rule
        type: string
      source_ipaddr:
        description: source ip address to add to system rule (change during reconfigure)
        type: string
        default: 10.10.1.0
```