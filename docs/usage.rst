#####
Usage
#####

Requirements
############

This script requires the YUM Python library which should be already
installed if you are running this script on a RedHat-derivated
GNU/Linux distribution.

Otherwise, it is available at http://yum.baseurl.org/.

.. Note::
   Unfortunately the YUM package is not distributed through
   a :py:mod:`distutils`-compatible system, making impossible to reference
   the dependencies in the ``setup.py`` script.

Usage examples
##############

Test all repositories presents in the system configuration:

.. code-block:: console

   user@darkstar:~$ yumcheckrepo
   ERROR: unable to access: fusiondirectory-extra
   OK: C7.0.1406-base
   OK: C7.0.1406-centosplus
   OK: C7.0.1406-extras
   OK: C7.0.1406-fasttrack
   OK: C7.0.1406-updates
   OK: C7.1.1503-base
   OK: C7.1.1503-centosplus
   OK: C7.1.1503-extras
   OK: C7.1.1503-fasttrack
   OK: C7.1.1503-updates
   OK: C7.2.1511-base
   OK: C7.2.1511-centosplus
   OK: C7.2.1511-extras
   OK: C7.2.1511-fasttrack
   OK: C7.2.1511-updates
   OK: C7.3.1611-base
   OK: C7.3.1611-centosplus
   OK: C7.3.1611-extras
   OK: C7.3.1611-fasttrack
   OK: C7.3.1611-updates
   OK: base
   OK: base-debuginfo
   OK: base-source
   OK: beats
   FAIL: c7-media
   OK: centosplus
   OK: centosplus-source
   OK: cr
   OK: cuda
   OK: docker-ce-edge
   OK: docker-ce-edge-debuginfo
   OK: docker-ce-edge-source
   OK: docker-ce-stable
   OK: docker-ce-stable-debuginfo
   OK: docker-ce-stable-source
   OK: docker-ce-test
   OK: docker-ce-test-debuginfo
   OK: docker-ce-test-source
   OK: elasticsearch-2.x
   OK: elrepo
   OK: elrepo-extras
   OK: elrepo-kernel
   OK: elrepo-testing
   OK: epel
   OK: epel-debuginfo
   OK: epel-source
   OK: epel-testing
   OK: epel-testing-debuginfo
   OK: epel-testing-source
   OK: extras
   OK: extras-source
   OK: fasttrack
   FAIL: fusiondirectory
   FAIL: fusiondirectory-extra
   OK: gf
   OK: gf-plus
   OK: gf-plus-source
   OK: gf-source
   OK: gf-testing
   OK: gf-testing-source
   OK: google-chrome
   OK: nux-dextop
   OK: nux-dextop-testing
   OK: rpmforge
   OK: rpmforge-extras
   OK: rpmforge-testing
   OK: runner_gitlab-ci-multi-runner
   OK: runner_gitlab-runner
   OK: runner_gitlab-runner-source
   OK: updates
   OK: updates-source

   user@darkstar:~$ echo $?
   1

Suppress logs, use Nagios compatibility and limit to only some repositories:

.. code-block:: console

   user@darkstar:~$ yumcheckrepo -q --nagios epel fusiondirectory
   FAIL: fusiondirectory; OK: epel; 

   user@darkstar:~$ echo $?
   2

Use a custom ``yum.conf``:

.. code-block:: console

   user@darkstar:~$ tree --noreport /path/to/custom/conf/
   /path/to/custom/conf/
   ├── yum.conf
   └── yum.repos.d
       └── epel.repo

   user@darkstar:~$ yumcheckrepo --list-repos \
     -c /path/to/custom/conf/yum.conf
   epel: Extra Packages for Enterprise Linux 7 - x86_64
   epel-debuginfo: Extra Packages for Enterprise Linux 7 - x86_64 - Debug
   epel-source: Extra Packages for Enterprise Linux 7 - x86_64 - Source
