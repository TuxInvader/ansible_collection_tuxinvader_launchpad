#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: ppa

short_description: Retrieve facts about a Launchpad project
version_added: "1.0.0"

description: Retrieve facts about a Launchpad project and its PPAs

options:
    project:
        description: The name of the project owning the PPA
        required: true
        type: str

    name:
        description: The name of the PPA
        required: true
        type: str

    ensure:
        description: Ensure the PPA is present or absent
        required: false
        default: present
        type: str

    displayname:
        description: The launchpad display name for the PPA
        required: false
        default: <name>
        type: str

    description:
        description: The launchpad description for the PPA
        required: false
        default: "A PPA for <name>"
        type: str

author:
    - Mark Boddington (@TuxInvader)
'''

EXAMPLES = r'''
# Ensure the PPA ~tuxinvader/jammy-mainline exists
- name: Ensure ~tuxinvader/jammy-mainline exists
  ppa:
    project: ~tuxinvader
    name: jammy-mainline
    ensure: present
  environment:
    LP_ACCESS_TOKEN: kjaslkdjalksd
    LP_ACCESS_SECRET: alskjajsdlk
'''

RETURN = r'''
# Returns a dictionary containing ppa information and its source packages
details:
    description: The PPA information
    type: dict
    returned: always
    sample: {}
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.tuxinvader.launchpad.plugins.module_utils.lpad import LPHandler

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
        project=dict(type='str', required=True),
        ensure=dict(type='str', required=False, default="present"),
        displayname=dict(type='str', required=False, default=None),
        description=dict(type='str', required=False, default=None)
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

    if module.params['displayname'] is None:
      module.params['displayname'] = module.params['name']

    if module.params['description'] is None:
      module.params['description'] = "A PPA Hosting packages related to " + module.params['name']

    try:
      launchpad = LPHandler(True)
      result = launchpad.upsert_ppa(module.params['project'], module.params['name'], 
             module.params['ensure'], displayname=module.params['displayname'],
             description=module.params['description'] )
    except Exception as e:
      module.fail_json(msg=e.args, **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
