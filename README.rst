README
######

A tool to check YUM repositories and ensure they are reachable.

Example
=======

Suppress logs, use Nagios compatibility, use a custom ``yum.conf``
and limit to only some repositories:

.. code-block:: console

   user@darkstar:~$ tree --noreport /path/to/custom/conf/
   /path/to/custom/conf/
   ├── yum.conf
   └── yum.repos.d
       ├── CentOS-Base.repo
       └── epel.repo

   user@darkstar:~$ yumcheckrepo -c /path/to/custom/conf/yum.conf -q --nagios base epel
   OK: base
   FAIL: epel

   user@darkstar:~$ echo $?
   2
