from __future__ import (absolute_import, division, print_function)
#from ansible.module_utils.common.text.converters import to_native, to_text
from ftplib import FTP
import os

LP_APP_NAME = 'ansible'

class Dput(object):

  def __init__(self):
    self.init = True

  def upload(self, source_changes, ppa):

    if os.path.exists( source_changes ) is False:
      raise Exception("Failed to find Changes file for processing")

    path = os.path.dirname(source_changes)
    files = [ os.path.basename(source_changes) ]
    result = { 'count': 0, 'uploads': []}

    ftp = FTP('ppa.launchpad.net')
    ftp.login()
    ftp.cwd(ppa)
    ftp.set_pasv(True)

    upload = False
    with open(source_changes, "r") as ifile:
      for line in ifile:
        if line.startswith("Checksums-Sha1:"):
          upload=True
          continue
        if line.startswith("Checksums-Sha256:"):
          upload=False
          break
        if upload:
          files.append(line.split()[-1])
    
    for ufile in files:
      print("uploading %s to %s" % (path + "/" + ufile, ufile))
      result['uploads'].append(ufile)
      self._stor(ftp, ufile, path + "/" + ufile)

    result['count'] = len(files)
    return result


  def _stor(self, ftp, filename, path):
    fh = open(path, 'rb')
    ftp.storbinary("STOR "+filename, fh)
    

