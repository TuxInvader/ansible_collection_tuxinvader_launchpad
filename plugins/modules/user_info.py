#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
from ansible_collections.tuxinvader.launchpad.plugins.module_utils.lpad import LPHandler
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type

DOCUMENTATION = r'''
---
module: user_info

short_description: Retrieve facts about a Launchpad user
version_added: "1.0.0"

description: Retrieve facts about a Launchpad user

options:
    name:
        description: The name of the user to retrieve
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
# Get facts about user tuxinvader
- name: Get tuxinvaders details
  user_info:
    name: tuxinvader
    authorize: true
  environment:
    LP_ACCESS_TOKEN: kjaslkdjalksd
    LP_ACCESS_SECRET: alskjajsdlk
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
'''


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
        authorize=dict(type='bool', required=False, default=False)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        user='',
        details={}
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

    result['user'] = module.params['name']

    try:
        launchpad = LPHandler(module.params['authorize'])
        lp_result = launchpad.get_user_info(module.params['name'])
        result = {**result, **lp_result}
    except Exception as e:
        module.fail_json(msg=e.args, **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
