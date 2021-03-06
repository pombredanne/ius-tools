"""version_tracker controller class to expose commands for iustools."""

from cement.core.namespace import get_config

from iustools.core.exc import IUSToolsArgumentError
from iustools.core.controller import IUSToolsController, expose
from iustools.helpers.compare import vcompare
from iustools.lib.version_tracker import get_upstream_version, get_ius_version
from iustools.lib.version_tracker import get_packages
from iustools.lib.version_tracker import bug_titles, compare_titles, create_bug
from iustools.lib.version_tracker import email

class colors:
    red = '\033[91m'
    green = '\033[92m'
    blue = '\033[94m'
    yellow = '\033[33m'
    end = '\033[0m'

class htmlcolors:
    red = '<font color=red>'
    green = '<font color=green>'
    blue = '<font color=blue>'
    end = '</font>'

config = get_config()

TAGS = ['testing', 'stable']
RELEASES = ['4', '5']

class VersionTrackerController(IUSToolsController):

    @expose(namespace='version_tracker')
    def default(self):
        """
        List the version tracker report.
        """
        packages = get_packages(name=self.cli_opts.package,
                                filter_name=self.cli_opts.filter)
        # Verify input 
        if not self.cli_opts.release:
            raise IUSToolsArgumentError, "A valid --release is required."
        elif self.cli_opts.release not in RELEASES:
            raise IUSToolsArgumentError, "Invalid release."
            
        if packages:
            with_launchpad = False
            # Create Launchpad Ticket
            if config['version_tracker']['launchpad']:
                from iustools.lib.mf_identity import mfgroups
                groups = mfgroups()
                if groups:
                    if 'ius-coredev' in groups:
                        with_launchpad = True
                    else:
                        print '\nYou are not apart of the ius-coredev group'
                else:
                    print 'Unable to determine MF group'

            # Print out our Packages and Info
            print
            print config['version_tracker']['layout'] % \
                config['version_tracker']['layout_titles']
            print '='*75

            output = []
            for pkg_dict in sorted(packages, key=lambda a: a['name']):
                upstream_ver = get_upstream_version(pkg_dict)
                ius_ver = get_ius_version(pkg_dict['name'], 
                                          self.cli_opts.release, 
                                          'stable')

                # verify we pulled a version
                if upstream_ver:
                
                    # package didn't exist
                    if not ius_ver:
                        continue
                        
                    if ius_ver == upstream_ver:
                        status = 'current'
                        color = colors.green
                        htmlcolor = htmlcolors.green
                        
                    else:
                        status = 'outdated'
                        color = colors.red
                        htmlcolor = htmlcolors.red
                        
                        # Since its out of date we should check testing
                        ius_test = get_ius_version(pkg_dict['name'], 
                                                   self.cli_opts.release, 
                                                   'testing')
                        if ius_test:
                            if ius_test == upstream_ver:
                                ius_ver = ius_test
                                status = 'testing'
                                color = colors.blue
                                htmlcolor = htmlcolors.blue
                            else:
                                ius_ver = ius_test
                                status = 'testing outdated'
                                color = colors.red
                                htmlcolor = htmlcolors.red

                else:
                    status = 'unknown'
                    color = colors.red
                    htmlcolor = htmlcolors.red
                    upstream_ver = '??????'

                # Print out for the viewer
                print config['version_tracker']['layout'] % \
                        (pkg_dict['name'], ius_ver, upstream_ver, 
                         color + status + colors.end)
                # Append to our list for email
                output.append((pkg_dict['name'], ius_ver, upstream_ver,
                         htmlcolor + status + htmlcolors.end))

                # Check Launchpad if status is outdated
                if with_launchpad and status == 'outdated' or status == 'testing outdated':
                    try:
                        if titles:
                            pass
                    except NameError:
                        # If we haven't checked LP do it now
                        titles = bug_titles()

                    if compare_titles(titles, pkg_dict['name'], upstream_ver):
                        # Already in Launchpad
                        pass
                    else:
                        create_bug(pkg_dict['name'], upstream_ver, pkg_dict['url'])
            print
           
            # Do we want to send email
            if config['version_tracker']['email']:
                layout = config['version_tracker']['layout']
                layout_titles = config['version_tracker']['layout_titles']
                toaddr = config['version_tracker']['toaddr']
                fromaddr = config['version_tracker']['fromaddr']
                subject = config['version_tracker']['subject']

                email(layout, layout_titles, output, fromaddr, toaddr, subject)

            return dict(packages=packages)
                
        else:
            print "No data found using pkg dir '%s'" % \
                    config['version_tracker']['pkg_dir']
            return dict(packages=[])
