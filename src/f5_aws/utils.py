# utils.py

import subprocess
import itertools
import boto.ec2
from boto.exception import EC2ResponseError

# not sure how else to generate a 'namespace' like object
#  similar to what argparse returns...couldn't they just use a dict?
def get_namespace(**kwargs):
  class Namespace(object):
    def __init__(self, kwargs):
      for k, v in kwargs.items():
        setattr(self, k, v)

    def __repr__(self):
      print dir(self)

    def __str__(self):
      return dir(self)

  return Namespace(kwargs)

def convert_str(inStr):
  """
    One of the quirks with ansible is the use of several different
    object notations, sometimes even one embedded within another...
    This function modifies the string formatting so we can read it
    in as a variable.
  """
  l = [i.split('=') for i in inStr.split(' ')]
  res_arr = [i.replace('"', '') for i in list(itertools.chain(*l))]
  return dict(zip(res_arr[::2], res_arr[1::2]))

def touchImage(region='', imageId='',
  keyName='', instanceType='', vpcId='',
  subnetId='', okayStatusCodes=[401]):

  try: 
    ec2_conn = boto.ec2.connect_to_region(region)
    ec2_conn.get_image(image_id=imageId).run(
      instance_type=instanceType,
      key_name=keyName,
      subnet_id=subnetId,
      dry_run=True
      )
  except EC2ResponseError, e:
    
    status=int(e.status)

    if status not in okayStatusCodes:
      # e.reason == 'Unauthorized' => EULA needs to be accepted
      if int(e.status) == 401:
        print 'Error: Unauthorized to use this image {} in {}, \
  have the terms and conditions been accepted?'.format(
          imageId, region)
        return False

      # e.reason == 'Bad Request' => bad image launch conditions
      # for example:
      # "The image id '[ami-4c7a3924]' does not exist"
      #   "Virtualization type 'hvm' is required for instances of type 't2.micro'."
      elif int(e.status) == 400:
        print 'Error: Unable to launch image with params region={}, \
imageId={}, keyName={}, instanceType={}\r\n\
\tReason was: {}'.format(
            region, imageId, keyName, instanceType, e.message)
        return False

      # e.reason = 'Precondition Failed'
      # for example: 
      #   Request would have succeeded, but DryRun flag is set.
      elif int(e.status) == 412:
        return True
      else: 
        raise e
        return False
  return True

def ntp_update():
  """
  somtimes the vagrant VM system time is incorrect, which 
  causes errors when using the AWS CFT API
  """
  try:
    subprocess.check_call(['sudo', 'ntpdate', 'ntp.ubuntu.com'])
  except:
    print 'WARN: Clock update failed'
    pass

def region_to_azs(region):
  pass
