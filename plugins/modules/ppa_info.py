#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: ppa_info

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

    authorize:
        description: Use an Authenticated connection to launchpad. You need to set LP_ACCESS_[TOKEN|SECRET] env vars for authentication
        required: false
        default: false
        type: bool

author:
    - Mark Boddington (@TuxInvader)
'''

EXAMPLES = r'''
# Get facts about PPA ~tuxinvader/lts-mainline
- name: Get ~tuxinvaders details
  ppa_info:
    project: ~tuxinvader
    name: lts-mainline
    authorize: true
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
        authorize=dict(type='bool', required=False, default=False)
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
      launchpad = LPHandler(module.params['authorize'])
      result['details'] = launchpad.get_ppa_info(module.params['project'], module.params['name'])
    except Exception as e:
      module.fail_json(msg=e, **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
