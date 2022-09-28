#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
from ansible_collections.tuxinvader.launchpad.plugins.module_utils.lpad import LPHandler
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type

DOCUMENTATION = r'''
---
module: project_info

short_description: Retrieve facts about a Launchpad project
version_added: "1.0.0"

description: Retrieve facts about a Launchpad project and its PPAs

options:
    name:
        description: The name of the project to retrieve
        default: None
        required: true
        type: str

    ppa_filter:
        description: By default we return a list of PPAs which are Active, you can choose to remove
                     the filter by setting this to '*' or to 'Deleted' if you want deleted PPAs only
        required: false
        default: Active
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
# Get facts about project ~tuxinvader
- name: Get ~tuxinvaders details
  project_info:
    name: ~tuxinvader
    authorize: true
  environment:
    LP_ACCESS_TOKEN: kjaslkdjalksd
    LP_ACCESS_SECRET: alskjajsdlk
'''

RETURN = r'''
# Returns a dictionary containing project and ppa information
details:
  description: Facts about the Project
  type: dict
  returned: always
  sample: { "account_status": "Active", "account_status_history": "tag:launchpad.net:2008:redacted", "date_created": "2006-05-21T14:19:54.712320+00:00",
        "description": "https://github.com/TuxInvader", "display_name": "TuxInvader", "hide_email_addresses": true, "homepage_content": null,
        "http_etag": "\"fnnnnnnnnnnnnnnnnnne83c-5f07fb80393dnnnnnnnnnnnnnnn23d42ff\"", "is_probationary": true,
        "is_team": false, "is_ubuntu_coc_signer": true, "is_valid": true, "karma": 0, "mailing_list_auto_subscribe_policy": "Ask me when I join a team",
        "name": "tuxinvader", "private": false, "resource_type_link": "https://api.launchpad.net/devel/#person",
        "self_link": "https://api.launchpad.net/devel/~tuxinvader", "time_zone": "Europe/London", "visibility": "Public",
        "web_link": "https://launchpad.net/~tuxinvader" }

ppas:
  description: List of PPAs owned by this project
  type: list
  returned: always
  sample: [ { "authorized_size": 2048, "build_debug_symbols": false, "description": "Ubuntu mainline kernels",
            "displayname": "lts-mainline", "external_dependencies": null,
            "http_etag": "\"cannnnnnnnnnnnnnnnna86c10-0d4e6e732nnnnnnnnnnnnnnnnnnd\"", "name": "lts-mainline",
            "permit_obsolete_series_uploads": false, "private": false, "publish": true,
            "publish_debug_symbols": false, "reference": "~tuxinvader/ubuntu/lts-mainline", "relative_build_score": 0,
            "require_virtualized": true, "resource_type_link": "https://api.launchpad.net/devel/#archive",
            "self_link": "https://api.launchpad.net/devel/~tuxinvader/+archive/ubuntu/lts-mainline",
            "signing_key_fingerprint": "A132D7D22655C81961EDEA823844A6C1C6FD1056", "status": "Active",
            "suppress_subscription_notifications": false,
            "web_link": "https://launchpad.net/~tuxinvader/+archive/ubuntu/lts-mainline"  }  ]
'''


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
        ppa_filter=dict(type='str', required=False, default="Active"),
        authorize=dict(type='bool', required=False, default=False)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        details={},
        ppas=[]
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
        lp_result = launchpad.get_project_info(module.params['name'], module.params['ppa_filter'])
        result = {**result, **lp_result}
    except Exception as e:
        module.fail_json(msg=e.args, **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
