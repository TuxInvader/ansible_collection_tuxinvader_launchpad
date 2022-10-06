#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
from ansible_collections.tuxinvader.launchpad.plugins.module_utils.lpad import LPHandler
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type

DOCUMENTATION = r'''
---
module: prune_ppa

short_description: Prune a PPA for size, by removing the oldest source packages
version_added: "1.0.0"

description: Prune a PPA for size, by removing the oldest source packages

options:
    name:
        description: The name of the PPA to prune
        required: true
        type: str

    project:
        description: The name of the project which owns the PPA
        required: true
        type: str

    max_sources:
        description: The number of source packages to leave
        required: false
        type: int
        default: 2

    source_name:
        description: The source_package name to limit pruning to matching packages
        required: false
        type: string
        default: None

    match:
        description: How to match the source_package name, either [exact, starts_with_ ends_with, contains, or regex]
        required: false
        type: string
        defailt: exact

    prune_by:
        description: How should the packages be ordered prior to pruning, options are [date, or version]
        required: false
        type: string
        default: date

author:
    - Mark Boddington (@TuxInvader)
'''

EXAMPLES = r'''
# Prune the PPA by publish date down to 2 source packages
- name: Prune mainline PPA to most recent 2 releases
  prune_ppa:
    name: lts-mainline
    project: ~tuxinvader
    max_sources: 2
  environment:
    LP_ACCESS_TOKEN: kjaslkdjalksd
    LP_ACCESS_SECRET: alskjajsdlk

# Prune PPA by package version to 4 packages matching regex 'linux-[0-9]+'
- name: prune lts-mainline PPA to 4 linux-[0-9]+ packages by regex, ordered by version
  prune_ppa:
    name: lts-mainline
    project: ~tuxinvader
    source_name: "linux[0-9]+"
    match: regex
    prune_by: version
    max_sources: 4
'''

RETURN = r'''
# Returns the number of packages pruned
count:
    description: The number of packages removed
    type: int
    returned: always
    sample: 1
pruned:
  description: Dictionary of package names and publication dates which were pruned
  type: dict
  returned: always
  sample: { "linux-5.19.10": "2022-09-21T14:28:54.544426+00:00" }
remaining:
  description: Dictionary of package names and publication dates remaining
  type: dict
  returned: always
  sample: { "linux-5.19.10": "2022-09-21T14:28:54.544426+00:00" }
'''


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
        project=dict(type='str', required=True),
        max_sources=dict(type='int', required=False, default=2),
        source_name=dict(type='str', required=False, default=None),
        match=dict(type='str', required=False, default="exact"),
        prune_by=dict(type='str', required=False, default="date"),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    try:
        launchpad = LPHandler(True)
        lp_result = launchpad.prune_ppa(
            module.params['project'], module.params['name'], module.params['max_sources'], module.params['source_name'], 
            module.params['match'], module.params['prune_by'])
        result = {**result, **lp_result}
        if result['count'] > 0:
            result['changed'] = True
    except Exception as e:
        module.fail_json(msg=e.args, **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
