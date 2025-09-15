..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

Updating a System
=================

If a system already exists, its external package definitions can be updated from the
output of `benchpark system external`:

::

    [ruby]$ benchpark system external llnl-cluster cluster=ruby

    $ benchpark system external llnl-cluster
    ==> The following specs have been detected on this system and added to /g/g20/mckinsey/.spack/packages.yaml
    cmake@3.23.1  cmake@3.26.5  gmake@4.2.1  hwloc@2.11.2  python@2.7.18  python@2.7.18  python@3.6.8  python@3.9.12  python@3.10.8  python@3.12.8  tar@1.30
                    The Packages are different. Here are the differences:
    {'dictionary_item_added': ["root['gmake']['buildable']"],
    'dictionary_item_removed': ["root['elfutils']", "root['papi']", "root['unwind']", "root['blas']", "root['lapack']", "root['fftw']", "root['mpi']"],
    'iterable_item_added': {"root['cmake']['externals'][1]": {'prefix': '/usr/tce',
                                                              'spec': 'cmake@3.23.1'},
                            "root['python']['externals'][1]": {'prefix': '/usr',
                                                                'spec': 'python@2.7.18+bz2+crypt+ctypes+dbm~lzma+nis+pyexpat~pythoncmd+readline+sqlite3+ssl~tkinter+uuid+zlib'},
                            "root['python']['externals'][2]": {'prefix': '/usr',
                                                                'spec': 'python@3.6.8+bz2+crypt+ctypes+dbm+lzma+nis+pyexpat~pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib'},
                            "root['python']['externals'][3]": {'prefix': '/usr/tce',
                                                                'spec': 'python@2.7.18+bz2+crypt+ctypes+dbm~lzma+nis+pyexpat~pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib'},
                            "root['python']['externals'][4]": {'prefix': '/usr/tce',
                                                                'spec': 'python@3.9.12+bz2+crypt+ctypes+dbm+lzma+nis+pyexpat~pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib'},
                            "root['python']['externals'][5]": {'prefix': '/usr/workspace/wsa/mckinsey/venv/benchpark-3.12.8',
                                                                'spec': 'python@3.12.8+bz2+crypt+ctypes+dbm+lzma+nis+pyexpat+pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib'}},
    'values_changed': {"root['cmake']['externals'][0]['prefix']": {'new_value': '/usr',
                                                                    'old_value': '/usr/tce/packages/cmake/cmake-3.26.3'},
                        "root['cmake']['externals'][0]['spec']": {'new_value': 'cmake@3.26.5',
                                                                  'old_value': 'cmake@3.26.3'},
                        "root['hwloc']['externals'][0]['spec']": {'new_value': 'hwloc@2.11.2',
                                                                  'old_value': 'hwloc@2.9.1'},
                        "root['python']['externals'][0]['prefix']": {'new_value': '/usr/WS1/mckinsey/venv/python-3.10.8',
                                                                    'old_value': '/usr/tce/packages/python/python-3.9.12/'},
                        "root['python']['externals'][0]['spec']": {'new_value': 'python@3.10.8+bz2+crypt+ctypes+dbm+lzma+nis+pyexpat+pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib',
                                                                  'old_value': 'python@3.9.12'}}}
                    Here are all of the new packages:
    {'cmake': {'buildable': False,
              'externals': [{'prefix': '/usr', 'spec': 'cmake@3.26.5'},
                            {'prefix': '/usr/tce', 'spec': 'cmake@3.23.1'}]},
    'gmake': {'buildable': False,
              'externals': [{'prefix': '/usr', 'spec': 'gmake@4.2.1'}]},
    'hwloc': {'buildable': False,
              'externals': [{'prefix': '/usr', 'spec': 'hwloc@2.11.2'}]},
    'python': {'buildable': False,
                'externals': [{'prefix': '/usr/WS1/mckinsey/venv/python-3.10.8',
                              'spec': 'python@3.10.8+bz2+crypt+ctypes+dbm+lzma+nis+pyexpat+pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib'},
                              {'prefix': '/usr',
                              'spec': 'python@2.7.18+bz2+crypt+ctypes+dbm~lzma+nis+pyexpat~pythoncmd+readline+sqlite3+ssl~tkinter+uuid+zlib'},
                              {'prefix': '/usr',
                              'spec': 'python@3.6.8+bz2+crypt+ctypes+dbm+lzma+nis+pyexpat~pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib'},
                              {'prefix': '/usr/tce',
                              'spec': 'python@2.7.18+bz2+crypt+ctypes+dbm~lzma+nis+pyexpat~pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib'},
                              {'prefix': '/usr/tce',
                              'spec': 'python@3.9.12+bz2+crypt+ctypes+dbm+lzma+nis+pyexpat~pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib'},
                              {'prefix': '/usr/workspace/wsa/mckinsey/venv/benchpark-3.12.8',
                              'spec': 'python@3.12.8+bz2+crypt+ctypes+dbm+lzma+nis+pyexpat+pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib'}]},
    'tar': {'buildable': False,
            'externals': [{'prefix': '/usr', 'spec': 'tar@1.30'}]}}

where the command should be ran on a cluster that is defined for the given system, e.g.
ruby for llnl-cluster.
