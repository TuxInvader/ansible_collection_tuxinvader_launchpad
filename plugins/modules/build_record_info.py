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

description: Get info about build records for a source package in a PPA. The module returns a list of matching records. Each item is a dictionary including a
            link to the log of the build and buildstate. The buildstate can be one of; "Needs building", "Successfully built", "Failed to build",
            "Dependency wait", "Chroot problem", "Build for superseded Source", "Currently building", "Failed to upload", "Uploading build",
            "Cancelling build" or "Cancelled build". See the sample for more properties in the dictionary.

            The project and ppa name are mandatory, and will return all build records from the last 24 hours (1440 minutes) by default. You can change the
            time_frame, and filter on packages by source_name and/or source_version. You can also provide a build_id if you want info on a specific build.

options:
    project:
        description: The name of the project owning the PPA
        required: true
        default: None
        type: str

    ppa:
        description: The name of the PPA
        required: true
        default: None
        type: str

    source_name:
        description: The name of the Source Package
        required: false
        default: None
        type: str

    source_version:
        description: The version of source package, the default is None (all versions)
        required: false
        default: None
        type: str

    time_frame:
        description: The time frame for builds in minutes. The default is 24 hours (1440 minutes).
        required: false
        default: 1440
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
# Get a build record for a recently uploaded source package
- name: Get build records for linux-generic-5.19
      build_record_info:
        project: ~tuxinvader
        ppa: my-random-ppa
        source_name: linux-generic-5.19
        source_version: 5.19.12
        time_frame: 30

# Get a specific build record from the ppa
- name: Get build records for build #1234567
      build_record_info:
        project: ~tuxinvader
        ppa: my-random-ppa
        build_id: 1234567
'''

RETURN = r'''
# Returns a list containing matching build records
records:
    description: A list of matching build records
    type: list
    returned: always
    sample: [
        {
            "arch_tag": "amd64",
            "build_log_url": "https://launchpad.net/~me/+archive/ubuntu/ppa/+build/246/+files/buildlog_snip-5.19_5.19.12_BUILDING.txt.gz",
            "buildstate": "Uploading build",
            "can_be_cancelled": false,
            "can_be_rescored": false,
            "can_be_retried": false,
            "changesfile_url": null,
            "date_first_dispatched": "2022-09-30T23:48:22.137375+00:00",
            "date_started": "2022-09-30T23:48:22.137375+00:00",
            "datebuilt": "2022-09-30T23:49:28.308409+00:00",
            "datecreated": "2022-09-30T23:48:11.715660+00:00",
            "dependencies": null,
            "duration": "0:01:06.171034",
            "external_dependencies": null,
            "http_etag": "\"688413b0946912af2dffb13359dbe9e721a9397d-181ac05e4425dc0066f12f4c16b633b6c20d7c11\"",
            "pocket": "Release",
            "resource_type_link": "https://api.launchpad.net/devel/#build",
            "score": null,
            "self_link": "https://api.launchpad.net/devel/~tuxinvader/+archive/ubuntu/my-random-ppa/+build/24511076",
            "source_package_name": "linux-generic-5.19",
            "source_package_version": "5.19.12",
            "title": "amd64 build of linux-generic-5.19 5.19.12 in ubuntu focal RELEASE",
            "upload_log_url": null,
            "web_link": "https://launchpad.net/~tuxinvader/+archive/ubuntu/my-random-ppa/+build/24511076"
        }
    ]
'''


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        project=dict(type='str', required=True),
        ppa=dict(type='str', required=True),
        source_name=dict(type='str', required=False, default=None),
        source_version=dict(type='str', required=False, default=None),
        build_id=dict(type='int', required=False, default=None),
        time_frame=dict(type='int', Required=False, default=1440)
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
