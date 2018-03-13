import csv
from optparse import make_option

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--csv', dest='csv',
                    help='CSV file containing user, password and group'),
    )

    def process_row(self, row):
        username = row[0]
        password = row[1]
        group = row[2]
        print('{}/{} in {}').format(username, password, group)

        try:
            user = User.objects.get(username=username)
            print('User {} already exists').format(username)
        except User.DoesNotExist:
            user = User.objects.create_user(username, '', password)

        user.profile.research_group = group
        user.profile.save()

    def handle(self, *app_labels, **options):
        args = 'Usage: ./manage.py import_users --csv csv file'

        if not options.get('csv'):
            print(args)
            return

        try:
            fh = open(options.get('csv'), 'r')

        except IOError:
            print('error opening {}').format(options.get('csv'))
            return

        table = csv.reader(fh)

        rows = list(table)
        for row in rows:
            self.process_row(row)
