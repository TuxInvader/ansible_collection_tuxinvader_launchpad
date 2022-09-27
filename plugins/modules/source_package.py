#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
from ansible_collections.tuxinvader.launchpad.plugins.module_utils.lpad import LPHandler
from ansible_collections.tuxinvader.launchpad.plugins.module_utils.dput import Dput
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = r'''
---
module: source_package

short_description: Manage source_packages in a PPA
version_added: "1.0.2"

description: Manage source packages in a PPA

options:
    project:
        description: The name of the project owning the PPA
        required: true
        type: str

    ppa:
        description: The name of the PPA
        required: true
        type: str

    name:
        description: The name of the Source Package
        required: true
        type: str

    version:
        description: The version of source package, the default is '*' (all versions)
        required: false
        default: '*'
        type: str

    ensure:
        description: Ensure the PPA is present or absent
        required: false
        default: present
        type: str

    match:
        description: Use when ensure==absent to select files for deletion, ignored when ensure==present
                     Can be either exact, starts_with, ends_with, contains, or regex
        required: false
        default: exact
        type: str

    source_changes:
        description: The source file to upload to the PPA. If ensure is present and the package is missing
                     we will send the changes file to the PPA for building, if source_changes is unset we fail.
        required: false
        type: str

author:
    - Mark Boddington (@TuxInvader)
'''

EXAMPLES = r'''
# Delete the kernel 5.19.11 packages from ~tuxinvader/jammy-mainline
- name: Delete the kernel 5.19.11 packages from ~tuxinvader/jammy-mainline
  source_package:
    project: ~tuxinvader
    ppa: jammy-mainline
    name: kernel-5.19.11
    ensure: absent
  environment:
    LP_ACCESS_TOKEN: kjaslkdjalksd
    LP_ACCESS_SECRET: alskjajsdlk
'''

RETURN = r'''
# Returns a dictionary containing ppa information and its source packages
sources:
    description: Information about all effected packages
    type: list
    returned: always
    sample: [{"package": "foo", "status": "deleted"}]
'''


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
        version=dict(type='str', required=False, default="*"),
        project=dict(type='str', required=True),
        ppa=dict(type='str', required=True),
        ensure=dict(type='str', required=False, default="present"),
        match=dict(type='str', required=False, default="exact"),
        source_changes=dict(type='str', required=False, default=None)
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
        result = launchpad.check_source_package(module.params['project'], module.params['ppa'], 
                                      module.params['name'], module.params['version'], 
                                      module.params['ensure'], module.params['match'])
        if len(result['sources']) == 0:
            if module.params['ensure'].lower() == 'present':
                if module.params['source_changes'] != None:
                    dput = Dput()
                    ppa_name = "%s/%s" % (module.params['project'], module.params['ppa'])
                    result['dput'] = dput.upload(module.params['source_changes'], ppa_name)
                else:
                    module.fail_json(msg="FAIL - The source package is not present on PPA and we have no source_changes file to upload", **result)
    except Exception as e:
        module.fail_json(msg=e.args, **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
