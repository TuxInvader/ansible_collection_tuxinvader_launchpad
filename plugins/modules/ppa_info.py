#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
from ansible_collections.tuxinvader.launchpad.plugins.module_utils.lpad import LPHandler
from ansible.module_utils.basic import AnsibleModule
import os
__metaclass__ = type

DOCUMENTATION = r'''
---
module: ppa_info

short_description: Retrieve facts about a Launchpad PPA
version_added: "1.0.0"

description: Retrieve facts about a Launchpad PPA and its source_packages.
             Facts about the PPA are returned in a dictionary called 'details', and a list of published source_packages
             is returned in a list called 'sources'. By default we return source packages which are in the 'Published'
             state, but you can apply a source_filter of '*' to see all packages, or one of 'Pending', 'Published',
             'Superseded', 'Deleted' or 'Obsolete'

options:
    project:
        description: The name of the project owning the PPA
        default: None
        required: true
        type: str

    name:
        description: The name of the PPA
        required: true
        default: None
        type: str

    source_filter:
        description: By default we return a list of source_packages which are published, you can choose to remove
                     the filter by setting this to '*' or to use a different source status. The options for
                     source_status are Pending, Published, Superseded, Deleted or Obsolete
        required: false
        default: Published
        type: str

author:
    - Mark Boddington (@TuxInvader)
'''

EXAMPLES = r'''
# Get facts about PPA ~tuxinvader/lts-mainline using an authenticated connection
- name: Get ~tuxinvaders details
  ppa_info:
    project: ~tuxinvader
    name: lts-mainline
  environment:
    LP_ACCESS_TOKEN: kjaslkdjalksd
    LP_ACCESS_SECRET: alskjajsdlk

# Get facts about PPA ~tuxinvader/lts-mainline
- name: Get ~tuxinvaders details
  ppa_info:
    project: ~tuxinvader
    name: lts-mainline
  register: ppa_mainline
'''

RETURN = r'''
# returns
details:
  description: Facts about the PPA
  type: dict
  returned: always
  sample: { "authorized_size": 2048, "build_debug_symbols": false, "description": "PPA for LTS foo", "displayname": "foo", "external_dependencies": null,
        "http_etag": "\"70d6b91de3d852e1bd3dbb07a6391a3342fdnnnnnnnnnnnnnnnnnnnnn\"", "name": "foo", "permit_obsolete_series_uploads": false,
        "private": false, "publish": true, "publish_debug_symbols": false, "reference": "~project/ubuntu/foo", "relative_build_score": 0,
        "require_virtualized": true, "resource_type_link": "https://api.launchpad.net/devel/#archive",
        "self_link": "https://api.launchpad.net/devel/~project/+archive/ubuntu/foo", "signing_key_fingerprint": "Annnnnnn655C819nnnnnn23844A6C1nnnnn6",
        "status": "Active", "suppress_subscription_notifications": false, "web_link": "https://launchpad.net/~project/+archive/ubuntu/foo" }

sources:
  description: List of source_packages published in this PPA
  type: list
  returned: always
  sample: [ { "component_name": "main", "date_created": "2022-09-27T10:02:08.870234+00:00", "date_made_pending": null,
                "date_published": "2022-09-27T10:33:30.086025+00:00", "date_removed": null, "date_superseded": null,
                "display_name": "linux-5.19.11 5.19.11-051911.202209270958 in jammy",
                "http_etag": "\"nnnnnnnnnnnnnnnnnnnnnnnnnnnn-nnnnnnnnnnnnnnnnnnnnn\"", "pocket": "Release",
                "removal_comment": null, "resource_type_link": "https://api.launchpad.net/devel/#source_package_publishing_history",
                "scheduled_deletion_date": null, "section_name": "devel",
                "self_link": "https://api.launchpad.net/devel/~project/+archive/ubuntu/foo/+sourcepub/nnnnnnn",
                "source_package_name": "linux-5.19.11", "source_package_version": "5.19.11-051911.202209270958", "status": "Published"
            } ]
'''


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
        project=dict(type='str', required=True),
        source_filter=dict(type='str', required=False, default='Published')
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        details={},
        sources=[]
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

        lp_result = launchpad.get_ppa_info(
            module.params['project'], module.params['name'], module.params['source_filter'])
        result = {**result, **lp_result}
    except Exception as e:
        module.fail_json(msg=e.args, **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
