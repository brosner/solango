#
# Copyright 2008 Optaros, Inc.
#

from django.core.management.base import BaseCommand, CommandError, NoArgsCommand
from optparse import make_option
import os
import shutil

class Command(NoArgsCommand):
    option_list = BaseCommand.option_list + (
        make_option('--flush', dest='flush_solr', action='store_true', default=False,
            help='Will remove the data directory from Solr.'),
                                             
        make_option('--reindex', dest='index_solr', action='store_true', default=False,
            help='Will reindex Solr from the registry.'),
            
        make_option('--schema', dest='solr_schema', action='store_true', default=False,
            help='Will create the schema.xml in SOLR_SCHEMA_PATH or in the --path.'),
        
        make_option('--path', dest='schema_path', default=False,
            help='Tells Solango where to create config file.'),
       
        make_option('--fields', dest='solr_fields', action='store_true', default=False,
            help='Prints out the fields the schema.xml will create'),
    )
    args = ''

    def handle(self, *args, **options):
        if args:
            raise CommandError("Command doesn't accept any arguments")
        return self.handle_noargs(**options)

    def handle_noargs(self, **options):
        index_solr = options.get('index_solr')
        schema = options.get('solr_schema')
        schema_path = options.get('schema_path')
        flush_solr =options.get('flush_solr')
        solr_fields =options.get('solr_fields')
        
        from django.conf import settings
        
        #### SOLR
        SOLR_SCHEMA_PATH = getattr(settings, 'SOLR_SCHEMA_PATH', None)
        SOLR_DATA_DIR = getattr(settings, 'SOLR_DATA_DIR', None)
                
        if schema or solr_fields:
            #Get the Path
            path = None
            if schema_path:
                path = schema_path
            elif SOLR_SCHEMA_PATH:
                path = SOLR_SCHEMA_PATH
            else:
                raise CommandError("Need to specify either a SOLR_SCHEMA_PATH in settings.py or use --path")
            #Make sure the path exists
            if not os.path.exists(path):
                raise CommandError("Path does not exist: %s" % path)
            
            if not os.path.isfile(path):
                path = os.path.join(schema_path, 'schema.xml')
            
            from solango.utils import create_schema_xml
            if solr_fields:
                create_schema_xml(True)
            else:
                f = open(path, 'w')
                f.write(create_schema_xml())
                f.close()
                print "Successfully created schema.xml in/at: %s" % path
        
        if flush_solr:
            if SOLR_DATA_DIR:
                if not os.path.exists(SOLR_DATA_DIR):
                    raise CommandError("Solr Data Directory has already been deleted or doesn't exist: %s" % SOLR_DATA_DIR)
                else:
                    answer = raw_input('Do you wish to delete %s: [y/N] ' % SOLR_DATA_DIR)
                    if answer == 'y' or answer == 'Y':
                        shutil.rmtree(SOLR_DATA_DIR)
                        print 'Removed %s' % SOLR_DATA_DIR
                    else:
                        print 'Did not remove %s' % SOLR_DATA_DIR
            else:
                raise CommandError("Path does not exist: %s" % path)
        
        if index_solr:
            import solango
            if not solango.connection.is_available():
                raise CommandError("Solr connection is not avalible")
            
            from solango.utils import reindex
            print "Starting to reindex Solr"
            reindex()
            print "Finished the reindex of Solr"