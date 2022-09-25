# Ansible Collection - tuxinvader.launchpad

Interract with the Ubuntu Launchpad API from Ansible.

## Authentication

Most read operations can be done without authorization, however there are two tasks which can be used
to get a set of OATH credentials for use with tasks which do require authentication.

This playbook will execute the `start_interactive_login` module and output the authorization url.
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

## Pruning PPAs

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

Pruning (deleting packages from a PPA) requires authentication.

## Uploading Packages to PPA

Once pruned I want to upload new packages, and so there's a module for that too.

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


