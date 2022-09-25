#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: start_interactive_login

short_description: Perform the OAUTH authorization process for using a launchpad with a user account
version_added: "1.0.0"

description: This task should be called to get the request token url, and then wait_interactive_login should be called to complete the auth process

options:

author:
    - Mark Boddington (@TuxInvader)
'''

EXAMPLES = r'''
# Get the auth url for interactive login
- name: Start Interactive login
  start_interactive_login:
  register: login_start

- name: Prompt user
  debug:
    msg: "Please open this URL to authorize Ansible access: {{ login_start.authorization_url }}"
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
authorization_url:
    description: The authorization url, open in your web browser and authorize the ansible client 
    type: str
    returned: always
    sample: 'https://launchpad.net/+authorize?key=askjlaksdj'
credentials:
    description: The request token credentials needed for exchange. Pass these to `wait_interactive_login`
    type: dict
    returned: always
    sample: '{"oauth_token": "", "oauth_token_secret": ""}'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native, to_text
from ansible_collections.tuxinvader.launchpad.plugins.module_utils.lpad import LPHandler

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=False, default='start_interactive_login'),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        authorization_url=''
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

    return_msg = ""
    try:
      launchpad = LPHandler()
      details = launchpad.start_interactive_login()
      result['credentials'] = details['credentials']
      result['authorization_url'] = details['authorization_url']
      module.log(return_msg)
    except Exception as e:
      module.fail_json(msg=e, **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
