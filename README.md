# Ansible Collection - tuxinvader.launchpad

This Ansible Collection enables you to interract with the Ubuntu Launchpad API.

- [Ansible Collection - tuxinvader.launchpad](#ansible-collection---tuxinvaderlaunchpad)
- [Read Operations](#read-operations)
  - [The user_info module](#the-user_info-module)
  - [The project_info module](#the-project_info-module)
  - [The ppa_info module](#the-ppa_info-module)
  - [The build_record_info module](#the-build_record_info-module)
- [Write Operations](#write-operations)
  - [The ppa module](#the-ppa-module)
  - [The prune_ppa module](#the-prune_ppa-module)
  - [The ppa_upload_package module](#the-ppa_upload_package-module)
  - [The source_package module](#the-source_package-module)
- [Authentication](#authentication)
  


# Read Operations

The read operations can usually be done anonymously and so don't require an OAUTH token, but the modules will all use an
authenticated connection if the `LP_ACCESS_TOKEN` and `LP_ACCESS_SECRET` environment variables are present. 
See the [Authentication section](#authentication) for helper modules to setup OAUTH access.

## The user_info module

This is one of the simplest modules in the collection. It can be used to retrieve a dictionary containing `details` about a
specific user. In fact it returns almost identical information to the `project_info` module below, but the other module also
returns a list of `ppas` owned by the project/user/team.

The `name` parameter for this module is the name without any leading `~` tilda.

```yaml
- hosts: localhost
  become: false
  collections:
    - tuxinvader.launchpad

tasks:

  - name: Test User Info
    user_info:
      name: tuxinvader
    register: tux
```

## The project_info module

This module returns a `details` dictionary about the provided project/user/team supplied in the `name` parameter, and by default
a list of "Active" PPAs under `ppas`. The PPAs returned can be filtered by status using the optional `ppa_filter`
parameter, possible values are ['Active', 'Deleted', '*'].

```yaml
- hosts: localhost
  become: false
  collections:
    - tuxinvader.launchpad

tasks:

  - name: Test Project Info
    project_info:
      name: ~tuxinvader
      ppa_filter: '*'
```

## The ppa_info module

You can use `ppa_info` to retrieve information about a given PPA and its source packages. You need to provide the `project` name as "~username"
and the PPA `name`. The information about the PPA will be returned in a dictionary called `details` and a list of source packages in `sources`. 

```yaml
- hosts: localhost
  become: false
  collections:
    - tuxinvader.launchpad

tasks:

  - name: Test PPA Info
    ppa_info:
      project: ~tuxinvader
      name: my-random-ppa
```
The module will return a list of "Published" source packages by default, but you can change that by providing a `source_filter` parameter which
can be set to one of [Pending, Published, Superseded, Deleted, or Obsolete]. Alternatively you can set the value to '*' and the module will return
all source packages.

## The build_record_info module

The `build_record_info` module will return build records from the provided `project` and `ppa`. You can narrow the list of records returned
by providing one or more optional parameters. 

You can search for records of specific packages with:

* source_name: filters the records for matching source packages
* source_version: filters the records for matching source versions

You can limit the time frame of the search by providing the max number of minutes in the past the build was created. The default time frame is 24 hours.
* time_frame: limits the build records to those with a creation date within `n` minutes of now

You can also pass an ID of a known build if you have one
* build_id: retrieves the record of a known build

Example:
```yaml
- hosts: localhost
  become: false
  collections:
    - tuxinvader.launchpad

tasks:

  - name: Get build records for linux-generic-5.19 in the past 30 minutes
    build_record_info:
      project: ~tuxinvader
      ppa: my-random-ppa
      source_name: linux-generic-5.19
      time_frame: 30
```

# Write Operations

Several of these modules will require an authenticated connection to launchpad. You should take a look at the
[Authentication Section](#authentication) if you haven't already setup OAUTH access tokens.

## The ppa module

The PPA module enables CRUD operations on PPAs. Use the `ensure` parameter to ensure that a PPA is
either present or absent from launchpad. You can modify it's display name and description too.

```yaml
- hosts: localhost
  become: false
  collections:
    - tuxinvader.launchpad
    - community.general

  vars:
    rand_string: "{{ lookup('community.general.random_string', length=24, special=false) }}"

  environment:
    LP_ACCESS_TOKEN: "{{ secret_access_token }}"
    LP_ACCESS_SECRET: "{{ secret_access_secret }}"

  tasks:

    - name: Ensure Random PPA is updated
      ppa:
        project: ~tuxinvader
        name: my-random-ppa
        displayname: ppa created by launchpadlib
        description: This has nothing to do with {{ rand_string }}
        ensure: present
```
This module returns details of the PPA modified in a `details` dictionary a list of source packages under `sources`.
By default it returns a list of "Published" source packages, but this can be changed by providing the `source_filter`
parameter.

## The prune_ppa module

My primary use-case for this collection is to prune packages from my kernel PPAs before uploading new ones. 

```yaml
- hosts: localhost
  become: false
  collections:
    - tuxinvader.launchpad

  environment:
    LP_ACCESS_TOKEN: "{{ secret_access_token }}"
    LP_ACCESS_SECRET: "{{ secret_access_secret }}"

  tasks:

    - name: Prune PPA to 2 packages
      prune_ppa:
        name: lts-mainline
        project: ~tuxinvader
        max_sources: 2
```

This module returns a `count` and a list of `pruned` packages.

## The ppa_upload_package module

The `ppa_upload_package` module doesn't check for the existence of a source package before starting
the upload, in fact it will blindly make a dput upload of whatever changes file you provide. 

You need to check you're not uploading a duplicate prior to calling this module, *alternatively* 
use the [source_package](#the-source_package-module) instead.

```yaml
- hosts: localhost
  become: false
  collections:
    - tuxinvader.launchpad

  tasks:

    - name: Upload Kernel packages to PPA
      ppa_upload_package:
        source_changes: /usr/local/src/cod/debs/v5.15.70/linux-generic-5.15_5.15.70_source.changes
        ppa: ~tuxinvader/lts-mainline-longterm
```

No authentication needed. The source package was signed when it was built, so PPA upload is via anonymous FTP.

This module returns a `count` and a list of `uploads` sent.

## The source_package module

The `source_package` module can be used to ensure a package is present on a PPA. It will call the API to
check whether a package of `name` and `version` exists in the given `project`/`ppa` and depending on whether
`ensure` is set to "present" or "absent" it will attempt to create or delete any matching packages.

The `project`, `ppa`, and `name` parameters are required and `ensure` defaults to "present". 
If you don't provide a `version` then all released versions will be acted upon (this could mean deleted!).

If you set `ensure` to "present", but don't provide a `source_package` then a missing package will result
in the module returning a `fail`

```yaml
- hosts: localhost
  become: false
  collections:
    - tuxinvader.launchpad

tasks:

  - name: Ensure kernel 5.19.12 is added
    source_package:
      project: ~tuxinvader
      ppa: my-random-ppa
      name: linux-generic-5.19
      version: 5.19.12
      ensure: present
      source_changes: /usr/local/src/cod/debs/v5.19.12/linux-generic-5.19_5.19.12_source.changes
```
This module returns a list of `sources` which matched, and a list of `messages` detailing the steps taken.

# Authentication

Most read operations can be done without authorization, however there are two modules which can be used
to get a set of OAUTH credentials for use with tasks which do require authentication.

The `start_interactive_login` module can be used to initiate an OAUTH access request, and return an
authorization url. You can then authorize Ansible by opening the URL in your web browser. This module
also returns the temporary request token in a `credentials` dictionary, which needs to be passed on to 
the `wait_interactive_login` module. The `wait_interactive_login` module should be called in a loop to
wait for the browser authorization to be completed. Once you have authorized Ansible, this module will
return your access tokens.

The playbook below will execute the `start_interactive_login` module and output the authorization url.
It will then loop for 60 seconds waiting for you to authorize ansible in a browser window.
If successful it will output the OAUTH token and secret which can then be provided to ansible through
environment variables `LP_ACCESS_TOKEN` and `LP_ACCESS_SECRET`

```yaml
- hosts: localhost
  become: false
  collections:
    - tuxinvader.launchpad

  tasks:

    - name: Start Interactive login
      start_interactive_login:
      register: login_start

    - name: Prompt user
      debug:
        msg: "Please open this URL to authorize Ansible access: {{ login_start.authorization_url }}"

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
```

:wq
