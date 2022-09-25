from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.common.text.converters import to_native, to_text
from launchpadlib.credentials import Consumer, Credentials, CredentialStore, MemoryCredentialStore, AuthorizeRequestTokenWithURL, AccessToken
from launchpadlib.launchpad import Launchpad
import time
import os
import httplib2
import json

LP_APP_NAME = 'ansible'


class LPHandler(object):

  _consumer = LP_APP_NAME
  _authorize = False
  _credStore = None
  _credentials = None
  api_root = None

  def __init__(self, authorize=False, consumer=LP_APP_NAME):
    self._consumer = consumer
    self._authorize = authorize
    if authorize:
      if os.environ.get('LP_ACCESS_TOKEN') == None:
        raise Exception( to_text("You need to set 'LP_ACCESS_TOKEN' and 'LP_ACCESS_SECRET' environment variables when 'authorize' is 'true'"))
      if os.environ.get('LP_ACCESS_SECRET') == None:
        raise Exception( to_text("You need to set 'LP_ACCESS_TOKEN' and 'LP_ACCESS_SECRET' environment variables when 'authorize' is 'true'"))
      self._credStore = EnvCredentialStore(consumer)
      self._credentials = self._credStore.load(consumer)

  def _login(self):
    if self._authorize:
      ae = AuthorizeRequestTokenWithURL(service_root='production', consumer_name=self._consumer)
      self.api_root = Launchpad.login_with(application_name=self._consumer, service_root='production', credential_store=self._credStore, authorization_engine=ae, version='devel')
    else:
      self.api_root = Launchpad.login_anonymously(self._consumer, 'production', version='devel')

  def start_interactive_login(self):
    self._credStore = EnvCredentialStore(self._consumer)
    self._credentials = ReqTokenCredentials(self._consumer)
    authorization_url = self._credentials.get_request_token( context=None, web_root='production' )
    return { 'authorization_url': authorization_url, 'credentials': self._credentials.get_req_token() }

  def wait_interactive_login(self, credentials):
    result = {}
    self._credStore = EnvCredentialStore(self._consumer)
    self._credentials = ReqTokenCredentials(self._consumer)
    self._credentials.set_req_token(credentials)
    self._credentials.exchange_request_token_for_access_token(web_root='production')
    result['LP_ACCESS_TOKEN'] = self._credentials.access_token.key
    result['LP_ACCESS_SECRET'] = self._credentials.access_token.secret
    return result
 
  def get_user_info(self, name):
    result = {}
    if self.api_root is None:
      self._login()
    people = self.api_root.people
    for person in people.find(text=name):
      result['self_link'] = person.self_link
      result['web_link'] = person.web_link
      result['resource_type_link'] = person.resource_type_link
      result['http_etag'] = person.http_etag
      result['account_status'] = person.account_status
      result['account_status_history'] = person.account_status_history
      result['date_created'] = person.date_created
      result['description'] = person.description
      result['display_name'] = person.display_name
      result['hide_email_addresses'] = person.hide_email_addresses
      result['homepage_content'] = person.homepage_content
      result['is_probationary'] = person.is_probationary
      result['is_team'] = person.is_team
      result['is_ubuntu_coc_signer'] = person.is_ubuntu_coc_signer
      result['is_valid'] = person.is_valid
      result['karma'] = person.karma
      result['mailing_list_auto_subscribe_policy'] = person.mailing_list_auto_subscribe_policy
      result['name'] = person.name
      result['private'] = person.private
      result['time_zone'] = person.time_zone
      result['visibility'] = person.visibility
    return result

  def get_project_info(self, name):
    result = { 'ppas': {} }
    if self.api_root is None:
      self._login()
    project = self.api_root.projects[name]
    result['self_link'] = project.self_link
    result['web_link'] = project.web_link
    result['resource_type_link'] = project.resource_type_link
    result['http_etag'] = project.http_etag
    result['account_status'] = project.account_status
    result['account_status_history'] = project.account_status_history
    result['date_created'] = project.date_created
    result['description'] = project.description
    result['display_name'] = project.display_name
    result['hide_email_addresses'] = project.hide_email_addresses
    result['homepage_content'] = project.homepage_content
    result['is_probationary'] = project.is_probationary
    result['is_team'] = project.is_team
    result['is_ubuntu_coc_signer'] = project.is_ubuntu_coc_signer
    result['is_valid'] = project.is_valid
    result['karma'] = project.karma
    result['mailing_list_auto_subscribe_policy'] = project.mailing_list_auto_subscribe_policy
    result['name'] = project.name
    result['private'] = project.private
    result['time_zone'] = project.time_zone
    result['visibility'] = project.visibility
    for ppa in project.ppas:
      result['ppas'][ppa.name] = {}
      result['ppas'][ppa.name]['self_link'] = ppa.self_link
      result['ppas'][ppa.name]['web_link'] = ppa.web_link
      result['ppas'][ppa.name]['resource_type_link'] = ppa.resource_type_link
      result['ppas'][ppa.name]['http_etag'] = ppa.http_etag
      result['ppas'][ppa.name]['authorized_size'] = ppa.authorized_size
      result['ppas'][ppa.name]['build_debug_symbols'] = ppa.build_debug_symbols
      result['ppas'][ppa.name]['description'] = ppa.description
      result['ppas'][ppa.name]['displayname'] = ppa.displayname
      result['ppas'][ppa.name]['external_dependencies'] = ppa.external_dependencies
      result['ppas'][ppa.name]['name'] = ppa.name
      result['ppas'][ppa.name]['permit_obsolete_series_uploads'] = ppa.permit_obsolete_series_uploads
      result['ppas'][ppa.name]['private'] = ppa.private
      result['ppas'][ppa.name]['publish'] = ppa.publish
      result['ppas'][ppa.name]['publish_debug_symbols'] = ppa.publish_debug_symbols
      result['ppas'][ppa.name]['reference'] = ppa.reference
      result['ppas'][ppa.name]['relative_build_score'] = ppa.relative_build_score
      result['ppas'][ppa.name]['require_virtualized'] = ppa.require_virtualized
      result['ppas'][ppa.name]['signing_key_fingerprint'] = ppa.signing_key_fingerprint
      result['ppas'][ppa.name]['status'] = ppa.status
      result['ppas'][ppa.name]['suppress_subscription_notifications'] = ppa.suppress_subscription_notifications
    return result

  def prune_ppa(self, project, name, max_sources):
    result = { 'pruned': {}, 'count': 0  }
    if self.api_root is None:
      self._login()

    project = self.api_root.projects[project]
    lp_ppa = list(filter(lambda x: x.name == name, project.ppas))[0]
    pb = lp_ppa.getPublishedSources(status="Published")

    if pb.total_size > max_sources:
      ascpkgs = sorted(pb, key=lambda x: x.date_published)
      for package in ascpkgs[:( pb.total_size - max_sources )]:
        result[ 'pruned' ][ package.source_package_name ] = package.date_published
        result['count'] += 1
        package.requestDeletion()
    return result

   
class EnvCredentialStore(CredentialStore):

  _consumer = LP_APP_NAME
  _credentials = None

  def __init__(self, consumer=LP_APP_NAME, credential_save_failed=None):
    self._consumer = consumer
    self._credentials = {}
    self._credentials[consumer] = Credentials(consumer_name=consumer, access_token=AccessToken( os.environ.get('LP_ACCESS_TOKEN'), os.environ.get('LP_ACCESS_SECRET') ))
    super().__init__(credential_save_failed)

  def do_save(self, credentials, unique_key=LP_APP_NAME):
    unique_key = unique_key.split('@')[0]
    self._credentials[unique_key] = credentials

  def do_load(self, unique_key=LP_APP_NAME):
    unique_key = unique_key.split('@')[0]
    creds = self._credentials.get(unique_key)
    if creds is None:
      raise Exception('No credentials stored under: ' + unique_key)
    return creds;

class ReqTokenCredentials(Credentials):

  def get_req_token(self):
    params = { 'oauth_token': self._request_token.key,
               'oauth_token_secret': self._request_token.secret
    }
    return params

  def set_req_token(self, credentials):
    creds = json.loads(credentials)
    self._request_token = AccessToken.from_params( creds )


