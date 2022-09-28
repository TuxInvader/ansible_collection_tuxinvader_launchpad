#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
from ansible_collections.tuxinvader.launchpad.plugins.module_utils.lpad import LPHandler
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type

DOCUMENTATION = r'''
---
module: wait_interactive_login

short_description: Perform the OAUTH authorization process for using a launchpad with a user account
version_added: "1.0.0"

description: This task should be called in a loop after `start_interactive_login` and retry until \
             the user has authorized the request token. The task will return LP_ACCESS_TOKEN and \
             LP_ACCESS_SECRET which can then be used as environment vars for authenticated Launchpad access.

options:
    credentials:
        description: The OAUTH request token output from start_interactive_login
        required: true
        type: str

author:
    - Mark Boddington (@TuxInvader)
'''

EXAMPLES = r'''

# Start the interactive login process by generating a request token and presenting url to user
- name: Start Interactive login
  start_interactive_login:
  register: login_start

- name: Prompt user
  debug:
    msg: "Please open this URL to authorize Ansible access: {{ login_start.authorization_url }}"

# Wait for the token exchange to be completed by the user, and return the OAUTH tokens
- name: Wait for auth to complete
  wait_interactive_login:
    credentials: "{{ login_start.credentials | to_json }}"
  delay: 5
  retries: 12
  register: login_done
  until: login_done.LP_ACCESS_TOKEN is defined

- name: Display Tokens
  debug:
    msg: "Please Add these to your environment: LP_ACCESS_TOKEN={{ login_done.LP_ACCESS_TOKEN }}   LP_ACCESS_SECRET={{ login_done.LP_ACCESS_SECRET }}"

'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
LP_ACCESS_TOKEN:
    description: The Access token for authenticated LP access. Add to your environment.
    type: str
    returned: changed
    sample: 'TWGbLbMX892jdbffzQF5'
LP_ACCESS_SECRET:
    description: The Access token secret for authenticated LP access. Add to your environment.
    type: str
    returned: changed
    sample: 'cFmGdmkXCTjRdfc5pRVvd8933bv8R7pmSkbXbmpPC2Ddkasjdklagp5gK32xK9VlxqPmRcRcnvJskKj7xN'
'''


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        credentials=dict(type='str', required=True),
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
        launchpad = LPHandler()
        details = launchpad.wait_interactive_login(
            module.params['credentials'])
        result = {**details, **result}
        result['changed'] = True
    except Exception as e:
        module.log(e)
        module.fail_json(msg="Waiting for Authorization...", **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
