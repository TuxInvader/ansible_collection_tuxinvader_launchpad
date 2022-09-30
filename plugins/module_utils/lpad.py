from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.common.text.converters import to_text
from launchpadlib.credentials import Credentials, CredentialStore, AuthorizeRequestTokenWithURL, AccessToken
from launchpadlib.launchpad import Launchpad
from datetime import datetime, timedelta, timezone
import os
import json
import re

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
            if os.environ.get('LP_ACCESS_TOKEN') is None:
                raise Exception("You need to set 'LP_ACCESS_TOKEN' and 'LP_ACCESS_SECRET' environment variables")
            if os.environ.get('LP_ACCESS_SECRET') is None:
                raise Exception("You need to set 'LP_ACCESS_TOKEN' and 'LP_ACCESS_SECRET' environment variables")
            self._credStore = EnvCredentialStore(consumer)
            self._credentials = self._credStore.load(consumer)

    def _login(self):
        if self._authorize:
            ae = AuthorizeRequestTokenWithURL(
                service_root='production', consumer_name=self._consumer)
            self.api_root = Launchpad.login_with(application_name=self._consumer, service_root='production',
                                                 credential_store=self._credStore, authorization_engine=ae, version='devel')
        else:
            self.api_root = Launchpad.login_anonymously(
                self._consumer, 'production', version='devel')

    def start_interactive_login(self):
        self._credStore = EnvCredentialStore(self._consumer)
        self._credentials = ReqTokenCredentials(self._consumer)
        authorization_url = self._credentials.get_request_token(
            context=None, web_root='production')
        return {'authorization_url': authorization_url, 'credentials': self._credentials.get_req_token()}

    def wait_interactive_login(self, credentials):
        result = {}
        self._credStore = EnvCredentialStore(self._consumer)
        self._credentials = ReqTokenCredentials(self._consumer)
        self._credentials.set_req_token(credentials)
        self._credentials.exchange_request_token_for_access_token(
            web_root='production')
        result['LP_ACCESS_TOKEN'] = self._credentials.access_token.key
        result['LP_ACCESS_SECRET'] = self._credentials.access_token.secret
        return result

    def get_user_info(self, name):
        result = {'details': {}}
        if self.api_root is None:
            self._login()
        people = self.api_root.people
        for person in people.find(text=name):
            for att in person.lp_attributes:
                result['details'][att] = person.lp_get_parameter(att)
        return result

    def _get_project(self, name):
        project = self.api_root.projects[name]
        if project is None:
            raise LaunchPadLookupError("Project '" + name + "' not found")
        return project

    def _build_project_result(self, project, ppa_filter):
        result = {'details': {}, 'ppas': []}

        ppa_filter = ppa_filter.capitalize()
        ppa_list = ['*', 'Active', 'Deleted']
        if ppa_filter not in ppa_list:
            raise Exception(
                to_text("status_filter should be one of %s" % str(ppa_list)))

        for att in project.lp_attributes:
            result['details'][att] = project.lp_get_parameter(att)
        for ppa in project.ppas:
            ppa_atts = {}
            if ppa_filter == '*' or ppa_filter == ppa.status:
                for att in ppa.lp_attributes:
                    ppa_atts[att] = ppa.lp_get_parameter(att)
                result['ppas'].append(ppa_atts)
        return result

    def _get_ppa(self, project, name):
        ppa = list(filter(lambda x: x.name == name, project.ppas))
        if len(ppa) == 0:
            raise LaunchPadLookupError("PPA '" + name + "' not found")
        return ppa[0]

    def _build_entry_result(self, source_package):
        source_atts = {}
        for att in source_package.lp_attributes:
            source_atts[att] = source_package.lp_get_parameter(att)
        return source_atts

    def _build_ppa_result(self, ppa, status_filter):
        result = {'details': {}, 'sources': []}
        for att in ppa.lp_attributes:
            result['details'][att] = ppa.lp_get_parameter(att)

        status_filter = status_filter.capitalize()
        status_list = ['*', 'Pending', 'Published',
                       'Superseded', 'Deleted', 'Obsolete']
        if status_filter not in status_list:
            raise Exception("status_filter should be one of %s" %
                            str(status_list))

        if status_filter == '*':
            for source in ppa.getPublishedSources():
                result['sources'].append(
                    self._build_entry_result(source))
        else:
            for source in ppa.getPublishedSources(status=status_filter):
                result['sources'].append(
                    self._build_entry_result(source))

        return result

    def get_project_info(self, name, status_filter=None):
        if self.api_root is None:
            self._login()

        try:
            project = self._get_project(name)
        except LaunchPadLookupError as e:
            raise Exception(e.args)

        return self._build_project_result(project, status_filter)

    def get_ppa_info(self, project_name, name, source_filter):
        if self.api_root is None:
            self._login()

        try:
            project = self._get_project(project_name)
            ppa = self._get_ppa(project, name)
        except LaunchPadLookupError as e:
            raise Exception(e.args)

        return self._build_ppa_result(ppa, source_filter)

    def upsert_ppa(self, project_name, name, ensure, source_filter, displayname=None, description=None):
        result = {}
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
        except LaunchPadLookupError:
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
                changed = True
                project.createPPA(
                    name=name, displayname=displayname, description=description)

        try:
            ppa = self._get_ppa(project, name)
        except LaunchPadLookupError as e:
            if ensure.lower() == "absent":
                return {'details': {}, 'sources': []}
            raise Exception(e.args)

        result = self._build_ppa_result(ppa, source_filter)
        result['changed'] = changed
        return result

    def prune_ppa(self, project_name, name, max_sources):
        result = {'pruned': {}, 'count': 0}
        if self.api_root is None:
            self._login()

        try:
            project = self._get_project(project_name)
            ppa = self._get_ppa(project, name)
        except LaunchPadLookupError as e:
            raise Exception(e.args)

        pb = ppa.getPublishedSources(status="Published")

        if pb.total_size > max_sources:
            ascpkgs = sorted(pb, key=lambda x: x.date_published)
            for package in ascpkgs[:(pb.total_size - max_sources)]:
                result['pruned'][package.source_package_name] = package.date_published
                result['count'] += 1
                package.requestDeletion()
        return result

    def check_source_package(self, project_name, ppa_name, name, version, ensure, match):
        result = {'sources': [], 'messages': []}
        regex = None

        if self.api_root is None:
            self._login()

        try:
            project = self._get_project(project_name)
            ppa = self._get_ppa(project, ppa_name)
        except LaunchPadLookupError as e:
            raise Exception(e.args)

        sources = None
        if match.lower() == "exact":
            sources = ppa.getPublishedSources(source_name=name)
        else:
            sources = ppa.getPublishedSources()

        if match.lower() == "starts_with":
            regex = r"^%s.*" % name
        elif match.lower() == "ends_with":
            regex = r".*%s$" % name
        elif match.lower() == "contains":
            regex = r".*%s.*" % name
        else:
            regex = r"%s" % name

        for source in sources:
            if ensure.lower() == "absent":
                if match.lower() == "exact" and source.source_package_name == name:
                    if version == '*' or source.source_package_version == version:
                        if source.status.lower() != "deleted":
                            source.requestDeletion()
                            result['changed'] = True
                        result['sources'].append(
                            self._build_entry_result(source))
                    else:
                        result['message'] = "package found, but version mismatch. %s != %s" % (
                            source.source_package_version, version)
                else:
                    regex_result = re.search(regex, source.source_package_name)
                    if regex_result is not None:
                        if version == '*' or source.source_package_version == version:
                            if source.status.lower() != "deleted":
                                source.requestDeletion()
                                result['changed'] = True
                            result['sources'].append(
                                self._build_entry_result(source))
                            result['messages'].append(
                                "regex_matched: %s" % regex_result.group())
                        else:
                            result['messages'].append("package unchanged, version mismatch: '%s' not '%s', regex: '%s', result: '%s'" % (
                                source.source_package_version, version, regex, regex_result.group()))
            elif ensure.lower() == "present":
                if match.lower() == "exact" and source.source_package_name == name:
                    if version == '*' or source.source_package_version == version:
                        if source.status.lower() == "published":
                            result['sources'].append(
                                self._build_entry_result(source))
                else:
                    regex_result = re.search(regex, source.source_package_name)
                    if regex_result is not None:
                        if version == '*' or source.source_package_version == version:
                            if source.status.lower() == "published":
                                result['sources'].append(
                                    self._build_entry_result(source))
            else:
                raise Exception(
                    "Permitted values for 'ensure' are 'present' or 'absent'")

        return result

    def _check_recency(self, time_frame, entry_time):
        max_delta = datetime.now(tz=timezone(
            timedelta(0))) - timedelta(minutes=time_frame)
        if max_delta > entry_time:
            return False
        return True

    def get_build_record_info(self, project_name, ppa_name, source_name, source_version, build_id, time_frame):
        result = {'records': []}
        if self.api_root is None:
            self._login()

        try:
            project = self._get_project(project_name)
            ppa = self._get_ppa(project, ppa_name)
        except LaunchPadLookupError as e:
            raise Exception(e.args)

        brs = None
        if source_name is not None:
            brs = ppa.getBuildRecords(source_name=source_name)
        else:
            brs = ppa.getBuildRecords()

        for br in brs:
            if build_id is not None:
                if br.self_link.endswith(str(build_id)):
                    result['records'].append(self._build_entry_result(br))
                    return result
            else:
                if source_version is not None:
                    if br.source_package_version == source_version:
                        if self._check_recency(time_frame, br.datecreated):
                            result['records'].append(
                                self._build_entry_result(br))
                else:
                    if self._check_recency(time_frame, br.datecreated):
                        result['records'].append(self._build_entry_result(br))

        return result


class EnvCredentialStore(CredentialStore):

    _consumer = LP_APP_NAME
    _credentials = None

    def __init__(self, consumer=LP_APP_NAME, credential_save_failed=None):
        self._consumer = consumer
        self._credentials = {}
        self._credentials[consumer] = Credentials(consumer_name=consumer, access_token=AccessToken(
            os.environ.get('LP_ACCESS_TOKEN'), os.environ.get('LP_ACCESS_SECRET')))
        super().__init__(credential_save_failed)

    def do_save(self, credentials, unique_key=LP_APP_NAME):
        unique_key = unique_key.split('@')[0]
        self._credentials[unique_key] = credentials

    def do_load(self, unique_key=LP_APP_NAME):
        unique_key = unique_key.split('@')[0]
        creds = self._credentials.get(unique_key)
        if creds is None:
            raise Exception('No credentials stored under: ' + unique_key)
        return creds


class ReqTokenCredentials(Credentials):

    def get_req_token(self):
        params = {'oauth_token': self._request_token.key,
                  'oauth_token_secret': self._request_token.secret
                  }
        return params

    def set_req_token(self, credentials):
        creds = json.loads(credentials)
        self._request_token = AccessToken.from_params(creds)


class LaunchPadLookupError(Exception):
    pass
