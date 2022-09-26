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
      for att in person.lp_attributes:
        result[att] = person.lp_get_parameter( att )
    return result

  def _get_project(self, name):
    project = self.api_root.projects[name]
    if project == None:
      raise LaunchPadLookupError("Project '" + name + "' not found")
    return project

  def _build_project_result(self, project):
    result = { 'ppas': [] }
    for att in project.lp_attributes:
      result[att] = project.lp_get_parameter( att )
    for ppa in project.ppas:
      ppa_atts = {}
      for att in ppa.lp_attributes:
        ppa_atts[att] = ppa.lp_get_parameter( att )
      result['ppas'].append( ppa_atts )
    return result

  def _get_ppa(self, project, name):
    ppa = list(filter(lambda x: x.name == name, project.ppas))
    if len(ppa) == 0:
      raise LaunchPadLookupError("PPA '" + name + "' not found")
    return ppa[0]

  def _build_ppa_result(self, ppa):
    result = { 'sources': [] }
    for att in ppa.lp_attributes:
      result[att] = ppa.lp_get_parameter( att )

    for source in ppa.getPublishedSources(status="Published"):
      source_atts = {}
      for att in source.lp_attributes:
        source_atts[att] = source.lp_get_parameter( att )
      result['sources'].append( source_atts )

    return result

  def get_project_info(self, name, status=None):
    if self.api_root is None:
      self._login()

    try:
      project = self._get_project(name)
    except LaunchPadLookupError as e:
      raise Exception(e.args)

    return self._build_project_result(project)

  def get_ppa_info(self, project_name, name):
    if self.api_root is None:
      self._login()

    try:
      project = self._get_project(project_name)
      ppa = self._get_ppa(project, name)
    except LaunchPadLookupError as e:
      raise Exception(e.args)

    return self._build_ppa_result(ppa)

  def upsert_ppa(self, project_name, name, ensure, displayname=None, description=None):
    result = { }
    ppa = None
    changed = False

    if self.api_root is None:
      self._login()

    try:
      project = self._get_project(project_name)
    except LaunchPadLookupError as e:
      raise Exception(e.args)

    try:
      ppa = self._get_ppa(project, name)
    except LaunchPadLookupError as e:
      pass

    if ppa is not None:
      if ppa.status == "Active" and ensure.lower() == "absent":
        changed = True
        ppa.lp_delete()
      else:
        if ppa.displayname != displayname:
          ppa.displayname = displayname
          changed = True
        if ppa.description != description:
          ppa.description = description
          changed = True
        if changed:
          ppa.lp_save()

    else:
      if ensure.lower() == "present":
        project.createPPA(name=name, displayname=displayname, description=description)

    try:
      ppa = self._get_ppa(project, name)
    except LaunchPadLookupError as e:
      raise Exception(e.args)

    result['details'] = self._build_ppa_result(ppa)
    result['changed'] = changed
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

class LaunchPadLookupError(Exception):
  pass


