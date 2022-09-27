#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
from ansible_collections.tuxinvader.launchpad.plugins.module_utils.dput import Dput
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type

DOCUMENTATION = r'''
---
module: ppa_upload_package

short_description: Upload source packages to a PPA for building
version_added: "1.0.0"

description: Upload source packages to a PPA for building

options:
    source_changes:
        description: The name of the source package changes file to process
        required: true
        type: str

    ppa:
        description: The name of the PPA (eg ~tuxinvader/lts-mainline)
        required: true
        type: str

author:
    - Mark Boddington (@TuxInvader)
'''

EXAMPLES = r'''
# Upload a source package to the given PPA
- name: Upload new kernel package
  ppa_upload_package:
    source_changes: /usr/local/src/deb/v5.19.11/linux-5.19.11_5.19.11-051911.202209251059_source.changes
    ppa: ~tuxinvader/lts-mainline
'''

RETURN = r'''
# Returns the number of packages pruned
count:
    description: The number of files sent to the PPA
    type: int
    returned: always
    sample: 4
'''


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        source_changes=dict(type='str', required=True),
        ppa=dict(type='str', required=True),
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
        dput = Dput()
        details = dput.upload(
            module.params['source_changes'], module.params['ppa'])
        result = {**details, **result}
        if result['count'] > 0:
            result['changed'] = True
    except Exception as e:
        module.fail_json(msg=e, **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
