import csv
from optparse import make_option

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--csv', dest='csv',
                    help='CSV file containing user, password and group'),
    )

    def handle(self, *app_labels, **options):
        args = 'Usage: ./manage.py import_users --csv csv file'

        if not options.get('csv'):
            print args
            return

        fh = open(options.get('csv'), 'r')
        table = csv.reader(fh)

        rows = list(table)
        for row in rows:
            username = row[0]
            password = row[1]
            group = row[2]

            user = User.objects.get_or_create(
                username=username, password=password)
            user.profile.research_group = group
            user.profile.save()
