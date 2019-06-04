# Cisco DNA Center Automation with pyATS | Genie

This repository contains examples of how to get started with automating Cisco 
DNA Center REST APIs in [Cisco pyATS | Genie test framework].

[Cisco pyATS | Genie test framework]: http://cs.co/pyats

## Installation

To run this demo, you should follow the pyATS | Genie installation guide, 
and have it installed in your Python virtual environment. Eg:

```bash
bash$ pip install pyats genie
```

## API Diff using Genie CLI

Genie CLI is a powerful linux-based command-line utility offering Genie Python 
functionality directly from a linux terminal. It requires no previous knowledge 
of Python or network programming, making it a great way to start getting 
acquainted with Genie.

This demo focuses on being able to take a snapshots of Cisco DNA Center's REST
API outputs, save to file, and use it later for comparison/difference analysis.

```bash

# snapshot rest apis related to: interface, isis and ospf
# and save to folder called "initial"
bash$ genie dnac interface isis ospf --testbed-file dna.yaml --output initial --via dnac:rest --device dnac

# now - if something changed, regardless of whether it was done intentionally
# or not, you can take another snapshot, and compare it against your know-good states

# take the 2nd snapshot, save it into folder "modified"
bash$ genie dnac interface isis ospf --testbed-file dna.yaml --output modified --via dnac:rest --device dnac

# do a diff between the two state snapshots
bash$ genie diff initial modified
# any differences will be displayed to screen
```

## Northbound & Southbound Test Automation

The next example uses the power of Genie triggers & verification concept, 
building on reusable testcases. Here's our test plan:

1. Find an interface via device mgmt/vty and make sure description is the same as DNAC’s REST API output
2. Change interface configuration on device: change description
3. Verify it has been modified both in device and in DNAC 
4. Restore configuration (remove description change)
5. Verify everything is restored in both device and in DNAC

The code necessary to run this example is included in this repository. 

```bash
bash$ pyats run job dnac_job.py --testbed-file dna.yaml --html-logs .
```

The generated HTML log files will be available in this folder.

> Copyright (c) 2019 Cisco Systems, Inc. and/or its affiliates