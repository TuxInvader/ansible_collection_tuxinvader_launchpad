#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
from ansible_collections.tuxinvader.launchpad.plugins.module_utils.lpad import LPHandler
from ansible.module_utils.basic import AnsibleModule
import os

__metaclass__ = type

DOCUMENTATION = r'''
---
module: build_record_info

short_description: Get info about Build records for a source package in a PPA
version_added: "1.0.3"

description: Get info about Build records for a source package in a PPA

options:
    project:
        description: The name of the project owning the PPA
        required: true
        type: str

    ppa:
        description: The name of the PPA
        required: true
        type: str

    source_name:
        description: The name of the Source Package
        required: true
        type: str

    source_version:
        description: The version of source package, the default is '*' (all versions)
        required: false
        default: '*'
        type: str

    time_frame:
        description: The time frame for builds in minutes. The default is 24 hours (168 minutes).
        required: false
        default: 168
        type: int

    build_id:
        description: A specific build_id to retrieve
        required: false
        default: None
        type: int

author:
    - Mark Boddington (@TuxInvader)
'''

EXAMPLES = r'''
# Delete the kernel 5.19.11 packages from ~tuxinvader/jammy-mainline
- name: Get build records for linux-generic-5.19
      build_record_info:
        project: ~tuxinvader
        ppa: my-random-ppa
        source_name: linux-generic-5.19
        #source_version: 5.19.12
        #build_id: 24510990
        #build_id: 24505969
        time_frame: 9999999

# Ensure the package 5.15.70 is published, upload if missing
-   name: Ensure kernel 5.19.12 is added
    source_package:
        project: ~tuxinvader
        ppa: my-random-ppa
        name: linux-5.19.12
        version: 5.19.12-051912.202209281927
        ensure: present
        source_changes: /usr/local/src/cod/debs/v5.19.12/linux-5.19.12_5.19.12-051912.202209281927_source.changes
'''

RETURN = r'''
# Returns a dictionary containing ppa information and its source packages
sources:
    description: Information about all effected packages
    type: list
    returned: always
    sample: [
         {
            "component_name": "main",
            "date_created": "2022-09-27T20:28:09.672351+00:00",
            "date_made_pending": null,
            "date_published": "2022-09-27T21:21:45.001015+00:00",
            "date_removed": null,
            "date_superseded": null,
            "display_name": "linux-generic-5.19 5.19.11 in focal",
            "http_etag": "\"dbbf1a487b52f75b2609734117fa4c4fb202240f-d03b23f6284e5b10e67438443fe111b7f5e65ab3\"",
            "pocket": "Release",
            "removal_comment": null,
            "resource_type_link": "https://api.launchpad.net/devel/#source_package_publishing_history",
            "scheduled_deletion_date": null,
            "section_name": "devel",
            "self_link": "https://api.launchpad.net/devel/~tuxinvader/+archive/ubuntu/my-random-ppa/+sourcepub/13973912",
            "source_package_name": "linux-generic-5.19",
            "source_package_version": "5.19.11",
            "status": "Published"
        }
    ]
messages:
    description: Information about each package that was processed
    type: list
    returned: always
    sample: [
        "package unchanged, version mismatch: '5.19.12' not '6.0-rc7', regex: '^linux-generic.*', result: 'linux-generic-5.19'"
    ]
dput:
    description: Information about any uploads which may have taken place (if source_changes was set and package was missing)
    type: dict
    returned: always
    sample: {
        "count": 4,
        "uploads": [
            "linux-5.19.12_5.19.12-051912.202209281927_source.changes",
            "linux-5.19.12_5.19.12-051912.202209281927.dsc",
            "linux-5.19.12_5.19.12-051912.202209281927.tar.gz",
            "linux-5.19.12_5.19.12-051912.202209281927_source.buildinfo"
        ]
    }
'''


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        project=dict(type='str', required=True),
        ppa=dict(type='str', required=True),
        source_name=dict(type='str', required=False),
        source_version=dict(type='str', required=False, default=None),
        build_id=dict(type='int', required=False, default=None),
        time_frame=dict(type='int', Required=False, default=168)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        records=[],
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
        auth = False
        if os.environ.get('LP_ACCESS_TOKEN') is not None:
            auth = True
        launchpad = LPHandler(auth)
        lp_result = launchpad.get_build_record_info(module.params['project'], module.params['ppa'],
                                                    module.params['source_name'], module.params['source_version'],
                                                    module.params['build_id'], module.params['time_frame'])
        result = {**result, **lp_result}
    except Exception as e:
        module.fail_json(msg=e.args, **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
